import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import time

# ၁။ Firebase Initialize လုပ်ခြင်း
def initialize_firebase():
    if not firebase_admin._apps:
        service_account_info = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        if service_account_info:
            cred_dict = json.loads(service_account_info)
            cred = credentials.Certificate(cred_dict)
        else:
            # Local path အနေနဲ့ စစ်ဆေးခြင်း
            current_dir = os.path.dirname(os.path.abspath(__file__))
            cred_path = os.path.join(current_dir, 'serviceAccountKey.json')
            cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firebase()

# ၂။ Configuration
FPL_API = "https://fantasy.premierleague.com/api/"
LEAGUES = {
    "League_A": "151552",
    "League_B": "2892732"
}

def get_fpl_base_data():
    r = requests.get(f"{FPL_API}bootstrap-static/").json()
    players = {p['id']: p for p in r['elements']}
    teams = {t['id']: {'short': t['short_name'], 'full': t['name']} for t in r['teams']}
    pos_map = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}
    current_gw = next(e['id'] for e in r['events'] if e['is_current'])
    return players, teams, pos_map, current_gw

def sync_scouts():
    players_raw, teams_map, pos_map, gw = get_fpl_base_data()
    print(f"--- 🚀 Syncing Data for Gameweek {gw} ---")

    for league_name, l_id in LEAGUES.items():
        print(f"Processing {league_name}...")
        standings_url = f"{FPL_API}leagues-classic/{l_id}/standings/"
        standings_res = requests.get(standings_url).json()
        standings = standings_res['standings']['results']

        batch = db.batch()
        for team in standings:
            entry_id = str(team['entry'])
            picks_url = f"{FPL_API}entry/{entry_id}/event/{gw}/picks/"
            picks_res = requests.get(picks_url).json()
            
            lineup = []
            if 'picks' in picks_res:
                for p in picks_res['picks']:
                    p_id = p['element']
                    p_info = players_raw.get(p_id)
                    
                    # FPL API မှ တိုက်ရိုက်လာသော Boolean တန်ဖိုးကိုသာ ယူသည်
                    lineup.append({
                        "id": p_id,
                        "name": p_info['web_name'],
                        "pos": pos_map[p_info['element_type']],
                        "team": teams_map[p_info['team']]['short'],
                        "is_captain": p.get('is_captain', False),
                        "is_vice_captain": p.get('is_vice_captain', False),
                        "multiplier": p.get('multiplier', 1),
                        "points": p_info['event_points']
                    })

            data = {
                "entry_id": team['entry'],
                "manager": team['player_name'],
                "team_name": team['entry_name'],
                "gw_points": team['event_total'],
                "total_points": team['total'],
                "active_chip": picks_res.get('active_chip'),
                "transfer_cost": picks_res.get('entry_history', {}).get('event_transfers_cost', 0),
                "lineup": lineup,
                "last_updated": firestore.SERVER_TIMESTAMP
            }
            
            doc_ref = db.collection(f"scout_{league_name}").document(entry_id)
            # 🔥 merge=True ကို ဖယ်လိုက်ပါပြီ။ ဒါမှ Lineup အဟောင်းတွေ အကုန်ရှင်းသွားမှာပါ
            batch.set(doc_ref, data) 
            
        batch.commit()
        print(f"✅ {league_name} Data Updated.")

    # --- Player Scout Sync ---
    print("Fetching Player Stats...")
    top_scouts = sorted(players_raw.values(), key=lambda x: x['total_points'], reverse=True)[:100]
    
    s_batch = db.batch()
    for p in top_scouts:
        p_id = p['id']
        f_url = f"{FPL_API}element-summary/{p_id}/"
        f_res = requests.get(f_url).json()
        
        next_fixtures = []
        for f in f_res.get('fixtures', [])[:5]:
            is_home = f['is_home']
            opp_id = f['team_a'] if is_home else f['team_h']
            difficulty = f['difficulty']
            
            bg_color = "#375523" 
            if difficulty == 3: bg_color = "#e7d60d"
            if difficulty >= 4: bg_color = "#e9190c"
            
            next_fixtures.append({
                "opponent": teams_map[opp_id]['short'],
                "is_home": is_home,
                "difficulty": difficulty,
                "bg": bg_color,
                "text": "#000" if difficulty == 3 else "#fff"
            })

        s_ref = db.collection("scout_players").document(str(p_id))
        s_batch.set(s_ref, {
            "name": p['web_name'],
            "full_name": f"{p['first_name']} {p['second_name']}",
            "team": teams_map[p['team']]['short'],
            "team_full": teams_map[p['team']]['full'],
            "pos": pos_map[p['element_type']],
            "gw_points": p['event_points'],
            "form": p['form'],
            "price": p['now_cost'] / 10,
            "total_points": p['total_points'],
            "ownership": p['selected_by_percent'],
            "goals": p['goals_scored'],
            "assists": p['assists'],
            "clean_sheets": p['clean_sheets'],
            "bonus": p['bonus'],
            "xg": p['expected_goals'],
            "ict": p['ict_index'],
            "fixtures": next_fixtures,
            "last_updated": firestore.SERVER_TIMESTAMP
        }, merge=True)
        time.sleep(0.05)
        
    s_batch.commit()
    print("✨ Sync Process Completed Successfully!")

if __name__ == "__main__":
    sync_scouts()
