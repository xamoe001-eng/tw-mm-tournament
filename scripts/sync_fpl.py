import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os, json

def initialize_firebase():
    if not firebase_admin._apps:
        service_account_info = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        if service_account_info:
            firebase_admin.initialize_app(credentials.Certificate(json.loads(service_account_info)))
        else:
            firebase_admin.initialize_app(credentials.Certificate('serviceAccountKey.json'))
    return firestore.client()

db = initialize_firebase()
CURRENT_GW = 24  # ⚠️ အပတ်စဉ် ပြောင်းပေးရန်

def get_detailed_stats(entry_id, gw_num):
    try:
        url = f"{FPL_API}entry/{entry_id}/event/{gw_num}/picks/"
        res = requests.get(url, timeout=10).json()
        net_pts = res['entry_history']['points'] - res['entry_history']['event_transfers_cost']
        picks = res['picks']
        cap_id = next(p for p in picks if p['is_captain'])['element']
        vice_id = next(p for p in picks if p['is_vice_captain'])['element']
        gk_id = next(p for p in picks if p['position'] == 1)['element']

        def fetch_p_pts(p_id):
            p_res = requests.get(f"https://fantasy.premierleague.com/api/element-summary/{p_id}/").json()
            return next(e['event_points'] for e in p_res['history'] if e['event'] == gw_num)

        return {"net_pts": net_pts, "cap_pts": fetch_p_pts(cap_id), "vice_pts": fetch_p_pts(vice_id), "gk_pts": fetch_p_pts(gk_id)}
    except: return {"net_pts": 0, "cap_pts": 0, "vice_pts": 0, "gk_pts": 0}

def sync_fpl():
    print(f"--- 🔄 Syncing GW {CURRENT_GW} ---")
    
    # ၁။ Transition Check (အပတ်ကူးလျှင် အမှတ်ပေါင်းမည်)
    some_doc = db.collection("tw_mm_tournament").limit(1).get()[0].to_dict()
    last_gw = some_doc.get('last_synced_gw', 0)
    should_finalize = (CURRENT_GW > last_gw and last_gw != 0)

    # ၂။ Update Managers & FA Cup
    fa_fixtures = db.collection("fixtures").where("gameweek", "==", CURRENT_GW).where("type", "==", "fa_cup").stream()
    
    # FA Cup တွဲဖက်များအတွက် Winner ရှာရန် Stats ကြိုယူထားခြင်း (Optimization)
    for f_doc in fa_fixtures:
        f = f_doc.to_dict()
        h_id, a_id = str(f['home']['id']), str(f['away']['id'])
        h_s, a_s = get_detailed_stats(h_id, CURRENT_GW), get_detailed_stats(a_id, CURRENT_GW)

        # Tie-break Logic
        winner = h_id if h_s['net_pts'] > a_s['net_pts'] else a_id if a_s['net_pts'] > h_s['net_pts'] else None
        if not winner: # Tie-break sequence
            if h_s['cap_pts'] != a_s['cap_pts']: winner = h_id if h_s['cap_pts'] > a_s['cap_pts'] else a_id
            elif h_s['vice_pts'] != a_s['vice_pts']: winner = h_id if h_s['vice_pts'] > a_s['vice_pts'] else a_id
            else: winner = h_id if h_s['gk_pts'] >= a_s['gk_pts'] else a_id

        db.collection("fixtures").document(f_doc.id).update({
            "home.points": h_s['net_pts'], "away.points": a_s['net_pts'],
            "tie_break_winner": winner, "status": "live"
        })

    # ၃။ Final Standings Update
    managers = db.collection("tw_mm_tournament").stream()
    for m in managers:
        m_stats = get_detailed_stats(m.id, CURRENT_GW)
        upd = {"gw_live_points": m_stats['net_pts'], "last_synced_gw": CURRENT_GW}
        if should_finalize:
            upd["tournament_total_net_points"] = firestore.Increment(m_stats['net_pts'])
            # အဟောင်းတွေကို complete ပြောင်းရန် (ဥပမာ GW 23)
            old_fs = db.collection("fixtures").where("gameweek", "==", last_gw).stream()
            for of in old_fs: db.collection("fixtures").document(of.id).update({"status": "completed"})

        db.collection("tw_mm_tournament").document(m.id).update(upd)

    print(f"🏁 GW {CURRENT_GW} Sync Success!")

if __name__ == "__main__":
  
    sync_fpl()
