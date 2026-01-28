import firebase_admin
from firebase_admin import credentials, firestore
import random
import os
import json

# ၁။ Firebase ချိတ်ဆက်ခြင်း
def initialize_firebase():
    if not firebase_admin._apps:
        service_account_info = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        if service_account_info:
            cred = credentials.Certificate(json.loads(service_account_info))
        else:
            cred = credentials.Certificate('serviceAccountKey.json')
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firebase()

def generate_fixtures():
    # START_GW ကို သတ်မှတ်ခြင်း (မိတ်ဆွေရဲ့ ပထမဆုံး GW)
    start_gw = 23 
    
    # ပွဲစဉ်တွေ ရှိပြီးသားလား အရင်စစ်ဆေးမည် (Duplicate မဖြစ်အောင်)
    # GW 23 ပွဲစဉ်တစ်ခုခု ရှိနေရင် generate မလုပ်တော့ဘဲ ကျော်သွားမယ်
    check_fixtures = db.collection("fixtures").where("gameweek", "==", start_gw).limit(1).get()
    if len(check_fixtures) > 0:
        print(f"⚠️ Fixtures for GW {start_gw} already exist. Skipping generation.")
        return

    print(f"--- 🛠️ Initializing Fixtures (7 Weeks League + FA Round 1) ---")
    
    # ၂။ Tournament ထဲက Player ၄၈ ယောက်လုံးကို ဆွဲထုတ်ခြင်း
    players_ref = db.collection("tw_mm_tournament").stream()
    all_players = []
    for p in players_ref:
        data = p.to_dict()
        all_players.append({
            "id": data['fpl_id'], 
            "name": data['manager_name'],
            "team": data['team_name'], 
            "tag": data.get('league_tag', 'B')
        })

    if not all_players:
        print("❌ No players found in database!")
        return

    div_a = [p for p in all_players if p['tag'] == 'A']
    div_b = [p for p in all_players if p['tag'] == 'B']
    
    total_weeks = 7
    batch = db.batch()

    # ၃။ League Round Robin Logic (7 Weeks)
    def create_league_schedule(player_list, division_name):
        n = len(player_list)
        if n < 2: return
        
        pool = list(player_list)
        for week in range(total_weeks):
            current_gw = start_gw + week
            for i in range(n // 2):
                h, a = pool[i], pool[n-1-i]
                f_ref = db.collection("fixtures").document(f"GW{current_gw}_{division_name}_P{i+1}")
                batch.set(f_ref, {
                    "gameweek": current_gw, 
                    "division": division_name, 
                    "type": "league",
                    "home": h, 
                    "away": a, 
                    "status": "upcoming"
                })
            # Round Robin Rotation
            pool = [pool[0]] + [pool[-1]] + pool[1:-1]

    # ၄။ FA Cup Round 1 (၄၈ သင်း Playoff အဖွင့်)
    random.shuffle(all_players)
    for i in range(0, len(all_players), 2):
        if i+1 < len(all_players):
            h, a = all_players[i], all_players[i+1]
            f_ref = db.collection("fixtures").document(f"GW{start_gw}_FA_R1_P{i//2 + 1}")
            batch.set(f_ref, {
                "gameweek": start_gw, 
                "division": "FA_CUP", 
                "type": "fa_cup",
                "home": h, 
                "away": a, 
                "status": "upcoming", 
                "stage": "Round of 48"
            })

    # Firestore သို့ အချက်အလက်များ သွင်းခြင်း
    batch.commit()
    print("✅ League & FA R1 Setup Complete and Synced to Firestore!")

if __name__ == "__main__":
    generate_fixtures()
