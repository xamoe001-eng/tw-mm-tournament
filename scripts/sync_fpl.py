import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

def initialize_firebase():
    if not firebase_admin._apps:
        try:
            firebase_admin.initialize_app(credentials.Certificate('serviceAccountKey.json'))
        except: pass
    return firestore.client()

db = initialize_firebase()

LEAGUE_ID = "400231"
FPL_API = "https://fantasy.premierleague.com/api/"
CURRENT_GW = 24  # ⚠️ အပတ်သစ်ပြောင်းတိုင်း ဒီမှာလာပြင်ပါ

def get_net_points(entry_id, gw_num):
    try:
        url = f"{FPL_API}entry/{entry_id}/event/{gw_num}/picks/"
        res = requests.get(url, timeout=10).json()
        return res['entry_history']['points'] - res['entry_history']['event_transfers_cost']
    except: return 0

def sync_tournament():
    print(f"--- 🔄 Starting Sync for GW {CURRENT_GW} ---")
    
    # ၁။ လက်ရှိ Top 48 Managers ဒေတာယူခြင်း
    try:
        r = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/").json()
        top_48 = sorted(r['standings']['results'], key=lambda x: x['total'], reverse=True)[:48]
    except Exception as e:
        print(f"Error fetching API: {e}"); return

    # ၂။ အပတ်ဟောင်းကို ပိတ်ရန် လို/မလို စစ်ဆေးခြင်း
    some_entry_id = str(top_48[0]['entry'])
    some_doc = db.collection("tw_mm_tournament").document(some_entry_id).get()
    last_gw = some_doc.to_dict().get('last_synced_gw', 0) if some_doc.exists else 0
    
    # အကယ်၍ CURRENT_GW က Firestore ထဲက အပတ်ထက် ကြီးနေရင် Finalize လုပ်မယ်
    should_finalize_previous = (CURRENT_GW > last_gw)

    # ၃။ အကယ်၍ အပတ်ကူးသွားပြီဆိုလျှင် GW အဟောင်းကို 'completed' အရင်သွားပြောင်းပေးမည်
    if should_finalize_previous:
        print(f"🔒 Finalizing Previous GW {last_gw}...")
        old_fixtures = db.collection("fixtures").where("gameweek", "==", last_gw).stream()
        for doc in old_fixtures:
            db.collection("fixtures").document(doc.id).update({"status": "completed"})

    # ၄။ လက်ရှိ GW ပွဲစဉ်များကို Live Update လုပ်ခြင်း
    f_ref = db.collection("fixtures").where("gameweek", "==", CURRENT_GW).stream()
    fixtures_list = [f.to_dict() | {'doc_id': f.id} for f in f_ref]
    
    if not fixtures_list:
        print(f"⚠️ Warning: No fixtures found for GW {CURRENT_GW}. Did you generate them?")

    manager_scores = {}
    h2h_results = {}

    for index, manager in enumerate(top_48):
        entry_id = str(manager['entry'])
        net_pts = get_net_points(entry_id, CURRENT_GW)
        manager_scores[entry_id] = {
            "pts": net_pts,
            "name": manager['player_name'],
            "team": manager['entry_name'],
            "initial_index": index
        }

    # Fixtures ထဲသို့ အမှတ်များသွင်းခြင်း
    for f in fixtures_list:
        fid = f['doc_id']
        h_id, a_id = str(f['home']['id']), str(f['away']['id'])
        h_pts = manager_scores.get(h_id, {'pts': 0})['pts']
        a_pts = manager_scores.get(a_id, {'pts': 0})['pts']

        db.collection("fixtures").document(fid).update({
            "home.points": h_pts,
            "away.points": a_pts,
            "status": "live" # လက်ရှိအပတ်ကို အမြဲ live ပြမည်
        })

        # H2H Point Calculation (League Only)
        if f.get('type') == 'league':
            if h_id not in h2h_results: h2h_results[h_id] = {'w':0, 'd':0, 'l':0}
            if a_id not in h2h_results: h2h_results[a_id] = {'w':0, 'd':0, 'l':0}
            if h_pts > a_pts: h2h_results[h_id]['w']=1; h2h_results[a_id]['l']=1
            elif a_pts > h_pts: h2h_results[a_id]['w']=1; h2h_results[h_id]['l']=1
            else: h2h_results[h_id]['d']=1; h2h_results[a_id]['d']=1

    # ၅။ Standings Update
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

        # အပတ်ကူးသွားမှသာ Tournament Total ထဲသို့ အမှတ်ပေါင်းထည့်မည်
        if should_finalize_previous:
            # ⚠️ သတိပေးချက်- ဤနေရာတွင် last_gw ၏ အမှတ်ကို ပေါင်းရမည်ဖြစ်သော်လည်း 
            # အလွယ်ကူဆုံးမှာ အပတ်ကူးချိန်တွင် finalize_mode ဖြင့် run ရန်ဖြစ်သည်
            update_data.update({
                "played": firestore.Increment(1),
                "wins": firestore.Increment(res['w']),
                "draws": firestore.Increment(res['d']),
                "losses": firestore.Increment(res['l']),
                "h2h_points": firestore.Increment(h2h_pts),
                "tournament_total_net_points": firestore.Increment(data['pts'])
            })

        doc_ref.set(update_data, merge=True)

    print(f"🏁 Sync Success for GW {CURRENT_GW}. Mode: LIVE")

if __name__ == "__main__":
   
    sync_tournament()
