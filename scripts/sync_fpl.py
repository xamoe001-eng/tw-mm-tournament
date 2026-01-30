import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

def initialize_firebase():
    """Firebase ကို Environment Variable သို့မဟုတ် File မှ တစ်ဆင့် Initialize လုပ်သည်"""
    if not firebase_admin._apps:
        # GitHub Secrets (Environment Variable) ကို အရင်စစ်သည်
        service_account_info = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        
        if service_account_info:
            try:
                cred_dict = json.loads(service_account_info)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                print("✅ Firebase initialized via Environment Variable.")
            except Exception as e:
                print(f"❌ JSON Parsing Error: {e}")
        else:
            # Local တွင် Run လျှင် serviceAccountKey.json ကို သုံးမည်
            try:
                cred = credentials.Certificate('serviceAccountKey.json')
                firebase_admin.initialize_app(cred)
                print("✅ Firebase initialized via JSON file.")
            except Exception as e:
                print(f"❌ Local JSON file not found: {e}")
                raise e
    return firestore.client()

db = initialize_firebase()

# --- Configuration ---
LEAGUE_ID = "400231"
FPL_API = "https://fantasy.premierleague.com/api/"
CURRENT_GW = 24  # ⚠️ အပတ်သစ်ပြောင်းတိုင်း ဤနေရာတွင် ပြင်ပါ

def get_net_points(entry_id, gw_num):
    """API မှ Net Points (Total - Transfer Cost) ကို တွက်ယူသည်"""
    try:
        url = f"{FPL_API}entry/{entry_id}/event/{gw_num}/picks/"
        res = requests.get(url, timeout=10).json()
        raw_points = res['entry_history']['points']
        transfer_cost = res['entry_history']['event_transfers_cost']
        return raw_points - transfer_cost
    except Exception as e:
        print(f"⚠️ Error fetching points for {entry_id}: {e}")
        return 0

def sync_tournament():
    print(f"--- 🔄 Starting Sync for GW {CURRENT_GW} ---")
    
    # ၁။ FPL Standings မှ Data ယူခြင်း
    try:
        r = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/").json()
        top_48 = sorted(r['standings']['results'], key=lambda x: x['total'], reverse=True)[:48]
    except Exception as e:
        print(f"❌ Error fetching FPL API: {e}"); return

    # ၂။ အပတ်ကူး/မကူး စစ်ဆေးခြင်း (Finalize Logic)
    # Tournament ထဲက Manager တစ်ယောက်ရဲ့ ဒေတာကို နမူနာယူစစ်ဆေးသည်
    some_entry_id = str(top_48[0]['entry'])
    some_doc = db.collection("tw_mm_tournament").document(some_entry_id).get()
    
    last_gw = 0
    if some_doc.exists:
        last_gw = some_doc.to_dict().get('last_synced_gw', 0)
    
    # လက်ရှိအပတ်က Firestore ထဲက အပတ်ထက် ကြီးနေလျှင် အရင်အပတ်ကို ပိတ်မည်
    should_finalize_previous = (CURRENT_GW > last_gw and last_gw != 0)

    # ၃။ အရင်အပတ် (GW 23) ကို 'completed' ပြောင်းခြင်း
    if should_finalize_previous:
        print(f"🔒 GW {last_gw} is over. Finalizing records...")
        old_fixtures = db.collection("fixtures").where("gameweek", "==", last_gw).stream()
        for doc in old_fixtures:
            db.collection("fixtures").document(doc.id).update({"status": "completed"})

    # ၄။ လက်ရှိအပတ် (GW 24) ပွဲစဉ်များကို Live Update လုပ်ခြင်း
    f_ref = db.collection("fixtures").where("gameweek", "==", CURRENT_GW).stream()
    fixtures_list = [f.to_dict() | {'doc_id': f.id} for f in f_ref]
    
    if not fixtures_list:
        print(f"⚠️ Warning: No fixtures found for GW {CURRENT_GW}. Please check Fixture Generator.")

    manager_scores = {}
    h2h_results = {}

    for index, manager in enumerate(top_48):
        entry_id = str(manager['entry'])
        pts = get_net_points(entry_id, CURRENT_GW)
        manager_scores[entry_id] = {
            "pts": pts,
            "name": manager['player_name'],
            "team": manager['entry_name'],
            "initial_index": index
        }

    # Fixtures ထဲသို့ အမှတ်များ Update လုပ်ခြင်း
    for f in fixtures_list:
        fid = f['doc_id']
        h_id, a_id = str(f['home']['id']), str(f['away']['id'])
        h_pts = manager_scores.get(h_id, {'pts': 0})['pts']
        a_pts = manager_scores.get(a_id, {'pts': 0})['pts']

        db.collection("fixtures").document(fid).update({
            "home.points": h_pts,
            "away.points": a_pts,
            "status": "live"
        })

        # H2H Point Calculation (League Only)
        if f.get('type') == 'league':
            if h_id not in h2h_results: h2h_results[h_id] = {'w':0, 'd':0, 'l':0}
            if a_id not in h2h_results: h2h_results[a_id] = {'w':0, 'd':0, 'l':0}
            if h_pts > a_pts: h2h_results[h_id]['w']=1; h2h_results[a_id]['l']=1
            elif a_pts > h_pts: h2h_results[a_id]['w']=1; h2h_results[h_id]['l']=1
            else: h2h_results[h_id]['d']=1; h2h_results[a_id]['d']=1

    # ၅။ Standings (Tournament Table) Update လုပ်ခြင်း
    for entry_id, data in manager_scores.items():
        doc_ref = db.collection("tw_mm_tournament").document(entry_id)
        res = h2h_results.get(entry_id, {'w':0, 'd':0, 'l':0})
        h2h_pts = (res['w'] * 3) + (res['d'] * 1)

        update_data = {
            "manager_name": data['name'],
            "team_name": data['team'],
            "gw_live_points": data['pts'],
            "last_synced_gw": CURRENT_GW,
            "last_updated": firestore.SERVER_TIMESTAMP
        }

        # အပတ်ကူးချိန်တွင်သာ စုစုပေါင်းမှတ်များကို Increment လုပ်မည်
        if should_finalize_previous:
            update_data.update({
                "played": firestore.Increment(1),
                "wins": firestore.Increment(res['w']),
                "draws": firestore.Increment(res['d']),
                "losses": firestore.Increment(res['l']),
                "h2h_points": firestore.Increment(h2h_pts),
                "tournament_total_net_points": firestore.Increment(data['pts'])
            })

        doc_ref.set(update_data, merge=True)

    print(f"🏁 Sync Completed for GW {CURRENT_GW}. Status: LIVE")

if __name__ == "__main__":
   
    sync_tournament()
