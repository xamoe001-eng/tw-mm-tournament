import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import time

def initialize_firebase():
    if not firebase_admin._apps:
        service_account_info = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        if service_account_info:
            cred = credentials.Certificate(json.loads(service_account_info))
            firebase_admin.initialize_app(cred)
        else:
            firebase_admin.initialize_app(credentials.Certificate('serviceAccountKey.json'))
    return firestore.client()

db = initialize_firebase()

LEAGUE_ID = "400231"
FPL_API = "https://fantasy.premierleague.com/api/"
CURRENT_GW = 23  

def check_gw_status(gw):
    """ FPL မှာ ဒီ GW ပွဲစဉ်တွေ အကုန်ပြီးပြီလား စစ်ဆေးခြင်း """
    try:
        r_status = requests.get(f"{FPL_API}bootstrap-static/").json()
        current_event = next(e for e in r_status['events'] if e['id'] == gw)
        return current_event['finished']
    except:
        return False

def get_net_points(entry_id, gw_num, is_final):
    """ Live အမှတ်ယူခြင်းနှင့် Chip များ နှုတ်ခြင်း """
    try:
        url = f"{FPL_API}entry/{entry_id}/event/{gw_num}/picks/"
        res = requests.get(url, timeout=10).json()
        
        raw_points = res['entry_history']['points']
        transfer_cost = res['entry_history']['event_transfers_cost']
        net_points = raw_points - transfer_cost
        
        if is_final:
            active_chip = res.get('active_chip')
            if active_chip == '3xc':
                cap_id = next(p for p in res['picks'] if p['is_captain'])['element']
                p_res = requests.get(f"{FPL_API}element-summary/{cap_id}/").json()
                cap_pts = next(e['event_points'] for e in p_res['history'] if e['event'] == gw_num)
                net_points -= cap_pts
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
    # 🔥 Manual Force Sync: အမှတ်တွေ ချက်ချင်းပေါင်းရန် True ဟု ပြင်ထားသည်
    is_gw_finished = True 
    print(f"--- 🔄 Force Syncing GW {CURRENT_GW} (Status: Finalized) ---")
    
    try:
        r = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/").json()
        top_48 = sorted(r['standings']['results'], key=lambda x: x['total'], reverse=True)[:48]
    except Exception as e:
        print(f"Error fetching standings: {e}")
        return

    # Fixtures ကို ကြိုဆွဲထားမယ်
    f_ref = db.collection("fixtures").where("gameweek", "==", CURRENT_GW).stream()
    fixtures_list = [f.to_dict() | {'doc_id': f.id} for f in f_ref]
    
    # Manager တစ်ယောက်ချင်းစီရဲ့ Point တွေကို သိမ်းထားဖို့ dictionary
    manager_scores = {}

    print("Fetching points for all managers...")
    for index, manager in enumerate(top_48):
        entry_id = str(manager['entry'])
        net_pts = get_net_points(entry_id, CURRENT_GW, is_gw_finished)
        manager_scores[entry_id] = {
            "pts": net_pts,
            "name": manager['player_name'],
            "team": manager['entry_name'],
            "index": index
        }

    batch = db.batch()

    # ၁။ Fixtures Update နှင့် H2H Logic တွက်ချက်ခြင်း
    h2h_results = {} # {manager_id: {'win': 0, 'draw': 0, 'loss': 0}}

    for f in fixtures_list:
        fid = f['doc_id']
        h_id = str(f['home']['id'])
        a_id = str(f['away']['id'])

        h_pts = manager_scores.get(h_id, {'pts': 0})['pts']
        a_pts = manager_scores.get(a_id, {'pts': 0})['pts']

        # Fixture points update
        f_ref_doc = db.collection("fixtures").document(fid)
        batch.update(f_ref_doc, {
            "home.points": h_pts,
            "away.points": a_pts,
            "status": "completed"
        })

        # H2H Points Logic (နိုင်/ရှုံး/သရေ)
        if h_id not in h2h_results: h2h_results[h_id] = {'w':0, 'd':0, 'l':0}
        if a_id not in h2h_results: h2h_results[a_id] = {'w':0, 'd':0, 'l':0}

        if h_pts > a_pts:
            h2h_results[h_id]['w'] += 1
            h2h_results[a_id]['l'] += 1
        elif a_pts > h_pts:
            h2h_results[a_id]['w'] += 1
            h2h_results[h_id]['l'] += 1
        else:
            h2h_results[h_id]['d'] += 1
            h2h_results[a_id]['d'] += 1

        # GW ပြီးသွားရင် History သိမ်းမယ်
        col_hist = "fixtures_history_fa" if f.get('type') == 'fa_cup' else f"fixtures_history_gw_{CURRENT_GW}"
        hist_ref = db.collection(col_hist).document(fid)
        batch.set(hist_ref, {**f, "status": "completed", "home": {**f['home'], "points": h_pts}, "away": {**f['away'], "points": a_pts}})

    # ၂။ Tournament Standings Update
    for entry_id, data in manager_scores.items():
        doc_ref = db.collection("tw_mm_tournament").document(entry_id)
        div = "Division A" if data['index'] < 24 else "Division B"
        
        res = h2h_results.get(entry_id, {'w':0, 'd':0, 'l':0})
        h2h_pts = (res['w'] * 3) + (res['d'] * 1)

        # လက်ရှိရမှတ်များကို Update လုပ်ခြင်း
        update_data = {
            "manager_name": data['name'],
            "team_name": data['team'],
            "division": div,
            "gw_live_points": data['pts'],
            "last_updated": firestore.SERVER_TIMESTAMP
        }

        # GW ပြီးပြီဖြစ်၍ နိုင်/ရှုံး/ကစားပွဲ အရေအတွက်ကို တစ်ခါတည်းပေါင်းမည်
        existing = doc_ref.get().to_dict() or {}
        if existing.get('last_synced_gw') != CURRENT_GW:
            update_data.update({
                "played": firestore.Increment(1),
                "wins": firestore.Increment(res['w']),
                "draws": firestore.Increment(res['d']),
                "losses": firestore.Increment(res['l']),
                "h2h_points": firestore.Increment(h2h_pts),
                "tournament_total_net_points": firestore.Increment(data['pts']),
                "last_synced_gw": CURRENT_GW
            })

        batch.set(doc_ref, update_data, merge=True)

    batch.commit()
    print(f"✅ GW {CURRENT_GW} Forced Sync completed. Standings and Fixtures updated.")

if __name__ == "__main__":

    sync_tournament()
