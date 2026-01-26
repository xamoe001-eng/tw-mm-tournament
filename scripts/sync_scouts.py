import requests
import json
import os

# FPL API URL
FPL_API = "https://fantasy.premierleague.com/api/leagues-classic/400231/standings/"

# Scout အဖြစ် သတ်မှတ်ချင်သော Manager များ၏ Entry ID စာရင်း (ဒီမှာ ID တွေထည့်ပါ)
SCOUT_IDS = [123456, 789012, 345678] 

def sync_scouts():
    print("--- Fetching Scout Data from FPL ---")
    try:
        r = requests.get(FPL_API)
        r.raise_for_status()
        all_players = r.json()['standings']['results']
        
        scout_list = []
        
        # အမှတ်အလိုက် Rank အရင်စီမယ်
        sorted_players = sorted(all_players, key=lambda x: (-x['total'], x['rank']))

        for idx, player in enumerate(sorted_players):
            entry_id = player['entry']
            
            # ငါတို့သတ်မှတ်ထားတဲ့ ID စာရင်းထဲမှာ ပါသလား စစ်မယ်
            if entry_id in SCOUT_IDS:
                scout_list.append({
                    "team_name": player['entry_name'],
                    "manager_name": player['player_name'],
                    "fpl_total_points": player['total'],
                    "tournament_rank": idx + 1,
                    "is_scout": True
                })

        # JSON ဖိုင်အဖြစ် သိမ်းမယ် (Root Folder ထဲရောက်အောင် ../ နဲ့ သိမ်းပါ)
        output_path = os.path.join(os.path.dirname(__file__), '../scout_data.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(scout_list, f, indent=4)
            
        print(f"--- Success! {len(scout_list)} Scouts saved to scout_data.json ---")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    sync_sc
  outs()
