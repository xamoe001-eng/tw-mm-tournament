import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os

# ၁။ Firebase ချိတ်ဆက်ခြင်း
def initialize_firebase():
    if not firebase_admin._apps:
        # လမ်းကြောင်းကို GitHub Actions ရော Local ပါ အဆင်ပြေအောင် ချိန်ထားသည်
        cred_path = os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json')
        if not os.path.exists(cred_path):
            # scripts folder ထဲမှာ မရှိရင် root folder မှာ ရှာမည်
            cred_path = 'serviceAccountKey.json'
            
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
START_GW = 23  # ပြိုင်ပွဲစတင်သည့် GW (အစမ်းစစ်ရန် ၂၃ ထားသည်)

def sync_data():
    if not db: return

    print(f"--- FPL Sync Process Started for GW {START_GW} ---")
    
    # FPL API မှ Standings ဆွဲယူခြင်း
    try:
        r = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/")
        r.raise_for_status()
        all_players = r.json()['standings']['results']
    except Exception as e:
        print(f"Error fetching data from FPL: {e}")
        return

    # အမှတ်အများဆုံးအလိုက် Ranking အရင်စီခြင်း
    sorted_players = sorted(all_players, key=lambda x: (-x['total'], x['rank']))

    # လက်ရှိ Fixtures များကို Database မှ ပြန်ဖတ်ခြင်း
    fixtures_data = {}
    try:
        fixtures_ref = db.collection("fixtures").where("gameweek", "==", START_GW).stream()
        fixtures_data = {f.id: f.to_dict() for f in fixtures_ref}
    except Exception as e:
        print(f"Notice: Fixtures collection not found or error. {e}")

    batch = db.batch()
    official_list = []

    for idx, player in enumerate(sorted_players):
        entry_id = str(player['entry'])
        current_rank = idx + 1
        is_official = current_rank <= TOTAL_OFFICIALS
        
        # Default Values
        played, wins, draws, losses, h2h_points = 0, 0, 0, 0, 0
        fa_cup_status = "TBD"
        league_tag = "General"

        if is_official:
            league_tag = "A" if current_rank <= 24 else "B"
            
            # Fixtures ရှိမှသာ H2H Logic ကို တွက်မည်
            if fixtures_data:
                for fix_id, f in fixtures_data.items():
                    is_home = f['home']['id'] == player['entry']
                    is_away = f['away']['id'] == player['entry']
                    
                    if (is_home or is_away) and f['type'] == 'league':
                        played = 1
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

                    if (is_home or is_away) and f['type'] == 'fa_cup':
                        home_score = next((p['event_total'] for p in all_players if p['entry'] == f['home']['id']), 0)
                        away_score = next((p['event_total'] for p in all_players if p['entry'] == f['away']['id']), 0)
                        
                        if (is_home and home_score > away_score) or (is_away and away_score > home_score):
                            fa_cup_status = "Qualified"
                        else:
                            fa_cup_status = "Eliminated"

        data = {
            "fpl_id": player['entry'],
            "manager_name": player['player_name'],
            "team_name": player['entry_name'],
            "played": played,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "h2h_points": h2h_points,
            "fpl_total_points": player['total'],
            "gw_points": player['event_total'],
            "tournament_rank": current_rank,
            "is_official": is_official,
            "league_tag": league_tag,
            "fa_cup_status": fa_cup_status,
            "last_updated": firestore.SERVER_TIMESTAMP
        }

        if is_official:
            official_list.append(data)
        
        doc_ref = db.collection("tw_mm_tournament").document(entry_id)
        batch.set(doc_ref, data, merge=True)

    # ၃။ Fixtures Generation
    if official_list:
        generate_fixtures(official_list)

    try:
        batch.commit()
        print(f"--- Sync Success for GW {START_GW}! ---")
    except Exception as e:
        print(f"Batch Error: {e}")

def generate_fixtures(players):
    div_a = [p for p in players if p['league_tag'] == 'A']
    div_b = [p for p in players if p['league_tag'] == 'B']
    
    # Division A
    for i in range(0, len(div_a), 2):
        if i+1 < len(div_a):
            upload_fixture(f"gw{START_GW}_divA_m{i}", "league", "A", div_a[i], div_a[i+1])
    
    # Division B
    for i in range(0, len(div_b), 2):
        if i+1 < len(div_b):
            upload_fixture(f"gw{START_GW}_divB_m{i}", "league", "B", div_b[i], div_b[i+1])

    # FA Cup (Top A vs Bottom B logic)
    for i in range(min(len(div_a), len(div_b))):
        upload_fixture(f"gw{START_GW}_fa_m{i}", "fa_cup", "Mixed", div_a[i], div_b[len(div_b)-1-i])

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

# အရေးကြီးသည်- Workflow ထဲက NameError ကို ပြင်ရန်
def sync_sc():
    """ ဤ function နာမည်သည် workflow ထဲတွင် ခေါ်ထားသော နာမည်ဖြစ်ရမည် """
    print("Scout data sync process initiated...")
    # Scout logic များကို ဤနေရာတွင် ထည့်ပါ သို့မဟုတ် အခြား file သို့ ညွှန်းပါ

if __name__ == "__main__":
    sync_data()
