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
    """ Net Points နှင့် Tie-break အတွက် လိုအပ်သော stats များကို တစ်ခါတည်းယူသည် """
    try:
        # Picks info (Net points + Captain/GK IDs)
        res = requests.get(f"{FPL_API}entry/{entry_id}/event/{gw_num}/picks/", timeout=10).json()
        net_pts = res['entry_history']['points'] - res['entry_history']['event_transfers_cost']
        
        picks = res['picks']
        cap_id = next(p for p in picks if p['is_captain'])['element']
        vice_id = next(p for p in picks if p['is_vice_captain'])['element']
        gk_id = next(p for p in picks if p['position'] == 1)['element']

        # Live points info (Captain/GK/Vice points များကို fetch လုပ်ရန်)
        live_res = requests.get(f"{FPL_API}event/{gw_num}/live/", timeout=10).json()
        elements = {e['id']: e['stats']['total_points'] for e in live_res['elements']}

        return {
            "net_pts": net_pts,
            "cap_pts": elements.get(cap_id, 0),
            "vice_pts": elements.get(vice_id, 0),
            "gk_pts": elements.get(gk_id, 0)
        }
    except Exception as e:
        print(f"⚠️ Skip {entry_id} (API delay): {e}")
        return None

def sync_fpl():
    print(f"--- 🔄 GW {CURRENT_GW} Live Sync Started ---")
    
    # ၁။ Division ခွဲခြားခြင်း (Data မရှိသေးလျှင် တစ်ကြိမ်သာလုပ်မည်)
    tournament_ref = db.collection("tw_mm_tournament")
    if len(tournament_ref.get()) == 0:
        print("📊 Initializing Division A & B from Top 48...")
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

    # ၂။ FA Cup Fixtures Update (Live အမှတ်ပြရန်)
    fa_fixtures = db.collection("fixtures").where("gameweek", "==", CURRENT_GW).stream()
    for f_doc in fa_fixtures:
        f = f_doc.to_dict()
        h_stats = get_detailed_stats(f['home']['id'], CURRENT_GW)
        a_stats = get_detailed_stats(f['away']['id'], CURRENT_GW)

        if h_stats and a_stats:
            # Winner Logic
            winner = None
            if h_stats['net_pts'] > a_stats['net_pts']: winner = f['home']['id']
            elif a_stats['net_pts'] > h_stats['net_pts']: winner = f['away']['id']
            else: # Tie-break
                if h_stats['cap_pts'] != a_stats['cap_pts']: winner = f['home']['id'] if h_stats['cap_pts'] > a_stats['cap_pts'] else f['away']['id']
                elif h_stats['vice_pts'] != a_stats['vice_pts']: winner = f['home']['id'] if h_stats['vice_pts'] > a_stats['vice_pts'] else f['away']['id']
                else: winner = f['home']['id'] if h_stats['gk_pts'] >= a_stats['gk_pts'] else f['away']['id']

            db.collection("fixtures").document(f_doc.id).update({
                "home.points": h_stats['net_pts'],
                "away.points": a_stats['net_pts'],
                "status": "live",
                "tie_break_winner": winner
            })

    # ၃။ League Table (Points Accumulation)
    managers = tournament_ref.stream()
    for m in managers:
        m_data = m.to_dict()
        s = get_detailed_stats(m.id, CURRENT_GW)
        if not s: continue

        update_payload = {"gw_live_points": s['net_pts']}

        # အပတ်ကူးသွားပါက (ဥပမာ GW 24 ရောက်လျှင် GW 23 အမှတ်ကို Total ထဲပေါင်းထည့်မည်)
        if CURRENT_GW > m_data['last_synced_gw'] and m_data['last_synced_gw'] >= START_GW:
            # အရင်အပတ်ရဲ့ Final Net Point ကို ယူရန်
            old_s = get_detailed_stats(m.id, m_data['last_synced_gw'])
            if old_s:
                update_payload["tournament_total_net_points"] = firestore.Increment(old_s['net_pts'])
                # GW 24 ရောက်မှ GW 23 Fixture များကို complete လုပ်ခြင်း
                old_fixtures = db.collection("fixtures").where("gameweek", "==", m_data['last_synced_gw']).stream()
                for old_f in old_fixtures:
                    db.collection("fixtures").document(old_f.id).update({"status": "completed"})

        update_payload["last_synced_gw"] = CURRENT_GW
        tournament_ref.document(m.id).update(update_payload)

    print(f"🏁 GW {CURRENT_GW} Sync Success!")

if __name__ == "__main__":

    sync_fpl()
