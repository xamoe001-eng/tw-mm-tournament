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
            try:
                print("✅ GitHub Secret Found. Initializing Firebase...")
                cred_dict = json.loads(service_account_info)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
            except Exception as e:
                print(f"❌ Error parsing JSON from Secret: {e}")
                raise e
        else:
            if os.path.exists('serviceAccountKey.json'):
                cred = credentials.Certificate('serviceAccountKey.json')
                firebase_admin.initialize_app(cred)
            else:
                raise FileNotFoundError("Missing Firebase Credentials")
    return firestore.client()

db = initialize_firebase()

# ၂။ Configuration
LEAGUE_ID = "400231"
FPL_API = "https://fantasy.premierleague.com/api/"
CURRENT_GW = 23  # 👈 အပတ်စဉ် ပြောင်းလဲပေးရမည့် Gameweek နံပါတ်

def get_net_points(entry_id, gw_num):
    """ TC (2x ကျန်အောင် ၁ ဆ နှုတ်), BB (ပြန်နှုတ်) နှင့် Transfer Hits နှုတ်ပေးသည့် Logic """
    try:
        url = f"{FPL_API}entry/{entry_id}/event/{gw_num}/picks/"
        res = requests.get(url, timeout=10).json()
        raw_points = res['entry_history']['points']
        transfer_cost = res['entry_history']['event_transfers_cost']
        net_points = raw_points - transfer_cost
        
        active_chip = res.get('active_chip')
        
        # Triple Captain: ၃ ဆ ရထားတဲ့အထဲက ၁ ဆ ပြန်နှုတ် (Tournament အတွက် ၂ ဆ ပဲ ယူရန်)
        if active_chip == '3xc':
            cap_id = next(p for p in res['picks'] if p['is_captain'])['element']
            p_res = requests.get(f"{FPL_API}element-summary/{cap_id}/", timeout=10).json()
            cap_pts = next(e['event_points'] for e in p_res['history'] if e['event'] == gw_num)
            net_points -= cap_pts
            
        # Bench Boost: အရန်ခုံက အမှတ်တွေ အကုန်ပြန်နှုတ်
        elif active_chip == 'bboost':
            bench_ids = [p['element'] for p in res['picks'][11:]]
            for b_id in bench_ids:
                b_res = requests.get(f"{FPL_API}element-summary/{b_id}/", timeout=10).json()
                b_pts = next(e['event_points'] for e in b_res['history'] if e['event'] == gw_num)
                net_points -= b_pts

        return net_points
    except Exception as e:
        print(f"⚠️ Error for {entry_id}: {e}")
        return 0

