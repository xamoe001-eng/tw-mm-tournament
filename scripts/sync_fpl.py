import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os, json

def initialize_firebase():
    if not firebase_admin._apps:
        sa_info = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        cred = credentials.Certificate(json.loads(sa_info)) if sa_info else credentials.Certificate('serviceAccountKey.json')
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firebase()
FPL_API = "https://fantasy.premierleague.com/api/"

# ⚠️ GW 24 သတ်မှတ်ချက်
CURRENT_GW = 24  
PREVIOUS_GW = 23

def get_detailed_stats(entry_id, gw_num):
    try:
        # Net Points (Points - Transfer Cost)
        res = requests.get(f"{FPL_API}entry/{entry_id}/event/{gw_num}/picks/", timeout=10).json()
        net_pts = res['entry_history']['points'] - res['entry_history']['event_transfers_cost']
        
        # Tie-break IDs
        picks = res['picks']
        cap_id = next(p for p in picks if p['is_captain'])['element']
        vice_id = next(p for p in picks if p['is_vice_captain'])['element']
        gk_id = next(p for p in picks if p['position'] == 1)['element']

        # Live Player Points
        live_res = requests.get(f"{FPL_API}event/{gw_num}/live/", timeout=10).json()
        elements = {e['id']: e['stats']['total_points'] for e in live_res['elements']}

        return {
            "net_pts": net_pts,
            "cap_pts": elements.get(cap_id, 0) * 2,
            "vice_pts": elements.get(vice_id, 0),
            "gk_pts": elements.get(gk_id, 0)
        }
    except:
        return None

def sync_gw24_live():
    print(f"🚀 GW {CURRENT_GW} Live Sync Started...")

    # ၁။ GW 23 Fixtures ကို 'completed' သတ်မှတ်ခြင်း (တစ်ကြိမ်သာ)
    prev_fixtures = db.collection("fixtures").where("gameweek", "==", PREVIOUS_GW).stream()
    for pf in prev_fixtures:
        db.collection("fixtures").document(pf.id).update({"status": "completed"})

    # ၂။ GW 24 FA Cup Fixtures (၂၄ သင်း / ၁၂ ပွဲ) ကို Live လုပ်ခြင်း
    fa_fixtures = db.collection("fixtures").where("gameweek", "==", CURRENT_GW).stream()
    for f_doc in fa_fixtures:
        f = f_doc.to_dict()
        h_s = get_detailed_stats(f['home']['id'], CURRENT_GW)
        a_s = get_detailed_stats(f['away']['id'], CURRENT_GW)

        if h_s and a_s:
            # Winner Logic (Live အဆင့်မှာတင် နိုင်သူကို အရောင်ပြနိုင်ရန်)
            winner = f['home']['id'] if h_s['net_pts'] >= a_s['net_pts'] else f['away']['id']
            
            db.collection("fixtures").document(f_doc.id).update({
                "home.points": h_s['net_pts'],
                "away.points": a_s['net_pts'],
                "status": "live",
                "tie_break_winner": winner,
                "internal_stats": {
                    "home": {"cap": h_s['cap_pts'], "vice": h_s['vice_pts'], "gk": h_s['gk_pts']},
                    "away": {"cap": a_s['cap_pts'], "vice": a_s['vice_pts'], "gk": a_s['gk_pts']}
                }
            })

    # ၃။ Tournament Table (၄၈ သင်း) Update လုပ်ခြင်း
    managers = db.collection("tw_mm_tournament").stream()
    for m in managers:
        m_data = m.to_dict()
        s = get_detailed_stats(m.id, CURRENT_GW)
        if not s: continue

        # Update Payload
        update_data = {"gw_live_points": s['net_pts']}

        # Total Points ဆက်ပေါင်းရန် Logic (GW ပြောင်းမှသာ တစ်ကြိမ်ပေါင်းမည်)
        if m_data.get('last_synced_gw') == PREVIOUS_GW:
            # GW 23 ရမှတ်ကို Total ထဲသို့ အပြီးသတ်ပေါင်းထည့်သည်
            update_data["tournament_total_net_points"] = firestore.Increment(m_data.get('gw_live_points', 0))
            update_data["last_synced_gw"] = CURRENT_GW

        db.collection("tw_mm_tournament").document(m.id).update(update_data)

    print(f"✅ GW {CURRENT_GW} Sync Success! Standings & FA Cup are now LIVE.")

if __name__ == "__main__":
    sync_gw24_live()
