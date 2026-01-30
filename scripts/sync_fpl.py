import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os, json

def initialize_firebase():
    if not firebase_admin._apps:
        sa_info = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        # GitHub Actions အတွက် environment ကဖတ်၊ မရှိရင် local file ကဖတ်
        cred = credentials.Certificate(json.loads(sa_info)) if sa_info else credentials.Certificate('serviceAccountKey.json')
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firebase()
FPL_API = "https://fantasy.premierleague.com/api/"
CURRENT_GW = 23  # ⚠️ အပတ်စဉ် ပြောင်းပေးရန်

def get_detailed_stats(entry_id, gw_num):
    """ Net Points နှင့် Tie-break အတွက် လိုအပ်သော stats များကိုယူသည် """
    try:
        url = f"{FPL_API}entry/{entry_id}/event/{gw_num}/picks/"
        res = requests.get(url, timeout=15).json()
        
        # Net Points = Total - Transfer Cost
        net_pts = res['entry_history']['points'] - res['entry_history']['event_transfers_cost']
        
        # Captain, Vice, GK ID များရှာခြင်း
        picks = res['picks']
        cap_id = next(p for p in picks if p['is_captain'])['element']
        vice_id = next(p for p in picks if p['is_vice_captain'])['element']
        gk_id = next(p for p in picks if p['position'] == 1)['element']

        # ကစားသမားတစ်ဦးချင်းစီ၏ ထိုအပတ်ရမှတ်ကိုယူခြင်း
        def fetch_pts(p_id):
            p_res = requests.get(f"{FPL_API}element-summary/{p_id}/").json()
            return next(e['event_points'] for e in p_res['history'] if e['event'] == gw_num)

        return {
            "net_pts": net_pts,
            "cap_pts": fetch_pts(cap_id),
            "vice_pts": fetch_pts(vice_id),
            "gk_pts": fetch_pts(gk_id)
        }
    except Exception as e:
        print(f"⚠️ Error fetching stats for {entry_id}: {e}")
        return {"net_pts": 0, "cap_pts": 0, "vice_pts": 0, "gk_pts": 0}

def sync_fpl():
    print(f"--- 🔄 Syncing GW {CURRENT_GW} (With Internal Tie-break Logging) ---")
    
    # ၁။ အပတ်ကူးမကူး စစ်ဆေးခြင်း
    some_doc = db.collection("tw_mm_tournament").limit(1).get()[0].to_dict()
    last_gw = some_doc.get('last_synced_gw', 0)
    should_finalize = (CURRENT_GW > last_gw and last_gw != 0)

    # ၂။ FA Cup Live Sync & Internal Tie-break Data
    fa_fixtures = db.collection("fixtures").where("gameweek", "==", CURRENT_GW).where("type", "==", "fa_cup").stream()
    
    for f_doc in fa_fixtures:
        f = f_doc.to_dict()
        h_id, a_id = str(f['home']['id']), str(f['away']['id'])
        h_s = get_detailed_stats(h_id, CURRENT_GW)
        a_s = get_detailed_stats(a_id, CURRENT_GW)
        
        # Winner ဆုံးဖြတ်ခြင်း Logic
        winner = None
        if h_s['net_pts'] > a_s['net_pts']:
            winner = h_id
        elif a_s['net_pts'] > h_s['net_pts']:
            winner = a_id
        else: # Tie-break Sequence
            if h_s['cap_pts'] != a_s['cap_pts']:
                winner = h_id if h_s['cap_pts'] > a_s['cap_pts'] else a_id
            elif h_s['vice_pts'] != a_s['vice_pts']:
                winner = h_id if h_s['vice_pts'] > a_s['vice_pts'] else a_id
            else:
                winner = h_id if h_s['gk_pts'] >= a_s['gk_pts'] else a_id

        # Fixture collection ထဲမှာ internal_tie_break အောက်မှာ သိမ်းမည်
        db.collection("fixtures").document(f_doc.id).update({
            "home.points": h_s['net_pts'],
            "away.points": a_s['net_pts'],
            "status": "live",
            "tie_break_winner": winner,
            "internal_tie_break": {
                "home": {"cap": h_s['cap_pts'], "vice": h_s['vice_pts'], "gk": h_s['gk_pts']},
                "away": {"cap": a_s['cap_pts'], "vice": a_s['vice_pts'], "gk": a_s['gk_pts']}
            }
        })

    # ၃။ Tournament Table & Standings Update
    managers = db.collection("tw_mm_tournament").stream()
    for m in managers:
        s = get_detailed_stats(m.id, CURRENT_GW)
        upd = {"gw_live_points": s['net_pts'], "last_synced_gw": CURRENT_GW}
        
        if should_finalize:
            upd["tournament_total_net_points"] = firestore.Increment(s['net_pts'])
            # အရင်အပတ်ပွဲစဉ်များကို Complete ပြောင်းသည်
            for of in db.collection("fixtures").where("gameweek", "==", last_gw).stream():
                db.collection("fixtures").document(of.id).update({"status": "completed"})
        
        db.collection("tw_mm_tournament").document(m.id).update(upd)

    print(f"🏁 GW {CURRENT_GW} Sync Success! Tie-break stats logged in collection.")

if __name__ == "__main__":
    
    sync_fpl()
