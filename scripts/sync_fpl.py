import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os

# ၁။ Firebase ချိတ်ဆက်ခြင်း
def initialize_firebase():
    if not firebase_admin._apps:
        cred_path = os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json')
        try:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            print(f"Error: Firebase Key file missing. {e}")
            return None
    return firestore.client()

db = initialize_firebase()

# ၂။ Tournament Configuration
LEAGUE_ID = "400231"
FPL_API = "https://fantasy.premierleague.com/api/"
TOTAL_OFFICIALS = 48 
START_GW = 24  # ပြိုင်ပွဲစတင်သည့် GW

def sync_data():
    if not db: return

    print("--- FPL Sync & H2H Logic Process Started ---")
    
    # FPL API မှ Standings ဆွဲယူခြင်း
    try:
        r = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/")
        r.raise_for_status()
        all_players = r.json()['standings']['results']
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    # အမှတ်အများဆုံးအလိုက် Ranking အရင်စီခြင်း
    sorted_players = sorted(all_players, key=lambda x: (-x['total'], x['rank']))

    # လက်ရှိ Fixtures များကို Database မှ ပြန်ဖတ်ခြင်း (ရလဒ်တွက်ရန်)
    # မှတ်ချက် - GW အမှတ်တွေထွက်လာမှ နိုင်/ရှုံး တိကျမှာဖြစ်ပါတယ်
    fixtures_ref = db.collection("fixtures").where("gameweek", "==", START_GW).stream()
    fixtures_data = {f.id: f.to_dict() for f in fixtures_ref}

    batch = db.batch()
    official_list = []

    for idx, player in enumerate(sorted_players):
        entry_id = str(player['entry'])
        current_rank = idx + 1
        is_official = current_rank <= TOTAL_OFFICIALS
        
        # Default Values
        played = 0
        wins = 0
        draws = 0
        losses = 0
        h2h_points = 0
        fa_cup_status = "TBD" # To Be Decided

        if is_official:
            league_tag = "A" if current_rank <= 24 else "B"
            
            # ⚽ H2H Logic: Fixtures ထဲက အမှတ်တွေကို နှိုင်းယှဉ်ပြီး W/D/L တွက်ခြင်း
            # (လက်ရှိ GW အတွက် ရလဒ်ကို Fixtures collection ထဲကနေ လှမ်းစစ်တာပါ)
            for fix_id, f in fixtures_data.items():
                is_home = f['home']['id'] == player['entry']
                is_away = f['away']['id'] == player['entry']
                
                if (is_home or is_away) and f['type'] == 'league':
                    played = 1 # လက်ရှိ GW တစ်ပတ်စာတွက်ချက်မှု
                    # ဤနေရာတွင် Live GW Points များကို နှိုင်းယှဉ်ရန်-
                    # (ရိုးရှင်းစေရန် p['event_total'] ကို သုံးထားပါသည်)
                    home_score = next((p['event_total'] for p in all_players if p['entry'] == f['home']['id']), 0)
                    away_score = next((p['event_total'] for p in all_players if p['entry'] == f['away']['id']), 0)

                    if is_home:
                        if home_score > away_score: wins, h2h_points = 1, 3
                        elif home_score == away_score: draws, h2h_points = 1, 1
                        else: losses = 1
                    else:
                        if away_score > home_score: wins, h2h_points = 1, 3
                        elif away_score == home_score: draws, h2h_points = 1, 1
                        else: losses = 1

                # 🏆 FA Cup Status
                if (is_home or is_away) and f['type'] == 'fa_cup':
                    home_score = next((p['event_total'] for p in all_players if p['entry'] == f['home']['id']), 0)
                    away_score = next((p['event_total'] for p in all_players if p['entry'] == f['away']['id']), 0)
                    
                    if (is_home and home_score > away_score) or (is_away and away_score > home_score):
                        fa_cup_status = "Qualified"
                    else:
                        fa_cup_status = "Eliminated"

        else:
            league_tag = "General"

        data = {
            "fpl_id": player['entry'],
            "manager_name": player['player_name'],
            "team_name": player['entry_name'],
            "played": played,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "h2h_points": h2h_points, # Table စီရန် အဓိကမှတ်
            "fpl_total_points": player['total'],
            "gw_points": player['event_total'],
            "tournament_rank": current_rank,
            "is_official": is_official,
            "league_tag": league_tag,
            "fa_cup_status": fa_cup_status,
            "last_updated": firestore.SERVER_TIMESTAMP
        }

        if is_official: official_list.append(data)
        doc_ref = db.collection("tw_mm_tournament").document(entry_id)
        batch.set(doc_ref, data, merge=True)

    # ၃။ ပွဲစဉ်ဇယားများ အသစ်ထုတ်ခြင်း/Update လုပ်ခြင်း
    generate_fixtures(official_list)

    try:
        batch.commit()
        print("--- Sync Success! Table & Fixtures Updated ---")
    except Exception as e:
        print(f"Batch Error: {e}")

def generate_fixtures(players):
    div_a = [p for p in players if p['league_tag'] == 'A']
    div_b = [p for p in players if p['league_tag'] == 'B']
    
    # Division A matches
    for i in range(0, len(div_a), 2):
        upload_fixture(f"gw{START_GW}_divA_m{i}", "league", "A", div_a[i], div_a[i+1])
    
    # Division B matches
    for i in range(0, len(div_b), 2):
        upload_fixture(f"gw{START_GW}_divB_m{i}", "league", "B", div_b[i], div_b[i+1])

    # FA Cup matches (Div A vs Div B)
    for i in range(24):
        upload_fixture(f"gw{START_GW}_fa_m{i}", "fa_cup", "Mixed", div_a[i], div_b[23-i])

def upload_fixture(fix_id, match_type, div, p1, p2):
    db.collection("fixtures").document(fix_id).set({
        "fixture_id": fix_id,
        "type": match_type,
        "division": div,
        "gameweek": START_GW,
        "home": {"name": p1['team_name'], "id": p1['fpl_id'], "manager": p1['manager_name']},
        "away": {"name": p2['team_name'], "id": p2['fpl_id'], "manager": p2['manager_name']},
        "status": "active"
    }, merge=True)

if __name__ == "__main__":
    sync_data()
