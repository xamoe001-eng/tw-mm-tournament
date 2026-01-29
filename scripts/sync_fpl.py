import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

def initialize_firebase():
    if not firebase_admin._apps:
        service_account_info = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        if service_account_info:
            cred = credentials.Certificate(json.loads(service_account_info))
            firebase_admin.initialize_app(cred)
        else:
            # Local testing အတွက်
            try:
                firebase_admin.initialize_app(credentials.Certificate('serviceAccountKey.json'))
            except:
                pass
    return firestore.client()

db = initialize_firebase()

LEAGUE_ID = "400231"
FPL_API = "https://fantasy.premierleague.com/api/"
CURRENT_GW = 23  

def get_net_points(entry_id, gw_num):
    """ Manager တစ်ယောက်ချင်းစီရဲ့ အမှတ်ကို ဆွဲထုတ်ခြင်း """
    try:
        url = f"{FPL_API}entry/{entry_id}/event/{gw_num}/picks/"
        res = requests.get(url, timeout=10).json()
        raw_points = res['entry_history']['points']
        transfer_cost = res['entry_history']['event_transfers_cost']
        return raw_points - transfer_cost
    except:
        return 0

def sync_tournament():
    # Force Sync လုပ်ရန် True ထားပါသည်
    is_gw_finished = True 
    print(f"--- 🔄 Starting Clean Sync for GW {CURRENT_GW} ---")
    
    try:
        # League Standings ကို ဆွဲယူပြီး Rank အလိုက် စီခြင်း
        r = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/").json()
        top_48 = sorted(r['standings']['results'], key=lambda x: x['total'], reverse=True)[:48]
    except Exception as e:
        print(f"Error fetching standings: {e}")
        return

    # Fixtures ကို Database ထဲက ဆွဲထုတ်ခြင်း
    f_ref = db.collection("fixtures").where("gameweek", "==", CURRENT_GW).stream()
    fixtures_list = [f.to_dict() | {'doc_id': f.id} for f in f_ref]
    
    manager_scores = {}
    print("Fetching player points...")
    for index, manager in enumerate(top_48):
        entry_id = str(manager['entry'])
        net_pts = get_net_points(entry_id, CURRENT_GW)
        manager_scores[entry_id] = {
            "pts": net_pts,
            "name": manager['player_name'],
            "team": manager['entry_name'],
            "index": index
        }

    batch = db.batch()
    h2h_results = {}

    # ၁။ Fixtures မှာ အမှတ်သွင်းခြင်းနှင့် H2H Logic တွက်ချက်ခြင်း
    for f in fixtures_list:
        fid = f['doc_id']
        h_id, a_id = str(f['home']['id']), str(f['away']['id'])
        
        # ID မကိုက်ညီခဲ့လျှင် 0 ပေးရန် default value သုံးထားသည်
        h_pts = manager_scores.get(h_id, {'pts': 0})['pts']
        a_pts = manager_scores.get(a_id, {'pts': 0})['pts']

        # Fixture Update (Home/Away Points)
        batch.update(db.collection("fixtures").document(fid), {
            "home.points": h_pts,
            "away.points": a_pts,
            "status": "completed"
        })

        # H2H Points Logic (W/D/L)
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

    # ၂။ Tournament Standings Table Update
    for entry_id, data in manager_scores.items():
        doc_ref = db.collection("tw_mm_tournament").document(entry_id)
        div = "Division A" if data['index'] < 24 else "Division B"
        
        res = h2h_results.get(entry_id, {'w':0, 'd':0, 'l':0})
        h2h_pts = (res['w'] * 3) + (res['d'] * 1)

        # 🔥 Set သုံးထားလို့ Workflow ခဏခဏ Run လည်း အမှတ်မပွတော့ပါ
        batch.set(doc_ref, {
            "manager_name": data['name'],
            "team_name": data['team'],
            "division": div,
            "gw_live_points": data['pts'], 
            "played": 1,
            "wins": res['w'],
            "draws": res['d'],
            "losses": res['l'],
            "h2h_points": h2h_pts,
            "tournament_total_net_points": data['pts'],
            "last_synced_gw": CURRENT_GW,
            "last_updated": firestore.SERVER_TIMESTAMP
        }, merge=True)

    batch.commit()
    print(f"✅ GW {CURRENT_GW} Clean Sync Completed. Standings and Fixtures updated.")

if __name__ == "__main__":
    sync_tournament()
