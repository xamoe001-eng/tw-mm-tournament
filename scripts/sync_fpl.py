import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os

# 1. Firebase Setup (GitHub Secrets ကနေ သော့ယူဖို့ ပြင်ဆင်ထားပါတယ်)
def initialize_firebase():
    if not firebase_admin._apps:
        # GitHub မှာ 'serviceAccountKey.json' ကို scripts folder ထဲ တင်ထားရပါမယ်
        # (သတိ - လုံခြုံရေးအတွက် .gitignore မှာ ထည့်ထားဖို့ လိုပါမယ်)
        cred_path = os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json')
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firebase()

# 2. Tournament Config
LEAGUE_ID = "400231"
FPL_API = "https://fantasy.premierleague.com/api/"

def sync_data():
    print("Fetching data from FPL...")
    # League Standings ယူခြင်း
    r = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/")
    standings = r.json()['standings']['results']

    # Bootstrap Static (Team Names/Jersey Codes အတွက်)
    static_r = requests.get(f"{FPL_API}bootstrap-static/").json()
    teams = {t['id']: t['code'] for t in static_r['teams']}
    elements = {e['id']: e['team'] for e in static_r['elements']}

    batch = db.batch()

    for idx, player in enumerate(standings):
        entry_id = str(player['entry'])
        
        # Player ရဲ့ အသင်း Jersey Code ကို ခန့်မှန်းတွက်ချက်ခြင်း
        # (ရိုးရှင်းအောင် ပထမဆုံး player ရဲ့ team ကို ယူပါမယ်)
        # အသေးစိတ် picks ယူချင်ရင် entry/{id}/event/{gw}/picks/ ကို ထပ်ခေါ်ရပါမယ်
        
        data = {
            "manager_name": player['player_name'],
            "team_name": player['entry_name'],
            "fpl_points": player['total'],
            "gw_points": player['event_total'],
            "rank": player['rank'],
            "league_tag": "A" if idx < 25 else "B", # ၂၅ ယောက်စီ ခွဲခြင်း
            "last_updated": firestore.SERVER_TIMESTAMP
        }

        doc_ref = db.collection("tw_mm_tournament").document(entry_id)
        batch.set(doc_ref, data)

    batch.commit()
    print(f"Successfully synced {len(standings)} players to Firebase!")

if __name__ == "__main__":
    sy
  nc_data()
