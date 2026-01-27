import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

# ၁။ Firebase Initialize လုပ်ခြင်း
def initialize_firebase():
    if not firebase_admin._apps:
        # GitHub Actions (Secret) သို့မဟုတ် Local (JSON file) မှ Key ကို ဖတ်ခြင်း
        service_account_info = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        if service_account_info:
            cred_dict = json.loads(service_account_info)
            cred = credentials.Certificate(cred_dict)
        else:
            # Local မှာ စမ်းသပ်ရန်အတွက် path ကို သင့် JSON file နာမည်အတိုင်း ပြင်ပါ
            cred = credentials.Certificate('scripts/serviceAccountKey.json')
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firebase()

# ၂။ Configuration
FPL_API = "https://fantasy.premierleague.com/api/"
LEAGUES = {
    "League_A": "151552",  # League A ID
    "League_B": "2892732"   # League B ID
}

def get_fpl_base_data():
    """ FPL ရဲ့ အခြေခံ Player Data နဲ့ အသေးစိတ် Stats များ ရယူခြင်း """
    r = requests.get(f"{FPL_API}bootstrap-static/").json()
    players = {p['id']: p for p in r['elements']}
    # Team နာမည်အတိုနှင့် အရှည် နှစ်မျိုးလုံး သိမ်းရန်
    teams = {t['id']: {'short': t['short_name'], 'full': t['name']} for t in r['teams']}
    pos_map = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}
    current_gw = next(e['id'] for e in r['events'] if e['is_current'])
    return players, teams, pos_map, current_gw

def sync_scouts():
    players_raw, teams_map, pos_map, gw = get_fpl_base_data()
    print(f"--- Syncing Data for Gameweek {gw} ---")

    # --- မန်နေဂျာများ၏ အသင်း (Lineup) နှင့် Chips/Hits ကို Sync လုပ်ခြင်း ---
    for league_name, l_id in LEAGUES.items():
        print(f"Processing {league_name}...")
        standings_url = f"{FPL_API}leagues-classic/{l_id}/standings/"
        standings = requests.get(standings_url).json()['standings']['results']

        batch = db.batch()
        
        for team in standings:
            entry_id = str(team['entry'])
            # Team တစ်ခုချင်းစီရဲ့ Picks (Lineup) နဲ့ Chips/Hits ကို ယူခြင်း
            picks_url = f"{FPL_API}entry/{entry_id}/event/{gw}/picks/"
            picks_res = requests.get(picks_url).json()
            
            lineup = []
            if 'picks' in picks_res:
                for p in picks_res['picks']:
                    p_id = p['element']
                    p_info = players_raw.get(p_id)
                    lineup.append({
                        "id": p_id,
                        "name": p_info['web_name'],
                        "pos": pos_map[p_info['element_type']],
                        "team": teams_map[p_info['team']]['short'],
                        "is_captain": p['is_captain'],
                        "is_vice_captain": p['is_vice_captain'],
                        "multiplier": p['multiplier'],
                        "points": p_info['event_points'],
                        "order": p['position']
                    })

            # Firebase သို့ ပို့မည့် Team Data (Chips နဲ့ Hit -4 ပါဝင်သည်)
            data = {
                "entry_id": team['entry'],
                "manager": team['player_name'],
                "team_name": team['entry_name'],
                "gw_points": team['event_total'],
                "total_points": team['total'],
                "rank": team['rank'],
                "active_chip": picks_res.get('active_chip'), # Chip သုံးထားခြင်းရှိမရှိ
                "transfer_cost": picks_res.get('entry_history', {}).get('event_transfers_cost', 0), # Transfer Hit (-4/-8)
                "lineup": lineup,
                "last_updated": firestore.SERVER_TIMESTAMP
            }

            doc_ref = db.collection(f"scout_{league_name}").document(entry_id)
            batch.set(doc_ref, data, merge=True)

        batch.commit()
        print(f"Done syncing {league_name}")

    # --- ၃။ Player Scout အပိုင်း (ပုံ ၄ ပါ Advanced Stats များ အကုန်ပါသည်) ---
    # Total Points အလိုက် ကစားသမား ၁၀၀ ကို စုစည်းခြင်း
    top_scouts = sorted(players_raw.values(), key=lambda x: x['total_points'], reverse=True)[:100]
    
    s_batch = db.batch()
    for p in top_scouts:
        s_ref = db.collection("scout_players").document(str(p['id']))
        
        # ပုံ ၃ နှင့် ၄ ပါ အချက်အလက်များ အားလုံး စုစည်းခြင်း
        s_batch.set(s_ref, {
            "name": p['web_name'],
            "full_name": f"{p['first_name']} {p['second_name']}",
            "team": teams_map[p['team']]['short'],
            "team_full": teams_map[p['team']]['full'],
            "pos": pos_map[p['element_type']],
            "form": p['form'], # GW Points အဖြစ် သုံးနိုင်သည်
            "price": p['now_cost'] / 10,
            "total_points": p['total_points'],
            "ownership": p['selected_by_percent'], # OWN%
            
            # Advanced Stats (ပုံ ၄ ပါ Player Detail Card အတွက်)
            "goals": p['goals_scored'],
            "assists": p['assists'],
            "clean_sheets": p['clean_sheets'], # CS
            "bonus": p['bonus'], # Bonus
            "xg": p['expected_goals'], # xG
            "ict": p['ict_index'], # ICT Index
            "status": p['status'],
            
            "last_updated": firestore.SERVER_TIMESTAMP
        }, merge=True)
        
    s_batch.commit()
    print("✅ Advanced Sync Completed with Chips & Hits!")

if __name__ == "__main__":
    sync_scouts() # Indentation မှန်ကန်စွာ 
ပြင်ဆင်ပြီး
