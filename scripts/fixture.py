import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os, json, random

def initialize_firebase():
    if not firebase_admin._apps:
        sa_info = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        if sa_info:
            cred = credentials.Certificate(json.loads(sa_info))
        else:
            cred = credentials.Certificate('serviceAccountKey.json')
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firebase()
LEAGUE_ID = "400231"
FPL_API = "https://fantasy.premierleague.com/api/"
START_GW = 23

def setup_tournament():
    print("🚀 Initializing Setup...")
    try:
        r = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/").json()
        top_48 = sorted(r['standings']['results'], key=lambda x: x['total'], reverse=True)[:48]
    except Exception as e:
        print(f"❌ Error: {e}"); return

    batch = db.batch()
    all_players = []

    for index, m in enumerate(top_48):
        entry_id = str(m['entry'])
        div = "Division A" if index < 24 else "Division B"
        p_data = {"id": entry_id, "name": m['player_name'], "team": m['entry_name']}
        all_players.append(p_data)
        
        batch.set(db.collection("tw_mm_tournament").document(entry_id), {
            **p_data, "division": div, "tournament_total_net_points": 0,
            "gw_live_points": 0, "last_synced_gw": START_GW - 1
        }, merge=True)

    # FA Cup Round 1 (GW 23)
    random.shuffle(all_players)
    for i in range(0, len(all_players), 2):
        h, a = all_players[i], all_players[i+1]
        batch.set(db.collection("fixtures").document(f"FA_GW{START_GW}_Match_{i//2 + 1}"), {
            "gameweek": START_GW, "type": "fa_cup", "home": {**h, "points": 0},
            "away": {**a, "points": 0}, "status": "upcoming", "tie_break_winner": None,
            "division": "FA_CUP"
        })
    batch.commit()
    print(f"✅ Setup Success for GW {START_GW}")

if __name__ == "__main__":
    setup_tournament()
