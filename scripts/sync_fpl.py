import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import time

def initialize_firebase():
    if not firebase_admin._apps:
        service_account_info = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        if service_account_info:
            cred = credentials.Certificate(json.loads(service_account_info))
            firebase_admin.initialize_app(cred)
        else:
            firebase_admin.initialize_app(credentials.Certificate('serviceAccountKey.json'))
    return firestore.client()

db = initialize_firebase()

LEAGUE_ID = "400231"
FPL_API = "https://fantasy.premierleague.com/api/"
CURRENT_GW = 23  

def check_gw_status(gw):
    """ FPL မှာ ဒီ GW ပွဲစဉ်တွေ အကုန်ပြီးပြီလား စစ်ဆေးခြင်း """
    try:
        r = requests.get(f"{FPL_API}event/{gw}/live/").json()
        # FPL API status check (This is simplified; real check often uses bootstrap-static)
        r_status = requests.get(f"{FPL_API}bootstrap-static/").json()
        current_event = next(e for e in r_status['events'] if e['id'] == gw)
        return current_event['finished']
    except:
        return False

def get_net_points(entry_id, gw_num, is_final):
    """ Live အမှတ်ယူခြင်းနှင့် Chip များ နှုတ်ခြင်း """
    try:
        # Live points from picks
        url = f"{FPL_API}entry/{entry_id}/event/{gw_num}/picks/"
        res = requests.get(url, timeout=10).json()
        
        raw_points = res['entry_history']['points']
        transfer_cost = res['entry_history']['event_transfers_cost']
        net_points = raw_points - transfer_cost
        
        # Game Week ပြီးမှသာ Chip အမှတ်များကို စည်းမျဉ်းအတိုင်း နှုတ်မည်
        if is_final:
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
    except:
        return 0

def sync_tournament():
    is_gw_finished = check_gw_status(CURRENT_GW)
    print(f"--- 🔄 Syncing GW {CURRENT_GW} (Finalized: {is_gw_finished}) ---")
    
    try:
        r = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/").json()
        # Rank 1-48 ကို ခေါ်ယူခြင်း
        top_48 = sorted(r['standings']['results'], key=lambda x: x['total'], reverse=True)[:48]
    except: return

    f_ref = db.collection("fixtures").where("gameweek", "==", CURRENT_GW).stream()
    fixtures_data = {f.id: f.to_dict() for f in f_ref}
    
    batch = db.batch()
    sync_logs = []

    for index, manager in enumerate(top_48):
        entry_id = str(manager['entry'])
        div = "Division A" if index < 24 else "Division B"
        
        # အမှတ်တွက်ခြင်း (ပွဲမပြီးသေးရင် Chip မနှုတ်သေးဘဲ Live ပြမည်)
        net_pts = get_net_points(entry_id, CURRENT_GW, is_gw_finished)
        sync_logs.append({"id": entry_id, "pts": net_pts, "name": manager['player_name']})

        # Tournament Standings Update (GW ပြီးမှသာ Table ထဲ အမှတ်ပေါင်းထည့်မည်)
        doc_ref = db.collection("tw_mm_tournament").document(entry_id)
        
        if is_gw_finished:
            existing = doc_ref.get().to_dict() or {}
            if existing.get('last_synced_gw') != CURRENT_GW:
                # နိုင်/ရှုံး တွက်ရန် logic
                # (H2H logic က ပြီးခဲ့တဲ့ code အတိုင်းပဲဖြစ်လို့ ဒီမှာ အတိုချုံးထားပါတယ်)
                pass # H2H Logic calculation here

        # Website Live Hub အတွက် အမြဲ Update လုပ်ပေးမည်
        batch.set(doc_ref, {
            "manager_name": manager['player_name'],
            "team_name": manager['entry_name'],
            "division": div,
            "gw_live_points": net_pts,
            "last_updated": firestore.SERVER_TIMESTAMP
        }, merge=True)

    # Fixture Update (Live ပြသရန်)
    for fid, f in fixtures_data.items():
        h_pts = next(l['pts'] for l in sync_logs if str(l['id']) == str(f['home']['id']))
        a_pts = next(l['pts'] for l in sync_logs if str(l['id']) == str(f['away']['id']))
        
        new_status = "completed" if is_gw_finished else "live"
        
        f_update = {
            "home.points": h_pts,
            "away.points": a_pts,
            "status": new_status
        }
        batch.update(db.collection("fixtures").document(fid), f_update)
        
        # GW ပြီးသွားရင် History သိမ်းမယ်
        if is_gw_finished:
            col = "fixtures_history_fa" if f.get('type') == 'fa_cup' else f"fixtures_history_gw_{CURRENT_GW}"
            db.collection(col).document(fid).set({**f, "status": "completed", "home": {**f['home'], "points": h_pts}, "away": {**f['away'], "points": a_pts}})

    batch.commit()
    print(f"✅ GW {CURRENT_GW} Synced successfully.")

if __name__ == "__main__":
    sync_tournament()
