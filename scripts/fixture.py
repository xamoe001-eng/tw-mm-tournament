import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import random

# ၁။ Firebase ချိတ်ဆက်ခြင်း
def initialize_firebase():
    if not firebase_admin._apps:
        service_account_info = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        if service_account_info:
            # GitHub Secrets အတွက်
            cred_dict = json.loads(service_account_info)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        else:
            # Local အတွက် serviceAccountKey.json ကို သုံးမယ်
            cred_path = 'serviceAccountKey.json'
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            else:
                raise FileNotFoundError("Missing Firebase Credentials (serviceAccountKey.json)")
    return firestore.client()

db = initialize_firebase()

# Configuration
LEAGUE_ID = "400231"
FPL_API = "https://fantasy.premierleague.com/api/"
START_GW = 23 # Tournament စမည့်အပတ်

def generate_fixtures():
    print(f"--- 🛠️ Starting Fixture Generation (GW {START_GW} - {START_GW+6}) ---")

    # ၂။ Guard Logic: ပွဲစဉ်တွေ ရှိပြီးသားဆိုရင် ထပ်မလုပ်ဖို့ စစ်ဆေးခြင်း
    check = db.collection("fixtures").where("gameweek", "==", START_GW).limit(1).get()
    if len(check) > 0:
        print(f"⚠️ Fixtures for GW {START_GW} already exist. Generation skipped to prevent duplication.")
        return

    # ၃။ FPL Standings မှ ထိပ်ဆုံး ၄၈ သင်းကို ဆွဲယူခြင်း
    try:
        r = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/", timeout=10).json()
        top_48 = sorted(r['standings']['results'], key=lambda x: x['total'], reverse=True)[:48]
        print(f"✅ Successfully fetched {len(top_48)} managers.")
    except Exception as e:
        print(f"❌ Error fetching FPL data: {e}")
        return

    div_a_players = []
    div_b_players = []
    all_players = []

    # ၄။ Sync Code နှင့် ကိုက်ညီအောင် Division ခွဲခြင်း
    for index, m in enumerate(top_48):
        p_info = {
            "id": str(m['entry']),
            "name": m['player_name'],
            "team": m['entry_name']
        }
        if index < 24:
            div_a_players.append(p_info)
        else:
            div_b_players.append(p_info)
        all_players.append(p_info)

    batch = db.batch()

    # ၅။ Round Robin Logic (၇ ပတ်စာ မထပ်အောင် စီခြင်း)
    def create_round_robin(player_list, division_name):
        n = len(player_list)
        pool = list(player_list)
        for week in range(7):
            current_gw = START_GW + week
            for i in range(n // 2):
                home, away = pool[i], pool[n - 1 - i]
                
                # Document ID ပုံသေပေးခြင်းဖြင့် overwrite ဖြစ်စေသည်
                f_id = f"GW{current_gw}_{division_name.replace(' ', '')}_M{i+1}"
                f_ref = db.collection("fixtures").document(f_id)
                
                batch.set(f_ref, {
                    "gameweek": current_gw,
                    "division": division_name,
                    "type": "league",
                    "home": home,
                    "away": away,
                    "status": "upcoming"
                })
            # Round Robin Rotation
            pool = [pool[0]] + [pool[-1]] + pool[1:-1]

    # League Fixtures များ ထည့်သွင်းခြင်း
    create_round_robin(div_a_players, "Division A")
    create_round_robin(div_b_players, "Division B")

    # ၆။ FA Cup Round 1 (GW 23 အတွက် ၄၈ သင်းလုံး ကျပန်းတွဲခြင်း)
    random.shuffle(all_players)
    for i in range(0, len(all_players), 2):
        if i+1 < len(all_players):
            h, a = all_players[i], all_players[i+1]
            fa_id = f"FA_GW{START_GW}_Match_{i//2 + 1}"
            batch.set(db.collection("fixtures").document(fa_id), {
                "gameweek": START_GW,
                "division": "FA_CUP",
                "type": "fa_cup",
                "home": h,
                "away": a,
                "status": "upcoming"
            })

    # ၇။ Batch Commit လုပ်ခြင်း
    batch.commit()
    print(f"✅ SUCCESS: Fixtures for GW {START_GW} to {START_GW+6} have been uploaded.")

if __name__ == "__main__":
    generate_fixtures()
