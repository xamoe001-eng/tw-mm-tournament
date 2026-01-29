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
            try:
                firebase_admin.initialize_app(credentials.Certificate('serviceAccountKey.json'))
            except:
                pass
    return firestore.client()

db = initialize_firebase()

LEAGUE_ID = "400231"
FPL_API = "https://fantasy.premierleague.com/api/"
CURRENT_GW = 23  # ၂၄ လို့ပြောင်းမှ အမှတ်တွေပေါင်းပြီး Status က 'completed' ဖြစ်မှာပါ

def get_player_stats(entry_id, gw_num):
    """ အမှတ်တူလျှင် ခွဲခြားရန် Captain, Vice, GK အမှတ်များကိုပါ ဆွဲထုတ်ခြင်း """
    try:
        url = f"{FPL_API}entry/{entry_id}/event/{gw_num}/picks/"
        res = requests.get(url, timeout=10).json()
        
        picks = res['picks']
        cap_id = next(p for p in picks if p['is_captain'])['element']
        vice_id = next(p for p in picks if p['is_vice_captain'])['element']
        gk_id = picks[0]['element'] # Index 0 သည် Goalkeeper ဖြစ်သည်

        def fetch_pts(p_id):
            p_res = requests.get(f"{FPL_API}element-summary/{p_id}/").json()
            return next(e['event_points'] for e in p_res['history'] if e['event'] == gw_num)

        return {
            "cap_pts": fetch_pts(cap_id),
            "vice_pts": fetch_pts(vice_id),
            "gk_pts": fetch_pts(gk_id)
        }
    except:
        return {"cap_pts": 0, "vice_pts": 0, "gk_pts": 0}

def get_net_points(entry_id, gw_num):
    try:
        url = f"{FPL_API}entry/{entry_id}/event/{gw_num}/picks/"
        res = requests.get(url, timeout=10).json()
        raw_points = res['entry_history']['points']
        transfer_cost = res['entry_history']['event_transfers_cost']
        return raw_points - transfer_cost
    except: return 0

def sync_tournament():
    print(f"--- 🔄 Starting Sync for GW {CURRENT_GW} ---")
    
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
            "initial_index": index
        }

    # last_synced_gw စစ်ဆေးခြင်း
    some_entry_id = str(top_48[0]['entry'])
    some_doc = db.collection("tw_mm_tournament").document(some_entry_id).get()
    last_gw = some_doc.to_dict().get('last_synced_gw', 0) if some_doc.exists else 0
    should_finalize = (CURRENT_GW > last_gw)
    current_status = "completed" if should_finalize else "live"

    h2h_results = {}
    
    for f in fixtures_list:
        fid = f['doc_id']
        h_id, a_id = str(f['home']['id']), str(f['away']['id'])
        h_pts = manager_scores.get(h_id, {'pts': 0})['pts']
        a_pts = manager_scores.get(a_id, {'pts': 0})['pts']

        # 🔥 FA Cup Tie-break Logic (အမှတ်တူလျှင် Captain/GK စစ်မည်)
        winner_id = None
        if f.get('type') == 'fa_cup' and h_pts == a_pts and h_pts > 0:
            print(f"⚖️ Tie-break for FA Cup: {h_id} vs {a_id}")
            h_stats = get_player_stats(h_id, CURRENT_GW)
            a_stats = get_player_stats(a_id, CURRENT_GW)
            
            if h_stats['cap_pts'] != a_stats['cap_pts']:
                winner_id = h_id if h_stats['cap_pts'] > a_stats['cap_pts'] else a_id
            elif h_stats['vice_pts'] != a_stats['vice_pts']:
                winner_id = h_id if h_stats['vice_pts'] > a_stats['vice_pts'] else a_id
            elif h_stats['gk_pts'] != a_stats['gk_pts']:
                winner_id = h_id if h_stats['gk_pts'] > a_stats['gk_pts'] else a_id

        # Fixtures Update
        update_payload = {
            "home.points": h_pts,
            "away.points": a_pts,
            "status": current_status 
        }
        if winner_id: update_payload["tie_break_winner"] = winner_id
        
        db.collection("fixtures").document(fid).update(update_payload)

        # H2H Points Logic (League ပွဲစဉ်များအတွက်သာ)
        if f.get('type') == 'league':
            if h_id not in h2h_results: h2h_results[h_id] = {'w':0, 'd':0, 'l':0}
            if a_id not in h2h_results: h2h_results[a_id] = {'w':0, 'd':0, 'l':0}
            if h_pts > a_pts: h2h_results[h_id]['w']=1; h2h_results[a_id]['l']=1
            elif a_pts > h_pts: h2h_results[a_id]['w']=1; h2h_results[h_id]['l']=1
            else: h2h_results[h_id]['d']=1; h2h_results[a_id]['d']=1

    # Tournament Standings Update
    for entry_id, data in manager_scores.items():
        doc_ref = db.collection("tw_mm_tournament").document(entry_id)
        doc = doc_ref.get()
        res = h2h_results.get(entry_id, {'w':0, 'd':0, 'l':0})
        h2h_pts = (res['w'] * 3) + (res['d'] * 1)

        current_division = doc.to_dict().get('division') if doc.exists else None
        if not current_division:
            current_division = "Division A" if data['initial_index'] < 24 else "Division B"

        update_data = {
            "manager_name": data['name'],
            "team_name": data['team'],
            "division": current_division,
            "gw_live_points": data['pts'],
            "last_synced_gw": CURRENT_GW,
            "last_updated": firestore.SERVER_TIMESTAMP
        }

        if should_finalize:
            update_data.update({
                "played": firestore.Increment(1),
                "wins": firestore.Increment(res['w']),
                "draws": firestore.Increment(res['d']),
                "losses": firestore.Increment(res['l']),
                "h2h_points": firestore.Increment(h2h_pts),
                "tournament_total_net_points": firestore.Increment(data['pts'])
            })

        doc_ref.set(update_data, merge=True)

    print(f"🏁 Sync Success. Mode: {current_status.upper()}")

if __name__ == "__main__":
 
    sync_tournament()
