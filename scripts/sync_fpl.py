import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os

def initialize_firebase():
    if not firebase_admin._apps:
        # serviceAccountKey.json ကို scripts/ folder ထဲမှာ တင်ထားဖို့ လိုပါမယ်
        cred_path = os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json')
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firebase()
LEAGUE_ID = "400231"
FPL_API = "https://fantasy.premierleague.com/api/"

def sync_data():
    print("Fetching data from FPL...")
    r = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/")
    all_players = r.json()['standings']['results']

    # အမှတ်အများဆုံး ၅၀ ကို Ranking စီခြင်း
    sorted_players = sorted(all_players, key=lambda x: (-x['total'], x['rank']))

    batch = db.batch()
    for idx, player in enumerate(sorted_players):
        entry_id = str(player['entry'])
        
        # ထိပ်ဆုံး ၅၀ ကို Official (A/B) ခွဲခြားခြင်း
        is_official = idx < 50
        league_tag = "General"
        if is_official:
            league_tag = "A" if idx < 25 else "B"

        data = {
            "manager_name": player['player_name'],
            "team_name": player['entry_name'],
            "fpl_points": player['total'],
            "gw_points": player['event_total'],
            "is_official": is_official,
            "league_tag": league_tag,
            "rank": idx + 1,
            "last_updated": firestore.SERVER_TIMESTAMP
        }

        doc_ref = db.collection("tw_mm_tournament").document(entry_id)
        batch.set(doc_ref, data)

    batch.commit()
    print("Sync Complete!")

if __name__ == "__main__":
    syn
    c_data()
