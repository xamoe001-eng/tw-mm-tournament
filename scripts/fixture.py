import firebase_admin
from firebase_admin import credentials, firestore
import random
import os
import json

# ၁။ Firebase Initialize လုပ်ခြင်း
def initialize_firebase():
    if not firebase_admin._apps:
        # GitHub Secret ထဲက Key ကို အရင်စစ်မည်
        service_account_info = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        
        if service_account_info:
            # Secret ရှိနေရင် (GitHub ပေါ်မှာ run နေရင်) အလုပ်လုပ်မည့် logic
            print("✅ Using FIREBASE_SERVICE_ACCOUNT from GitHub Secrets")
            try:
                cred_dict = json.loads(service_account_info)
                cred = credentials.Certificate(cred_dict)
            except Exception as e:
                print(f"❌ Error parsing JSON from Secrets: {e}")
                raise e
        else:
            # Secret မရှိရင် (Local ကွန်ပျူတာမှာ စမ်းနေရင်) ဖိုင်ကို ရှာမည်
            print("ℹ️ Secret not found. Looking for local serviceAccountKey.json")
            try:
                cred = credentials.Certificate('serviceAccountKey.json')
            except Exception as e:
                print(f"❌ Local serviceAccountKey.json not found: {e}")
                raise e
            
        firebase_admin.initialize_app(cred)
    return firestore.client()

# Firebase Database ကို စတင်ချိတ်ဆက်ခြင်း
db = initialize_firebase()

def generate_fixtures():
    # စတင်မည့် Gameweek
    start_gw = 23 
    
    # ၂။ Guard Logic: ပွဲစဉ်ရှိမရှိ အရင်စစ်မည် (Duplicate မဖြစ်အောင်)
    try:
        existing_check = db.collection("fixtures").where("gameweek", "==", start_gw).limit(1).get()
        if len(existing_check) > 0:
            print(f"⚠️ Fixtures for GW {start_gw} already exist. Generation skipped.")
            return
    except Exception as e:
        print(f"❌ Database error: {e}")
        return

    print("--- 🛠️ Generating Fixtures for Division A, B and FA Cup ---")
    
    # ၃။ Player စာရင်းယူခြင်း
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

    if not all_players:
        print("❌ No players found in 'tw_mm_tournament'!")
        return

    div_a = [p for p in all_players if p['tag'] == 'A']
    div_b = [p for p in all_players if p['tag'] == 'B']
    
    batch = db.batch()

    # ၄။ League Logic (Round Robin)
    def create_league_schedule(player_list, division_name):
        n = len(player_list)
        if n < 2: return
        pool = list(player_list)
        for week in range(7):
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

    if div_a: create_league_schedule(div_a, "A")
    if div_b: create_league_schedule(div_b, "B")

    # ၅။ FA Cup Round 1
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
                "status": "upcoming"
            })

    # Firestore သို့ Batch အလိုက် တစ်ခါတည်း Update လုပ်ခြင်း
    batch.commit()
    print("✅ Fixtures successfully generated and uploaded to Firestore!")

if __name__ == "__main__":
    generate_fixtures()
