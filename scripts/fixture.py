import firebase_admin
from firebase_admin import credentials, firestore
import random
import os
import json

# ၁။ Firebase Initialize လုပ်ခြင်း
def initialize_firebase():
    if not firebase_admin._apps:
        # GitHub Secrets မှတစ်ဆင့် Service Account ကို ယူမည်
        service_account_info = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        
        if service_account_info:
            # GitHub ပေါ်တွင် Run နေပါက Secret ကိုသုံးမည်
            try:
                cred_dict = json.loads(service_account_info)
                cred = credentials.Certificate(cred_dict)
            except Exception as e:
                print(f"❌ Error parsing JSON from Secrets: {e}")
                raise e
        else:
            # Local တွင် စမ်းသပ်နေပါက ဖိုင်ကိုသုံးမည်
            print("ℹ️ Using local serviceAccountKey.json")
            cred = credentials.Certificate('serviceAccountKey.json')
            
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firebase()

def generate_fixtures():
    # စတင်မည့် Gameweek
    start_gw = 23 
    
    # ၂။ Guard Logic: ပွဲစဉ်တွေ ရှိပြီးသားဆိုရင် ထပ်မဆောက်အောင် တားခြင်း
    try:
        existing_check = db.collection("fixtures").where("gameweek", "==", start_gw).limit(1).get()
        if len(existing_check) > 0:
            print(f"⚠️ Fixtures for GW {start_gw} already exist. Generation skipped.")
            return
    except Exception as e:
        print(f"❌ Firestore Access Error: {e}")
        return

    print("--- 🛠️ Initializing Fixtures for Division A, B and TW FA Cup ---")
    
    # ၃။ Players စာရင်းယူခြင်း
    players_ref = db.collection("tw_mm_tournament").stream()
    all_players = []
    for p in players_ref:
        data = p.to_dict()
        all_players.append({
            "id": data.get('fpl_id'), 
            "name": data.get('manager_name'),
            "team": data.get('team_name'), 
            "tag": data.get('league_tag', 'B') 
        })

    if len(all_players) < 2:
        print(f"❌ Error: Not enough players found in 'tw_mm_tournament'.")
        return

    div_a = [p for p in all_players if p['tag'] == 'A']
    div_b = [p for p in all_players if p['tag'] == 'B']
    
    total_weeks = 7
    batch = db.batch()

    # ၄။ League Schedule Generator (Round Robin Logic)
    def create_league_schedule(player_list, division_name):
        n = len(player_list)
        if n % 2 != 0:
            print(f"⚠️ Warning: {division_name} has odd number of players ({n}).")
            
        pool = list(player_list)
        for week in range(total_weeks):
            current_gw = start_gw + week
            for i in range(n // 2):
                h, a = pool[i], pool[n-1-i]
                f_id = f"GW{current_gw}_{division_name}_P{i+1}"
                f_ref = db.collection("fixtures").document(f_id)
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

    # Division A & B Generate လုပ်ခြင်း
    if div_a: 
        print(f"Generating Division A ({len(div_a)} players)...")
        create_league_schedule(div_a, "A")
    
    if div_b:
        print(f"Generating Division B ({len(div_b)} players)...")
        create_league_schedule(div_b, "B")

    # ၅။ FA Cup Round 1
    print(f"Generating FA Cup Round 1 for {len(all_players)} players...")
    random.shuffle(all_players)
    for i in range(0, len(all_players), 2):
        if i+1 < len(all_players):
            h, a = all_players[i], all_players[i+1]
            f_id = f"GW{start_gw}_FA_R1_P{i//2 + 1}"
            f_ref = db.collection("fixtures").document(f_id)
            batch.set(f_ref, {
                "gameweek": start_gw, 
                "division": "FA_CUP", 
                "type": "fa_cup",
                "home": h, 
                "away": a, 
                "status": "upcoming", 
                "stage": "Round 1"
            })

    # ၆။ Firestore သို့ အကုန်ပို့ခြင်း
    batch.commit()
    print("✅ Successfully generated all fixtures!")

if __name__ == "__main__":
    generate_
    fixtures()
