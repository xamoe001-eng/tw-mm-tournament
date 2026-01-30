import requests
import firebase_admin
from firebase_admin import credentials, firestore
import random

def initialize_firebase():
    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.Certificate('serviceAccountKey.json'))
    return firestore.client()

db = initialize_firebase()
LEAGUE_ID = "400231"
FPL_API = "https://fantasy.premierleague.com/api/"
START_GW = 23

def setup_tournament():
    print("🚀 Initializing Tournament Setup...")
    r = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/").json()
    top_48 = sorted(r['standings']['results'], key=lambda x: x['total'], reverse=True)[:48]

    batch = db.batch()
    all_players = []

    # ၁။ League Table & Divisions ဆောက်ခြင်း
    for index, m in enumerate(top_48):
        entry_id = str(m['entry'])
        div = "Division A" if index < 24 else "Division B"
        player_data = {"id": entry_id, "name": m['player_name'], "team": m['entry_name']}
        all_players.append(player_data)
        
        doc_ref = db.collection("tw_mm_tournament").document(entry_id)
        batch.set(doc_ref, {
            **player_data,
            "division": div,
            "tournament_total_net_points": 0,
            "gw_live_points": 0,
            "last_synced_gw": START_GW - 1
        }, merge=True)

    # ၂။ FA Cup Round 1 (GW 23) အတွက် တွဲဆိုင်းထုတ်ခြင်း
    random.shuffle(all_players)
    for i in range(0, len(all_players), 2):
        h, a = all_players[i], all_players[i+1]
        fa_id = f"FA_GW{START_GW}_Match_{i//2 + 1}"
        batch.set(db.collection("fixtures").document(fa_id), {
            "gameweek": START_GW,
            "type": "fa_cup",
            "home": {**h, "points": 0},
            "away": {**a, "points": 0},
            "status": "upcoming",
            "tie_break_winner": None
        })

    batch.commit()
    print(f"✅ Setup Complete: Managers mapped and FA Cup Round 1 (GW {START_GW}) created.")

if __name__ == "__main__":
    setup_tournament()
