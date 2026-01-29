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

def get_net_points(entry_id, gw_num):
    try:
        url = f"{FPL_API}entry/{entry_id}/event/{gw_num}/picks/"
        res = requests.get(url, timeout=10).json()
        raw_points = res['entry_history']['points']
        transfer_cost = res['entry_history']['event_transfers_cost']
        net_points = raw_points - transfer_cost
        return net_points
    except: return 0

def sync_tournament():
    print(f"--- 🔄 Starting Sync for GW {CURRENT_GW} ---")
    
    try:
        r = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/").json()
        top_48 = sorted(r['standings']['results'], key=lambda x: x['total'], reverse=True)[:48]
    except Exception as e:
        print(f"Error: {e}"); return

    # Firestore ထဲက တွဲဆိုင်းတွေကို အရင်ယူမယ်
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

    # 🔥 အရေးကြီးဆုံးအပိုင်း- Standings ထဲက last_synced_gw ကို အရင်စစ်မယ်
    # တစ်ယောက်ယောက်ရဲ့ record ကို စစ်လိုက်ရုံနဲ့ အပတ်သစ် ဟုတ်မဟုတ် သိနိုင်ပါတယ်
    some_entry_id = str(top_48[0]['entry'])
    some_doc = db.collection("tw_mm_tournament").document(some_entry_id).get()
    
    last_gw = 0
    if some_doc.exists:
        last_gw = some_doc.to_dict().get('last_synced_gw', 0)

    # ၂၄ ပြောင်းထားရင် should_finalize က True ဖြစ်မယ်
    should_finalize = (CURRENT_GW > last_gw)
    
    # Status သတ်မှတ်ချက်- ပတ်လမ်းမပြောင်းသေးရင် "live"၊ ပြောင်းသွားရင် "completed"
    current_status = "completed" if should_finalize else "live"

    h2h_results = {}
    # ၁။ Fixtures အမှတ်များကို Update လုပ်ခြင်း
    for f in fixtures_list:
        fid = f['doc_id']
        h_id, a_id = str(f['home']['id']), str(f['away']['id'])
        h_pts = manager_scores.get(h_id, {'pts': 0})['pts']
        a_pts = manager_scores.get(a_id, {'pts': 0})['pts']

        # 🔥 Status ကို Manual ပြောင်းတဲ့အပေါ်မူတည်ပြီး Dynamic ဖြစ်အောင်လုပ်လိုက်ပါပြီ
        db.collection("fixtures").document(fid).update({
            "home.points": h_pts,
            "away.points": a_pts,
            "status": current_status 
        })

        if f.get('type') == 'league':
            if h_id not in h2h_results: h2h_results[h_id] = {'w':0, 'd':0, 'l':0}
            if a_id not in h2h_results: h2h_results[a_id] = {'w':0, 'd':0, 'l':0}
            if h_pts > a_pts: h2h_results[h_id]['w']=1; h2h_results[a_id]['l']=1
            elif a_pts > h_pts: h2h_results[a_id]['w']=1; h2h_results[h_id]['l']=1
            else: h2h_results[h_id]['d']=1; h2h_results[a_id]['d']=1

    # ၂။ Tournament Standings Update
    for entry_id, data in manager_scores.items():
        doc_ref = db.collection("tw_mm_tournament").document(entry_id)
        doc = doc_ref.get()
        res = h2h_results.get(entry_id, {'w':0, 'd':0, 'l':0})
        h2h_pts = (res['w'] * 3) + (res['d'] * 1)

        current_division = None
        if doc.exists:
            current_division = doc.to_dict().get('division')
        
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
