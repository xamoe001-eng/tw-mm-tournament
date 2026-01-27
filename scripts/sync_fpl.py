import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os

# ၁။ Firebase ချိတ်ဆက်ခြင်း
def initialize_firebase():
    if not firebase_admin._apps:
        cred_path = os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json')
        if not os.path.exists(cred_path):
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
START_GW = 23 

def sync_data():
    if not db: return

    print(f"--- FPL Sync Process Started for GW {START_GW} ---")
    
    try:
        r = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/")
        r.raise_for_status()
        all_players = r.json()['standings']['results']
    except Exception as e:
        print(f"Error fetching data from FPL: {e}")
        return

    # အမှတ်အများဆုံးအလိုက် Ranking စီခြင်း
    sorted_players = sorted(all_players, key=lambda x: (-x['total'], x['rank']))

    # Fixtures ဖတ်ခြင်း
    fixtures_data = {}
    try:
        fixtures_ref = db.collection("fixtures").where("gameweek", "==", START_GW).stream()
        fixtures_data = {f.id: f.to_dict() for f in fixtures_ref}
    except Exception as e:
        print(f"Notice: Fixtures error. {e}")

    batch = db.batch()
    official_list = []

    for idx, player in enumerate(sorted_players):
        entry_id = str(player['entry'])
        current_rank = idx + 1
        is_official = current_rank <= TOTAL_OFFICIALS
        
        played, wins, draws, losses, h2h_points = 0, 0, 0, 0, 0
        fa_cup_status = "TBD"
        league_tag = "General"

        # Net Points တွက်ချက်ခြင်း (Event Total - Transfer Cost)
        # API မှာ transfer cost မပါလာခဲ့ရင် 0 လို့ ယူဆမည်
        transfer_cost = player.get('event_transfers_cost', 0)
        net_gw_points = player['event_total'] - transfer_cost

        if is_official:
            league_tag = "A" if current_rank <= 24 else "B"
            
            if fixtures_data:
                for fix_id, f in fixtures_data.items():
                    is_home = f['home']['id'] == player['entry']
                    is_away = f['away']['id'] == player['entry']
                    
                    if (is_home or is_away):
                        # ပြိုင်ဘက်ရဲ့ Data ကို ရှာပြီး Net Points တွက်ခြင်း
                        opp_id = f['away']['id'] if is_home else f['home']['id']
                        opp_player = next((p for p in all_players if p['entry'] == opp_id), None)
                        
                        opp_net_score = 0
                        if opp_player:
                            opp_net_score = opp_player['event_total'] - opp_player.get('event_transfers_cost', 0)

                        # H2H League Logic
                        if f['type'] == 'league':
                            played = 1
                            if net_gw_points > opp_net_score:
                                wins, h2h_points = 1, 3
                            elif net_gw_points == opp_net_score:
                                draws, h2h_points = 1, 1
                            else:
                                losses = 1

                        # FA Cup Logic
                        if f['type'] == 'fa_cup':
                            if net_gw_points > opp_net_score:
                                fa_cup_status = "Qualified"
                            elif net_gw_points < opp_net_score:
                                fa_cup_status = "Eliminated"
                            else:
                                # အမှတ်တူနေရင် Overall Rank ပိုကောင်းတဲ့သူကို ပေးနိုင်သည် (သို့မဟုတ် TBD ထားနိုင်သည်)
                                fa_cup_status = "Draw (Replay/Rank)"

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
            "gw_points": net_gw_points, # -4 နှုတ်ပြီးသားရမှတ်ကို သိမ်းမည်
            "transfer_cost": transfer_cost,
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

    if official_list:
        generate_fixtures(official_list)

    try:
        batch.commit()
        print(f"--- Sync Success for GW {START_GW} (Transfer Costs Deducted)! ---")
    except Exception as e:
        print(f"Batch Error: {e}")

def generate_fixtures(players):
    div_a = [p for p in players if p['league_tag'] == 'A']
    div_b = [p for p in players if p['league_tag'] == 'B']
    
    for i in range(0, len(div_a), 2):
        if i+1 < len(div_a):
            upload_fixture(f"gw{START_GW}_divA_m{i}", "league", "A", div_a[i], div_a[i+1])
    
    for i in range(0, len(div_b), 2):
        if i+1 < len(div_b):
            upload_fixture(f"gw{START_GW}_divB_m{i}", "league", "B", div_b[i], div_b[i+1])

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

def sync_sc():
    print("Scout data sync process initiated...")

if __name__ == "__main__":
    sync_data()
    
