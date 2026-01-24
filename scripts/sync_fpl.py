import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os

def initialize_firebase():
    if not firebase_admin._apps:
        cred_path = os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json')
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firebase()

LEAGUE_ID = "400231"
FPL_API = "https://fantasy.premierleague.com/api/"

# --- OFFICIAL MANAGERS LIST ---
# ဒီနေရာမှာ TW MM က သတ်မှတ်ထားတဲ့ Manager ၅၀ ရဲ့ Entry ID (Team ID) တွေကို ထည့်ပါ
# ဥပမာ - [123, 456, 789]
OFFICIAL_IDS = [12345, 67890] # မိတ်ဆွေဆီက list ရရင် ဒီမှာ အစားထိုးပါ

def sync_data():
    print("Fetching data from FPL...")
    r = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/")
    standings = r.json()['standings']['results']

    batch = db.batch()

    for idx, player in enumerate(standings):
        entry_id = str(player['entry'])
        
        # Official ဟုတ်မဟုတ် စစ်ဆေးခြင်း
        is_official = player['entry'] in OFFICIAL_IDS
        
        # Official ဆိုရင် Ranking အလိုက် League A/B ခွဲမယ်
        # Official မဟုတ်ရင် General လို့ပဲ သတ်မှတ်မယ်
        league_tag = "General"
        if is_official:
            # ၅၀ ထဲကမှ အဆင့် ၁-၂၅ ကို A၊ ၂၆-၅၀ ကို B ပေးမယ်
            # (မှတ်ချက်- standings ထဲမှာ official တွေချည်းပဲ rank ပြန်စီဖို့ လိုနိုင်ပါတယ်)
            league_tag = "A" if idx < 25 else "B" 

        data = {
            "manager_name": player['player_name'],
            "team_name": player['entry_name'],
            "fpl_points": player['total'],
            "gw_points": player['event_total'],
            "rank": player['rank'], # Private League ထဲက rank အစစ်
            "is_official": is_official,
            "league_tag": league_tag,
            "last_updated": firestore.SERVER_TIMESTAMP
        }

        doc_ref = db.collection("tw_mm_tournament").document(entry_id)
        batch.set(doc_ref, data)

    batch.commit()
    print(f"Successfully synced {len(standings)} players to Firebase!")

if __name__ == "__main__":
    s
    ync_data()
