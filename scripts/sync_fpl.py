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
LEAGUE_ID = "400231"
CURRENT_GW = 23  
START_GW = 23
END_GW = 29

def get_detailed_stats(entry_id, gw_num):
    """ Net Points နှင့် Tie-break (Cap/Vice/GK) stats များကိုယူသည် """
    try:
        # ၁။ Player Picks (Captain/GK IDs ကိုယူရန်)
        res = requests.get(f"{FPL_API}entry/{entry_id}/event/{gw_num}/picks/", timeout=10).json()
        net_pts = res['entry_history']['points'] - res['entry_history']['event_transfers_cost']
        
        picks = res['picks']
        cap_id = next(p for p in picks if p['is_captain'])['element']
        vice_id = next(p for p in picks if p['is_vice_captain'])['element']
        gk_id = next(p for p in picks if p['position'] == 1)['element']

        # ၂။ Live Points (IDs များမှတစ်ဆင့် Point ပြန်ရှာရန်)
        # မှတ်ချက် - API performance အတွက် တစ်ခါပဲ ခေါ်ယူရန် လိုအပ်သော်လည်း function သီးခြားဖြစ်၍ ဤနေရာတွင် ခေါ်ထားသည်
        live_res = requests.get(f"{FPL_API}event/{gw_num}/live/", timeout=10).json()
        elements = {e['id']: e['stats']['total_points'] for e in live_res['elements']}

        # Captain point ကို x2 တွက်ပေးရန် (FPL point အတိုင်း)
        cap_pts = elements.get(cap_id, 0) * 2

        return {
            "net_pts": net_pts,
            "cap_pts": cap_pts,
            "vice_pts": elements.get(vice_id, 0),
            "gk_pts": elements.get(gk_id, 0)
        }
    except Exception as e:
        print(f"⚠️ API Error for {entry_id}: {e}")
        return None

def sync_fpl():
    print(f"--- 🔄 GW {CURRENT_GW} Live Sync Started ---")
    
    tournament_ref = db.collection("tw_mm_tournament")
    
    # ၁။ Division Initializing (ပထမဆုံးအကြိမ်သာ)
    if len(tournament_ref.limit(1).get()) == 0:
        print("📊 Mapping Divisions from Top 48...")
        r = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/").json()
        top_48 = r['standings']['results'][:48]
        for index, m in enumerate(top_48):
            div = "Division A" if index < 24 else "Division B"
            tournament_ref.document(str(m['entry'])).set({
                "id": str(m['entry']),
                "name": m['player_name'],
                "team": m['entry_name'],
                "division": div,
                "tournament_total_net_points": 0,
                "gw_live_points": 0,
                "last_synced_gw": START_GW - 1
            })

    # ၂။ FA Cup Fixtures Update (Tie-break stats များပါထည့်သွင်းခြင်း)
    fa_fixtures = db.collection("fixtures").where("gameweek", "==", CURRENT_GW).stream()
    for f_doc in fa_fixtures:
        f = f_doc.to_dict()
        h_s = get_detailed_stats(f['home']['id'], CURRENT_GW)
        a_s = get_detailed_stats(f['away']['id'], CURRENT_GW)

        if h_s and a_s:
            # Winner Decision Logic
            winner = None
            reason = "Points"
            if h_s['net_pts'] > a_s['net_pts']:
                winner = f['home']['id']
            elif a_s['net_pts'] > h_s['net_pts']:
                winner = f['away']['id']
            else: # Tie-break Logic
                if h_s['cap_pts'] != a_s['cap_pts']:
                    winner = f['home']['id'] if h_s['cap_pts'] > a_s['cap_pts'] else f['away']['id']
                    reason = "Tie-break: Captain Points"
                elif h_s['vice_pts'] != a_s['vice_pts']:
                    winner = f['home']['id'] if h_s['vice_pts'] > a_s['vice_pts'] else f['away']['id']
                    reason = "Tie-break: Vice-Captain Points"
                else:
                    winner = f['home']['id'] if h_s['gk_pts'] >= a_s['gk_pts'] else f['away']['id']
                    reason = "Tie-break: GK Points"

            # Fixture ထဲသို့ အမှတ်များနှင့် stats များထည့်ခြင်း
            db.collection("fixtures").document(f_doc.id).update({
                "home.points": h_s['net_pts'],
                "away.points": a_s['net_pts'],
                "status": "live",
                "tie_break_winner": winner,
                "tie_break_reason": reason,
                "internal_stats": {
                    "home": {"cap": h_s['cap_pts'], "vice": h_s['vice_pts'], "gk": h_s['gk_pts']},
                    "away": {"cap": a_s['cap_pts'], "vice": a_s['vice_pts'], "gk": a_s['gk_pts']}
                }
            })

    # ၃။ League Table Points Update
    managers = tournament_ref.stream()
    for m in managers:
        m_data = m.to_dict()
        s = get_detailed_stats(m.id, CURRENT_GW)
        if not s: continue

        update_payload = {"gw_live_points": s['net_pts']}

        # GW အပြောင်းအလဲတွင် point ဟောင်းကို total ထဲပေါင်းထည့်ခြင်း
        if CURRENT_GW > m_data['last_synced_gw'] and m_data['last_synced_gw'] >= START_GW:
            old_s = get_detailed_stats(m.id, m_data['last_synced_gw'])
            if old_s:
                update_payload["tournament_total_net_points"] = firestore.Increment(old_s['net_pts'])
                # အရင်အပတ် Fixture များကို completed ပြောင်းခြင်း
                old_f_list = db.collection("fixtures").where("gameweek", "==", m_data['last_synced_gw']).stream()
                for old_f in old_f_list:
                    db.collection("fixtures").document(old_f.id).update({"status": "completed"})

        update_payload["last_synced_gw"] = CURRENT_GW
        tournament_ref.document(m.id).update(update_payload)

    print(f"🏁 GW {CURRENT_GW} Sync Success with Tie-break stats!")

if __name__ == "__main__":
    
    sync_fpl()
