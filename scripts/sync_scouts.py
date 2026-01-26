import requests
import json
import os

# FPL API URL
LEAGUE_ID = "400231"
FPL_API = f"https://fantasy.premierleague.com/api/leagues-classic/{LEAGUE_ID}/standings/"

# Scout အဖြစ် သတ်မှတ်ချင်သော Manager များ၏ Entry ID စာရင်း
# (မိတ်ဆွေ စောင့်ကြည့်ချင်တဲ့ ID အမှန်တွေကို ဒီနေရာမှာ အစားထိုးပါ)
SCOUT_IDS = [123456, 789012, 345678] 

def sync_scouts():
    print("--- Fetching Scout Data from FPL ---")
    try:
        r = requests.get(FPL_API)
        r.raise_for_status()
        all_players = r.json()['standings']['results']
        
        scout_list = []
        
        # အမှတ်အများဆုံးအတိုင်း Ranking အရင်စီမည်
        sorted_players = sorted(all_players, key=lambda x: (-x['total'], x['rank']))

        for idx, player in enumerate(sorted_players):
            entry_id = player['entry']
            
            # သတ်မှတ်ထားသော Scout ID များဖြစ်ပါက စာရင်းထဲထည့်မည်
            if entry_id in SCOUT_IDS:
                scout_list.append({
                    "fpl_id": entry_id,
                    "team_name": player['entry_name'],
                    "manager_name": player['player_name'],
                    "fpl_total_points": player['total'],
                    "gw_points": player['event_total'],
                    "tournament_rank": idx + 1,
                    "is_scout": True
                })

        # Root Folder ထဲသို့ scout_data.json သိမ်းဆည်းခြင်း
        # GitHub Actions မှာ error မတက်အောင် လမ်းကြောင်းကို သေချာချိန်ထားပါသည်
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(current_dir, '../scout_data.json')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(scout_list, f, indent=4, ensure_ascii=False)
            
        print(f"--- Success! {len(scout_list)} Scouts saved to scout_data.json ---")

    except Exception as e:
        print(f"Error logic fail: {e}")

if __name__ == "__main__":
    # ပျက်နေသော function call ကို ပြန်ပြင်ထားပါသည်
    sync_scouts()
