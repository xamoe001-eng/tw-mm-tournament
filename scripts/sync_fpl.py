import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

# Firebase Initialize & Config အပိုင်းတွေက အရင်အတိုင်းပါပဲ...
def initialize_firebase():
    if not firebase_admin._apps:
        service_account_info = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        if service_account_info:
            cred = credentials.Certificate(json.loads(service_account_info))
            firebase_admin.initialize_app(cred)
        else:
            try:
                firebase_admin.initialize_app(credentials.Certificate('serviceAccountKey.json'))
            except:
                pass
    return firestore.client()

db = initialize_firebase()

LEAGUE_ID = "400231"
FPL_API = "https://fantasy.premierleague.com/api/"
CURRENT_GW = 23  # ⚠️ ဒီနံပါတ်ကို ၂၄ လို့ ပြောင်းမှသာ အမှတ်တွေ စုပေါင်းသွားမှာပါ

def get_net_points(entry_id, gw_num):
    # Chips & Transfer Costs တွက်တဲ့အပိုင်း (မပြောင်းလဲပါ)
    try:
        url = f"{FPL_API}entry/{entry_id}/event/{gw_num}/picks/"
        res = requests.get(url, timeout=10).json()
        raw_points = res['entry_history']['points']
        transfer_cost = res['entry_history']['event_transfers_cost']
        net_points = raw_points - transfer_cost
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
    except: return 0

def sync_tournament():
    print(f"--- 🔄 Running Sync for GW {CURRENT_GW} ---")
    
    try:
        r = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/").json()
        top_48 = sorted(r['standings']['results'], key=lambda x: x['total'], reverse=True)[:48]
    except Exception as e:
        print(f"Error: {e}"); return

    f_ref = db.collection("fixtures").where("gameweek", "==", CURRENT_GW).stream()
    fixtures_list = [f.to_dict() | {'doc_id': f.id} for f in f_ref]
    
    manager_scores = {}
    for index, manager in enumerate(top_48):
        entry_id = str(manager['entry'])
        manager_scores[entry_id] = {
            "pts": get_net_points(entry_id, CURRENT_GW),
            "name": manager['player_name'],
            "team": manager['entry_name'],
            "index": index
        }

    h2h_results = {}
    for f in fixtures_list:
        fid = f['doc_id']
        h_id, a_id = str(f['home']['id']), str(f['away']['id'])
        h_pts = manager_scores.get(h_id, {'pts': 0})['pts']
        a_pts = manager_scores.get(a_id, {'pts': 0})['pts']

        # Fixtures ကို Live Update အမြဲလုပ်မယ်
        db.collection("fixtures").document(fid).update({
            "home.points": h_pts, "away.points": a_pts, "status": "live"
        })

        if f.get('type') == 'league':
            if h_id not in h2h_results: h2h_results[h_id] = {'w':0, 'd':0, 'l':0}
            if a_id not in h2h_results: h2h_results[a_id] = {'w':0, 'd':0, 'l':0}
            if h_pts > a_pts: h2h_results[h_id]['w']=1; h2h_results[a_id]['l']=1
            elif a_pts > h_pts: h2h_results[a_id]['w']=1; h2h_results[h_id]['l']=1
            else: h2h_results[h_id]['d']=1; h2h_results[a_id]['d']=1

    # ၂။ Standings Logic (GW Change Protection)
    for entry_id, data in manager_scores.items():
        doc_ref = db.collection("tw_mm_tournament").document(entry_id)
        doc = doc_ref.get()
        res = h2h_results.get(entry_id, {'w':0, 'd':0, 'l':0})
        h2h_pts = (res['w'] * 3) + (res['d'] * 1)

        # 🔥 Safety Logic: အရင်က သိမ်းခဲ့တဲ့ GW ထက် ကြီးမှသာ အမှတ်ပေါင်းမယ်
        should_increment = False
        if doc.exists:
            last_gw = doc.to_dict().get('last_synced_gw', 0)
            if CURRENT_GW > last_gw:
                should_increment = True
        else:
            should_increment = True # ပထမဆုံးအကြိမ်ဆိုရင် ပေါင်းမယ်

        update_data = {
            "manager_name": data['name'],
            "team_name": data['team'],
            "gw_live_points": data['pts'],
            "last_synced_gw": CURRENT_GW,
            "last_updated": firestore.SERVER_TIMESTAMP
        }

        if should_increment:
            # အပတ်သစ်ရောက်မှ (+1) တိုးမည့်အချက်များ
            update_data.update({
                "played": firestore.Increment(1),
                "wins": firestore.Increment(res['w']),
                "draws": firestore.Increment(res['d']),
                "losses": firestore.Increment(res['l']),
                "h2h_points": firestore.Increment(h2h_pts),
                "tournament_total_net_points": firestore.Increment(data['pts'])
            })
            # Fixture ကိုလည်း ပွဲပြီးကြောင်း သတ်မှတ်
            print(f"✅ Incrementing scores for {data['name']} (GW {CURRENT_GW})")

        doc_ref.set(update_data, merge=True)

        # History သိမ်းတာကတော့ အမြဲ Update ဖြစ်နေမယ်
        history_id = f"{entry_id}_GW{CURRENT_GW}"
        db.collection("fixtures_history").document(history_id).set({
            "entry_id": entry_id, "gameweek": CURRENT_GW, 
            "points": data['pts'], "manager_name": data['name']
        }, merge=True)

    print(f"🏁 Sync Finished for GW {CURRENT_GW}")

if __name__ == "__main__":
    sync_tournament()
