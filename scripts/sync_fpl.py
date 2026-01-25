import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os

# ၁။ Firebase ကို ချိတ်ဆက်ရန် ပြင်ဆင်ခြင်း
def initialize_firebase():
    if not firebase_admin._apps:
        # serviceAccountKey.json ဖိုင်သည် scripts/ folder ထဲတွင် ရှိနေရမည်
        cred_path = os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json')
        try:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            print(f"Error: Firebase Key file missing or invalid. {e}")
            return None
    return firestore.client()

db = initialize_firebase()

# ၂။ Tournament Configuration (League A/B ၂၄ သင်းစီ၊ စုစုပေါင်း ၄၈ သင်း)
LEAGUE_ID = "400231"
FPL_API = "https://fantasy.premierleague.com/api/"
TOTAL_OFFICIALS = 48 

def sync_data():
    if not db:
        print("Firebase database connection failed.")
        return

    print("--- FPL Sync Process Started ---")
    
    # FPL API မှ Standings ကို ဆွဲယူခြင်း
    try:
        r = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/")
        r.raise_for_status()
        all_players = r.json()['standings']['results']
    except Exception as e:
        print(f"Error fetching data from FPL: {e}")
        return

    # အမှတ်အများဆုံးအတိုင်း Ranking စီခြင်း (Tie-break အတွက် Rank ကိုသုံးသည်)
    sorted_players = sorted(all_players, key=lambda x: (-x['total'], x['rank']))

    batch = db.batch()
    print(f"Syncing {len(sorted_players)} players to Firebase...")

    for idx, player in enumerate(sorted_players):
        entry_id = str(player['entry'])
        current_rank = idx + 1
        
        # Official Status & League Tagging Logic
        is_official = current_rank <= TOTAL_OFFICIALS
        
        league_tag = "General"
        playoff_seed = "Not Qualified"
        
        if is_official:
            # Rank 1-24 သည် League A၊ Rank 25-48 သည် League B
            league_tag = "A" if current_rank <= 24 else "B"
            
            # Playoff Seeding Logic (Top 16 က Bye ရမည်)
            if current_rank <= 16:
                playoff_seed = "Top 16 (Bye to Round of 32)"
            else:
                playoff_seed = f"Round 1 (Seed {current_rank})"

        # Firebase ထဲ သိမ်းမည့် Data ပုံစံ
        data = {
            "manager_name": player['player_name'],
            "team_name": player['entry_name'],
            "fpl_total_points": player['total'],
            "gw_points": player['event_total'],
            "overall_rank": player['rank'],
            "tournament_rank": current_rank,
            "is_official": is_official,
            "league_tag": league_tag,
            "playoff_seed": playoff_seed,
            "last_updated": firestore.SERVER_TIMESTAMP
        }

        # Document တစ်ခုချင်းစီအတွက် Batch ထဲထည့်ခြင်း
        doc_ref = db.collection("tw_mm_tournament").document(entry_id)
        batch.set(doc_ref, data, merge=True)

    # Database ထဲသို့ တစ်ပြိုင်နက် Update လုပ်ခြင်း
    try:
        batch.commit()
        print(f"--- Sync Success! {TOTAL_OFFICIALS} Officials Updated ---")
    except Exception as e:
        print(f"Error committing to Firebase: {e}")

# Script ကို စတင် Run သော နေရာ
if __name__ == "__main__":
    
    sync_data()