def sync_tournament():
    print(f"--- 🚀 TW Tournament Started: GW {CURRENT_GW} (7-Week Season) ---")
    
    # League Standings ဆွဲပြီး Total Points အလိုက် စီ၍ ၄၈ သင်းယူမည်
    try:
        r = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/", timeout=10).json()
        all_managers = r['standings']['results']
        top_48 = sorted(all_managers, key=lambda x: x['total'], reverse=True)[:48]
        print(f"✅ Filtered Top 48 Managers by FPL Total Points.")
    except Exception as e:
        print(f"❌ Failed to fetch standings: {e}")
        return

    # Fixtures ရယူခြင်း
    f_ref = db.collection("fixtures").where("gameweek", "==", CURRENT_GW).stream()
    fixtures_data = {f.id: f.to_dict() for f in f_ref}

    batch = db.batch()
    sync_logs = []

    for index, manager in enumerate(top_48):
        entry_id = str(manager['entry'])
        
        # Division ခွဲခြင်း (Rank 1-24 = Div A, 25-48 = Div B)
        division = "Division A" if index < 24 else "Division B"
        
        net_pts = get_net_points(entry_id, CURRENT_GW)
        
        # H2H Logic (Win=3, Draw=1, Loss=0)
        played, wins, draws, losses, h2h_pts = 0, 0, 0, 0, 0
        
        # လက်ရှိ Manager ရဲ့ ပွဲစဉ်ကို ရှာမည် (League Type သာ)
        active_f = next((f for f in fixtures_data.values() 
                         if f.get('type') == 'league' and (str(f['home']['id']) == entry_id or str(f['away']['id']) == entry_id)), None)

        if active_f:
            played = 1
            is_home = str(active_f['home']['id']) == entry_id
            opp_id = active_f['away']['id'] if is_home else active_f['home']['id']
            opp_net = get_net_points(opp_id, CURRENT_GW)
            
            if net_pts > opp_net: wins, h2h_pts = 1, 3
            elif net_pts == opp_net: draws, h2h_pts = 1, 1
            else: losses = 1

        # Firestore Database Update
        doc_ref = db.collection("tw_mm_tournament").document(entry_id)
        batch.set(doc_ref, {
            "fpl_id": manager['entry'],
            "manager_name": manager['player_name'],
            "team_name": manager['entry_name'],
            "division": division,
            "played": firestore.Increment(played),
            "wins": firestore.Increment(wins),
            "draws": firestore.Increment(draws),
            "losses": firestore.Increment(losses),
            "h2h_points": firestore.Increment(h2h_pts),
            "gw_points": net_pts, # လက်ရှိအပတ်အမှတ်
            "tournament_total_net_points": firestore.Increment(net_pts), # ၇ ပတ်စာ စုစုပေါင်းအမှတ်
            "last_synced_gw": CURRENT_GW,
            "last_updated": firestore.SERVER_TIMESTAMP
        }, merge=True)
        
        sync_logs.append({"id": entry_id, "pts": net_pts, "name": manager['player_name']})
        time.sleep(0.05)

    # ပွဲစဉ်ရလဒ်များကို History အဖြစ် Collection အလိုအလျောက်ခွဲသိမ်းမည်
    archive_results(sync_logs, fixtures_data)
    
    batch.commit()
    print(f"✅ Sync GW {CURRENT_GW} Complete.")

    # FA Cup Playoff: နိုင်သူများကို နောက်တစ်ဆင့် ပွဲစဉ်ထုတ်ပေးမည်
    if CURRENT_GW < 29: # GW 29 သည် Final ဖြစ်မည်ဟု ယူဆလျှင်
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
        
        # Collection Auto ခွဲခြင်း
        col = "fixtures_history_fa" if f.get('type') == 'fa_cup' else f"fixtures_history_gw_{CURRENT_GW}"
        db.collection(col).document(fid).set(f)

def generate_next_fa_round(gw):
    """ FA Cup နိုင်သူများကို နောက်အပတ်အတွက် Fixture အသစ်ထုတ်ပေးခြင်း """
    winners = []
    # FA Cup ပွဲစဉ်များကိုသာ ဆွဲထုတ်မည်
    f_ref = db.collection("fixtures_history_fa").where("gameweek", "==", gw).stream()
    
    for doc in f_ref:
        f = doc.to_dict()
        if f['home']['points'] > f['away']['points']: winners.append(f['home'])
        elif f['away']['points'] > f['home']['points']: winners.append(f['away'])
        else: winners.append(random.choice([f['home'], f['away']])) # သရေကျလျှင် random

    if len(winners) >= 2:
        next_gw = gw + 1
        random.shuffle(winners)
        batch = db.batch()
        for i in range(0, len(winners), 2):
            if i+1 < len(winners):
                h, a = winners[i], winners[i+1]
                f_id = f"FA_GW{next_gw}_Match_{i//2 + 1}"
                batch.set(db.collection("fixtures").document(f_id), {
                    "gameweek": next_gw, "type": "fa_cup",
                    "home": {"id": h['id'], "name": h['name']},
                    "away": {"id": a['id'], "name": a['name']},
                    "status": "upcoming"
                })
        batch.commit()
        print(f"🏆 FA Cup GW {next_gw} Fixtures Generated!")

if __name__ == "__main__":
    sync_tournament()
