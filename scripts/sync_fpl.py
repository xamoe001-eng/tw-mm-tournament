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
                cred_dict = json.loads(service_account_info)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
            except Exception as e:
                print(f"❌ Error: {e}")
                raise e
        else:
            cred = credentials.Certificate('serviceAccountKey.json')
            firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firebase()

# ၂။ Configuration
LEAGUE_ID = "400231"
FPL_API = "https://fantasy.premierleague.com/api/"
CURRENT_GW = 23  

def get_net_points(entry_id, gw_num):
    """ Chip အမှတ်များ ညှိနှိုင်းပေးခြင်း """
    try:
        url = f"{FPL_API}entry/{entry_id}/event/{gw_num}/picks/"
        res = requests.get(url, timeout=10).json()
        raw_points = res['entry_history']['points']
        transfer_cost = res['entry_history']['event_transfers_cost']
        net_points = raw_points - transfer_cost
        
        active_chip = res.get('active_chip')
        if active_chip == '3xc':
            cap_id = next(p for p in res['picks'] if p['is_captain'])['element']
            p_res = requests.get(f"{FPL_API}element-summary/{cap_id}/", timeout=10).json()
            cap_pts = next(e['event_points'] for e in p_res['history'] if e['event'] == gw_num)
            net_points -= cap_pts
        elif active_chip == 'bboost':
            bench_ids = [p['element'] for p in res['picks'][11:]]
            for b_id in bench_ids:
                b_res = requests.get(f"{FPL_API}element-summary/{b_id}/", timeout=10).json()
                b_pts = next(e['event_points'] for e in b_res['history'] if e['event'] == gw_num)
                net_points -= b_pts
        return net_points
    except:
        return 0

def sync_tournament():
    print(f"--- 🚀 Sync Started: GW {CURRENT_GW} ---")
    
    # Standing ဆွဲယူခြင်း
    try:
        r = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/", timeout=10).json()
        top_48 = sorted(r['standings']['results'], key=lambda x: x['total'], reverse=True)[:48]
    except Exception as e:
        print(f"❌ Standings Error: {e}")
        return

    # Fixtures အချက်အလက်ယူခြင်း
    f_ref = db.collection("fixtures").where("gameweek", "==", CURRENT_GW).stream()
    fixtures_data = {f.id: f.to_dict() for f in f_ref}

    batch = db.batch()
    sync_logs = []

    for index, manager in enumerate(top_48):
        entry_id = str(manager['entry'])
        division = "Division A" if index < 24 else "Division B"
        
        # Guard Logic: ဒီအပတ်အတွက် အမှတ်ပေါင်းပြီးသားဆိုရင် ထပ်မပေါင်းရန်
        doc_ref = db.collection("tw_mm_tournament").document(entry_id)
        existing_doc = doc_ref.get().to_dict()
        
        # အမှတ်မတွက်ရသေးရင် (သို့မဟုတ်) GW အသစ်ဖြစ်ရင် Increment လုပ်မည်
        already_synced = existing_doc.get('last_synced_gw') == CURRENT_GW
        
        net_pts = get_net_points(entry_id, CURRENT_GW)
        
        played, wins, draws, losses, h2h_pts = 0, 0, 0, 0, 0
        active_f = next((f for f in fixtures_data.values() 
                         if f.get('type') == 'league' and (str(f['home']['id']) == entry_id or str(f['away']['id']) == entry_id)), None)

        if active_f and not already_synced:
            played = 1
            is_home = str(active_f['home']['id']) == entry_id
            opp_id = active_f['away']['id'] if is_home else active_f['home']['id']
            opp_net = get_net_points(opp_id, CURRENT_GW)
            
            if net_pts > opp_net: wins, h2h_pts = 1, 3
            elif net_pts == opp_net: draws, h2h_pts = 1, 1
            else: losses = 1

        # Update Data
        update_data = {
            "fpl_id": manager['entry'],
            "manager_name": manager['player_name'],
            "team_name": manager['entry_name'],
            "division": division,
            "gw_points": net_pts,
            "last_synced_gw": CURRENT_GW,
            "last_updated": firestore.SERVER_TIMESTAMP
        }

        # Sync မလုပ်ရသေးမှသာ Total တွေကို Increment လုပ်မည်
        if not already_synced:
            update_data.update({
                "played": firestore.Increment(played),
                "wins": firestore.Increment(wins),
                "draws": firestore.Increment(draws),
                "losses": firestore.Increment(losses),
                "h2h_points": firestore.Increment(h2h_pts),
                "tournament_total_net_points": firestore.Increment(net_pts)
            })

        batch.set(doc_ref, update_data, merge=True)
        sync_logs.append({"id": entry_id, "pts": net_pts, "name": manager['player_name']})
        time.sleep(0.05)

    # ၄။ ပွဲစဉ်ရလဒ်များကို Complete ပြောင်းခြင်းနှင့် History သိမ်းခြင်း
    archive_results(sync_logs, fixtures_data)
    
    batch.commit()
    print(f"✅ GW {CURRENT_GW} Sync Complete & Fixtures Archived.")

    # FA Cup နိုင်သူများ နောက်တစ်ဆင့်တက်ရန်
    if CURRENT_GW < 29:
        generate_next_fa_round(CURRENT_GW)

