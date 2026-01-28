import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import random
import time

# ၁။ Firebase ချိတ်ဆက်ခြင်း
def initialize_firebase():
    if not firebase_admin._apps:
        service_account_info = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        if service_account_info:
            cred = credentials.Certificate(json.loads(service_account_info))
        else:
            cred = credentials.Certificate('serviceAccountKey.json')
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firebase()

# ၂။ Configuration
LEAGUE_ID = "400231"
FPL_API = "https://fantasy.premierleague.com/api/"
CURRENT_GW = 23  # 👈 ပြီးသွားတဲ့ GW ကို ဒီမှာ ပြောင်းပြီး Run ပါ

def get_net_points(entry_id, gw_num):
    """ Chip Points (TC/BB) နှင့် Transfer Hits များကို နှုတ်ပြီး Net Point တွက်ပေးသည် """
    try:
        url = f"{FPL_API}entry/{entry_id}/event/{gw_num}/picks/"
        res = requests.get(url).json()
        
        raw_points = res['entry_history']['points']
        transfer_cost = res['entry_history']['event_transfers_cost']
        net_points = raw_points - transfer_cost
        
        active_chip = res.get('active_chip')
        
        # Triple Captain Logic: ၁ ဆ ပြန်နှုတ် (Tournament တွင် ၂ ဆပဲ ယူရန်)
        if active_chip == '3xc':
            cap_id = next(p for p in res['picks'] if p['is_captain'])['element']
            p_res = requests.get(f"{FPL_API}element-summary/{cap_id}/").json()
            cap_pts = next(e['event_points'] for e in p_res['history'] if e['event'] == gw_num)
            net_points -= cap_pts
            
        # Bench Boost Logic: Bench အမှတ် ၄ ယောက်လုံးကို ပြန်နှုတ်
        elif active_chip == 'bboost':
            bench_ids = [p['element'] for p in res['picks'][11:]]
            for b_id in bench_ids:
                b_res = requests.get(f"{FPL_API}element-summary/{b_id}/").json()
                b_pts = next(e['event_points'] for e in b_res['history'] if e['event'] == gw_num)
                net_points -= b_pts

        return net_points
    except:
        return 0

def sync_tournament():
    print(f"--- 🚀 Tournament Engine Started: GW {CURRENT_GW} ---")
    
    # Standings ရယူခြင်း
    r = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/").json()
    standings = r['standings']['results']

    # Fixtures ရယူခြင်း
    f_ref = db.collection("fixtures").where("gameweek", "==", CURRENT_GW).stream()
    fixtures_data = {f.id: f.to_dict() for f in f_ref}

    batch = db.batch()
    sync_logs = []

    for manager in standings:
        entry_id = str(manager['entry'])
        print(f"🔄 Fetching Data for: {manager['player_name']}...")
        
        net_pts = get_net_points(entry_id, CURRENT_GW)
        
        # H2H Logic (Division A/B အတွက်)
        played, wins, draws, losses, h2h_pts = 0, 0, 0, 0, 0
        active_fixture = next((f for f in fixtures_data.values() if f['home']['id'] == manager['entry'] or f['away']['id'] == manager['entry']), None)

        if active_fixture and active_fixture.get('type') == 'league':
            played = 1
            is_home = active_fixture['home']['id'] == manager['entry']
            opp_id = active_fixture['away']['id'] if is_home else active_fixture['home']['id']
            opp_net = get_net_points(opp_id, CURRENT_GW)
            
            if net_pts > opp_net: wins, h2h_pts = 1, 3
            elif net_pts == opp_net: draws, h2h_pts = 1, 1
            else: losses = 1

        # Tournament Table ကို Update လုပ်ခြင်း
        doc_ref = db.collection("tw_mm_tournament").document(entry_id)
        batch.set(doc_ref, {
            "fpl_id": manager['entry'],
            "manager_name": manager['player_name'],
            "team_name": manager['entry_name'],
            "played": firestore.Increment(played),
            "wins": firestore.Increment(wins),
            "draws": firestore.Increment(draws),
            "losses": firestore.Increment(losses),
            "h2h_points": firestore.Increment(h2h_pts),
            "gw_points": net_pts,
            "tournament_total_net_points": firestore.Increment(net_pts),
            "last_synced_gw": CURRENT_GW,
            "last_updated": firestore.SERVER_TIMESTAMP
        }, merge=True)
        
        sync_logs.append({"id": entry_id, "pts": net_pts, "name": manager['player_name'], "team": manager['entry_name']})

    # ရလဒ်များကို History အဖြစ် သိမ်းဆည်းခြင်း
    archive_results(sync_logs, fixtures_data)
    
    batch.commit()
    print(f"✅ GW {CURRENT_GW} Sync & Archive Complete.")
    
    # FA Cup Playoff: နောက်တစ်ဆင့်အတွက် ပွဲစဉ် Auto ထုတ်ခြင်း
    generate_next_fa_round(CURRENT_GW)

def archive_results(sync_logs, fixtures_data):
    for fid, f in fixtures_data.items():
        h_pts = next((l['pts'] for l in sync_logs if str(l['id']) == str(f['home']['id'])), 0)
        a_pts = next((l['pts'] for l in sync_logs if str(l['id']) == str(f['away']['id'])), 0)
        
        f.update({
            "home": {**f['home'], "points": h_pts},
            "away": {**f['away'], "points": a_pts},
            "status": "completed"
        })
        
        # FA Cup နှင့် League ခွဲသိမ်းခြင်း
        col = "fixtures_history_fa" if f['type'] == 'fa_cup' else f"fixtures_history_gw_{CURRENT_GW}"
        db.collection(col).document(fid).set(f)

def generate_next_fa_round(gw):
    winners = []
    # History ထဲမှ နိုင်သူများကို ရွေးထုတ်ခြင်း
    f_ref = db.collection("fixtures_history_fa").where("gameweek", "==", gw).stream()
    
    for doc in f_ref:
        f = doc.to_dict()
        if f['home']['points'] > f['away']['points']: winners.append(f['home'])
        elif f['away']['points'] > f['home']['points']: winners.append(f['away'])
        else: winners.append(random.choice([f['home'], f['away']])) # သရေကျလျှင် တစ်ယောက်ရွေးမည်

    if len(winners) >= 2:
        next_gw = gw + 1
        random.shuffle(winners)
        batch = db.batch()
        for i in range(0, len(winners), 2):
            if i+1 < len(winners):
                h, a = winners[i], winners[i+1]
                f_id = f"GW{next_gw}_FA_Playoff_P{i//2 + 1}"
                batch.set(db.collection("fixtures").document(f_id), {
                    "gameweek": next_gw, "type": "fa_cup", "division": "FA_CUP",
                    "home": {"id": h['id'], "name": h['name'], "team": h.get('team', '')},
                    "away": {"id": a['id'], "name": a['name'], "team": a.get('team', '')},
                    "status": "upcoming"
                })
        batch.commit()
        print(f"🏆 FA Cup GW {next_gw} Fixtures Generated Successfully!")

if __name__ == "__main__":
    sync_tournament()
