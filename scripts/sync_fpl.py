import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os

# ၁။ Firebase ကို ချိတ်ဆက်ရန် ပြင်ဆင်ခြင်း
def initialize_firebase():
    if not firebase_admin._apps:
        cred_path = os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json')
        try:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            print(f"Error: Firebase Key file missing or invalid. {e}")
            return None
    return firestore.client()

db = initialize_firebase()

# ၂။ Tournament Configuration
LEAGUE_ID = "400231"
FPL_API = "https://fantasy.premierleague.com/api/"
TOTAL_OFFICIALS = 48 
START_GW = 24  # Tournament စတင်မည့် Gameweek

def sync_data():
    if not db:
        print("Firebase database connection failed.")
        return

    print("--- FPL Sync & Fixture Generation Started ---")
    
    # FPL API မှ Standings ကို ဆွဲယူခြင်း
    try:
        r = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/")
        r.raise_for_status()
        all_players = r.json()['standings']['results']
    except Exception as e:
        print(f"Error fetching data from FPL: {e}")
        return

    # အမှတ်အများဆုံးအတိုင်း Ranking စီခြင်း
    sorted_players = sorted(all_players, key=lambda x: (-x['total'], x['rank']))

    batch = db.batch()
    official_list = [] # Fixtures ထုတ်ရန်အတွက် သိမ်းထားမည်

    for idx, player in enumerate(sorted_players):
        entry_id = str(player['entry'])
        current_rank = idx + 1
        is_official = current_rank <= TOTAL_OFFICIALS
        
        league_tag = "General"
        if is_official:
            league_tag = "A" if current_rank <= 24 else "B"

        data = {
            "fpl_id": player['entry'],
            "manager_name": player['player_name'],
            "team_name": player['entry_name'],
            "fpl_total_points": player['total'],
            "gw_points": player['event_total'],
            "tournament_rank": current_rank,
            "is_official": is_official,
            "league_tag": league_tag,
            "last_updated": firestore.SERVER_TIMESTAMP
        }

        if is_official:
            official_list.append(data)

        doc_ref = db.collection("tw_mm_tournament").document(entry_id)
        batch.set(doc_ref, data, merge=True)

    # ၃။ Fixtures Generation Logic (League & FA Cup)
    generate_fixtures(official_list)

    try:
        batch.commit()
        print(f"--- Sync Success! Data & Fixtures Updated ---")
    except Exception as e:
        print(f"Error committing to Firebase: {e}")

def generate_fixtures(players):
    """ Division 1, 2 နှင့် FA Cup ပွဲစဉ်များကို အလိုအလျောက် တည်ပေးခြင်း """
    div_a = [p for p in players if p['league_tag'] == 'A']
    div_b = [p for p in players if p['league_tag'] == 'B']
    
    # --- Division A H2H (12 Matches) ---
    for i in range(0, len(div_a), 2):
        p1, p2 = div_a[i], div_a[i+1]
        fix_id = f"gw{START_GW}_divA_m{i}"
        upload_fixture(fix_id, "league", "A", p1, p2)

    # --- Division B H2H (12 Matches) ---
    for i in range(0, len(div_b), 2):
        p1, p2 = div_b[i], div_b[i+1]
        fix_id = f"gw{START_GW}_divB_m{i}"
        upload_fixture(fix_id, "league", "B", p1, p2)

    # --- TW FA Cup Playoff (24 Matches - Div A vs Div B) ---
    # Div A No.1 vs Div B No.24 စသဖြင့် တွဲပေးခြင်း
    for i in range(24):
        p1 = div_a[i]
        p2 = div_b[23 - i]
        fix_id = f"gw{START_GW}_fa_m{i}"
        upload_fixture(fix_id, "fa_cup", "Mixed", p1, p2)

def upload_fixture(fix_id, match_type, div, p1, p2):
    """ Firebase ထဲသို့ ပွဲစဉ်ဒေတာ ပို့ပေးခြင်း """
    doc_ref = db.collection("fixtures").document(fix_id)
    doc_ref.set({
        "fixture_id": fix_id,
        "type": match_type,
        "division": div,
        "gameweek": START_GW,
        "home": {"name": p1['team_name'], "id": p1['fpl_id'], "manager": p1['manager_name']},
        "away": {"name": p2['team_name'], "id": p2['fpl_id'], "manager": p2['manager_name']},
        "status": "upcoming"
    }, merge=True)

if __name__ == "__main__":
    sync_data()
