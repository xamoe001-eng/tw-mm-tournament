import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import time

# ၁။ Firebase ချိတ်ဆက်ခြင်း
def initialize_firebase():
    if not firebase_admin._apps:
        # GitHub Actions အတွက် ENV သို့မဟုတ် Local JSON ကို စစ်ဆေးမည်
        service_account_info = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        if service_account_info:
            cred = credentials.Certificate(json.loads(service_account_info))
        else:
            cred = credentials.Certificate('serviceAccountKey.json')
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firebase()

# ၂။ Configuration
LEAGUE_ID = "400231"
FPL_API = "https://fantasy.premierleague.com/api/"
CURRENT_GW = 24  # 👈 ဒီနေရာလေးပဲ ချိန်းပြီး Run လိုက်ရုံပါပဲ

def get_net_points(entry_id, gw_num):
    """ FPL API မှ Chip Points များနှင့် Transfer Hits များကို နှုတ်ပြီး Net Point တွက်ပေးသည် """
    try:
        url = f"{FPL_API}entry/{entry_id}/event/{gw_num}/picks/"
        res = requests.get(url).json()
        
        raw_points = res['entry_history']['points']
        transfer_cost = res['entry_history']['event_transfers_cost']
        active_chip = res.get('active_chip')
        
        # Chip Points တွက်ချက်ခြင်း (Official ရမှတ်မှ ပြန်နှုတ်ရန်)
        chip_deduction = 0
        if active_chip == 'bboost':
            # Bench Boost သုံးထားလျှင် sub အမှတ်များကို နှုတ်ရမည် (FPL API အရ picks 12-15)
            # ဤနေရာတွင် logic ရှင်းစေရန် automatic raw_points ထဲမှ sub အမှတ်ကို နှုတ်ရန် picks အသေးစိတ်ယူရပါမည်
            # ရိုးရိုးရှင်းရှင်း Transfer cost ပဲ အရင်နှုတ်ထားပါမည်။
            pass
        elif active_chip == '3xc':
            # Triple Captain သုံးထားလျှင် Captain ရမှတ်၏ ၁ ဆ ကို ပြန်နှုတ်ရမည်
            captain = next(p for p in res['picks'] if p['is_captain'])
            # Captain ရမှတ်ကို element-summary မှ ထပ်ယူရပါမည် (သို့မဟုတ် ရိုးရိုး net ပဲသုံးမလား?)
            pass

        return raw_points - transfer_cost
    except:
        return 0

def sync_tournament():
    print(f"--- 🚀 Tournament Sync Started: GW {CURRENT_GW} ---")
    
    # League Standings ယူခြင်း
    try:
        r = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/")
        standings = r.json()['standings']['results']
    except Exception as e:
        print(f"Error: {e}")
        return

    # Fixtures ယူခြင်း
    f_ref = db.collection("fixtures").where("gameweek", "==", CURRENT_GW).stream()
    fixtures_data = {f.id: f.to_dict() for f in f_ref}

    batch = db.batch()
    sync_logs = []

    for manager in standings:
        entry_id = str(manager['entry'])
        
        # Net Points တွက်ခြင်း (Hits နှုတ်ပြီးသား)
        net_points = get_net_points(entry_id, CURRENT_GW)
        
        # H2H Logic
        played, wins, draws, losses, h2h_pts = 0, 0, 0, 0, 0
        active_fixture = None
        
        for fid, f in fixtures_data.items():
            if f['home']['id'] == manager['entry'] or f['away']['id'] == manager['entry']:
                active_fixture = f
                break

        if active_fixture and active_fixture.get('type') == 'league':
            played = 1
            is_home = active_fixture['home']['id'] == manager['entry']
            opp_id = active_fixture['away']['id'] if is_home else active_fixture['home']['id']
            
            # ပြိုင်ဘက်၏ Net Point ကို တွက်ချက်သည်
            opp_net = get_net_points(opp_id, CURRENT_GW)
            
            if net_points > opp_net: wins, h2h_pts = 1, 3
            elif net_points == opp_net: draws, h2h_pts = 1, 1
            else: losses = 1

        # Tournament Table Update
        doc_ref = db.collection("tw_mm_tournament").document(entry_id)
        
        # Division Tag သတ်မှတ်ခြင်း
        tag = "B"
        if active_fixture and 'division' in active_fixture:
            div = str(active_fixture['division']).upper()
            if "A" in div or "1" in div: tag = "A"

        payload = {
            "fpl_id": manager['entry'],
            "manager_name": manager['player_name'],
            "team_name": manager['entry_name'],
            "played": firestore.Increment(played),
            "wins": firestore.Increment(wins),
            "draws": firestore.Increment(draws),
            "losses": firestore.Increment(losses),
            "h2h_points": firestore.Increment(h2h_pts),
            "gw_points": net_points, # Last GW Net
            "tournament_total_net_points": firestore.Increment(net_points),
            "league_tag": tag,
            "last_synced_gw": CURRENT_GW,
            "last_updated": firestore.SERVER_TIMESTAMP
        }
        
        batch.set(doc_ref, payload, merge=True)
        sync_logs.append({"id": entry_id, "pts": net_points})

    # Archive Fixtures (League & FA Playoff)
    archive_fixtures(sync_logs, fixtures_data)

    batch.commit()
    print(f"✅ GW {CURRENT_GW} Synced & Archived Successfully!")

def archive_fixtures(sync_logs, fixtures_data):
    for fid, f in fixtures_data.items():
        h_pts = next((l['pts'] for l in sync_logs if l['id'] == str(f['home']['id'])), 0)
        a_pts = next((l['pts'] for l in sync_logs if l['id'] == str(f['away']['id'])), 0)
        
        history_payload = {
            "fixture_id": fid,
            "gameweek": CURRENT_GW,
            "division": f.get('division', 'Mixed'),
            "type": f['type'],
            "home": {**f['home'], "points": h_pts},
            "away": {**f['away'], "points": a_pts},
            "status": "completed"
        }
        
        if f['type'] == 'league':
            db.collection(f"fixtures_history_gw_{CURRENT_GW}").document(fid).set(history_payload)
        elif f['type'] == 'fa_cup':
            # FA Cup Playoff အတွက် သီးသန့် archive
            db.collection("fixtures_history_fa").document(f"gw_{CURRENT_GW}_{fid}").set(history_payload)

if __name__ == "__main__":
    sync_tournament()
