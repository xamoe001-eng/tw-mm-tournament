import firebase_admin
from firebase_admin import credentials, firestore
import random
import os
import json

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
    # ၁။ စစ်ဆေးခြင်း- Fixtures တွေ ရှိပြီးသားလား?
    # GW 23 ပွဲစဉ် တစ်ခုခု ရှိနေရင် ထပ်မလုပ်တော့ဘဲ ရပ်လိုက်မယ်
    docs = db.collection("fixtures").where("gameweek", "==", 23).limit(1).get()
    if len(docs) > 0:
        print("⚠️ Fixtures already exist in Firestore. Generation skipped.")
        return

    print("--- 🛠️ Initializing Fixtures (7 Weeks League + FA Round 1) ---")
    
    # ၂။ Players ဆွဲထုတ်ခြင်း
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

    if len(all_players) < 48:
        print(f"❌ Error: Found only {len(all_players)} players. Need 48.")
        return

    div_a = [p for p in all_players if p['tag'] == 'A']
    div_b = [p for p in all_players if p['tag'] == 'B']
    
    start_gw = 23
    total_weeks = 7
    batch = db.batch()

    # ၃။ League Schedule (Round Robin)
    def create_league_schedule(player_list, division_name):
        n = len(player_list)
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
            # Rotation Logic
            pool = [pool[0]] + [pool[-1]] + pool[1:-1]

    # ၄။ FA Cup R1 (Random 48)
    random.shuffle(all_players)
    for i in range(0, len(all_players), 2):
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

    # ၅။ Firestore သို့ သိမ်းခြင်း
    batch.commit()
    print("✅ Successfully generated 7 weeks of League and FA Cup Round 1.")

if __name__ == "__main__":
    generate_fixtures()