def archive_results(sync_logs, fixtures_data):
    """ fixtures collection ထဲမှ Status ကို 'completed' ပြောင်းပြီး History သို့ ပို့မည် """
    for fid, f in fixtures_data.items():
        h_pts = next((l['pts'] for l in sync_logs if str(l['id']) == str(f['home']['id'])), 0)
        a_pts = next((l['pts'] for l in sync_logs if str(l['id']) == str(f['away']['id'])), 0)
        
        updated_fixture = {
            **f,
            "home": {**f['home'], "points": h_pts},
            "away": {**f['away'], "points": a_pts},
            "status": "completed" # 👈 ဒီမှာ 'completed' ပြောင်းလိုက်ပါပြီ
        }
        
        # ၁။ မူရင်း fixtures ထဲမှာ Status Update လုပ်မည်
        db.collection("fixtures").document(fid).set(updated_fixture)
        
        # ၂။ History သိမ်းမည်
        col = "fixtures_history_fa" if f.get('type') == 'fa_cup' else f"fixtures_history_gw_{CURRENT_GW}"
        db.collection(col).document(fid).set(updated_fixture)

def generate_next_fa_round(gw):
    """ FA Cup Winner Logic """
    winners = []
    f_ref = db.collection("fixtures_history_fa").where("gameweek", "==", gw).stream()
    
    for doc in f_ref:
        f = doc.to_dict()
        if f['home']['points'] > f['away']['points']: winners.append(f['home'])
        elif f['away']['points'] > f['home']['points']: winners.append(f['away'])
        else: winners.append(random.choice([f['home'], f['away']]))

    if len(winners) >= 2:
        next_gw = gw + 1
        # နောက်အပတ်အတွက် ရှိပြီးသား Fixture ရှိမရှိ အရင်စစ်မည် (Duplicate မဖြစ်အောင်)
        check = db.collection("fixtures").where("gameweek", "==", next_gw).where("type", "==", "fa_cup").limit(1).get()
        if len(check) == 0:
            random.shuffle(winners)
            batch = db.batch()
            for i in range(0, len(winners), 2):
                if i+1 < len(winners):
                    h, a = winners[i], winners[i+1]
                    f_id = f"FA_GW{next_gw}_Match_{i//2 + 1}"
                    batch.set(db.collection("fixtures").document(f_id), {
                        "gameweek": next_gw, "type": "fa_cup",
                        "division": "FA_CUP",
                        "home": {"id": h['id'], "name": h['name']},
                        "away": {"id": a['id'], "name": a['name']},
                        "status": "upcoming"
                    })
            batch.commit()
            print(f"🏆 FA Cup GW {next_gw} Fixtures Generated!")

if __name__ == "__main__":
    sync_tournament()

