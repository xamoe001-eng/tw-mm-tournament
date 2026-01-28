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
            cred = credentials.Certificate(json.loads(service_account_info))
        else:
            # Local စမ်းသပ်ရန်အတွက်
            cred = credentials.Certificate('serviceAccountKey.json')
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firebase()

def generate_fixtures():
    # START_GW ကို သတ်မှတ်ခြင်း (မိတ်ဆွေ စချင်သည့် GW)
    start_gw = 23 
    
    # ၂။ Guard Logic: ပွဲစဉ်တွေ ရှိပြီးသားဆိုရင် ထပ်မဆောက်အောင် တားခြင်း
    existing_check = db.collection("fixtures").where("gameweek", "==", start_gw).limit(1).get()
    if len(existing_check) > 0:
        print(f"⚠️ Fixtures for GW {start_gw} already exist. Generation skipped to avoid duplicates.")
        return

    print("--- 🛠️ Initializing Fixtures for Division A, B and TW FA Cup ---")
    
    # ၃။ Players စာရင်းယူခြင်း
    players_ref = db.collection("tw_mm_tournament").stream()
    all_players = []
    for p in players_ref:
        data = p.to_dict()
        all_players.append({
            "id": data['fpl_id'], 
            "name": data['manager_name'],
            "team": data['team_name'], 
            "tag": data.get('league_tag', 'B') # Tag မပါရင် Division B လို့ သတ်မှတ်
        })

    if len(all_players) < 48:
        print(f"❌ Error: Found only {len(all_players)} players. Need 48.")
        return

    div_a = [p for p in all_players if p['tag'] == 'A']
    div_b = [p for p in all_players if p['tag'] == 'B']
    
    total_weeks = 7
    batch = db.batch()

    # ၄။ League Schedule Generator (Round Robin Logic)
    def create_league_schedule(player_list, division_name):
        n = len(player_list)
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

    # Division A အတွက် Generate လုပ်ခြင်း
    print("Generating Division A...")
    create_league_schedule(div_a, "A")
    
    # Division B အတွက် Generate လုပ်ခြင်း (Update Line #36)
    print("Generating Division B...")
    create_league_schedule(div_b, "B")

    # ၅။ FA Cup Round 1 (Random Pairings for 48 Players)
    print("Generating FA Cup Round 1...")
    random.shuffle(all_players)
    for i in range(0, len(all_players), 2):
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
            "stage": "Round of 48"
        })

    # ၆။ Firestore သို့ အကုန်ပို့ခြင်း
    batch.commit()
    print("✅ Successfully generated all fixtures for 7 weeks!")

if __name__ == "__main__":
    generate_
    fixtures()
