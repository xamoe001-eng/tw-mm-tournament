import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import random

# ၁။ Firebase Initializing
def initialize_firebase():
    if not firebase_admin._apps:
        service_account_info = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        if service_account_info:
            cred_dict = json.loads(service_account_info)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        else:
            # Local အတွက် serviceAccountKey.json ရှိရပါမယ်
            cred = credentials.Certificate('serviceAccountKey.json')
            firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firebase()

# Configuration (Sync Code နှင့် တူအောင်ထားခြင်း)
LEAGUE_ID = "400231"
FPL_API = "https://fantasy.premierleague.com/api/"
START_GW = 23 # Tournament စမည့်အပတ်

def generate_fixtures():
    print("--- 🛠️ Starting Fixture Generation (GW 23-29) ---")

    # ၂။ FPL Standings မှ ထိပ်ဆုံး ၄၈ သင်းကို ဆွဲယူခြင်း
    try:
        r = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/", timeout=10).json()
        top_48 = sorted(r['standings']['results'], key=lambda x: x['total'], reverse=True)[:48]
    except Exception as e:
        print(f"❌ Error fetching FPL data: {e}")
        return

    div_a_players = []
    div_b_players = []
    all_players = []

    # ၃။ Sync Code ၏ Index Logic အတိုင်း Division ခွဲခြင်း
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

    # ၄။ Round Robin Schedule Generator (၇ ပတ်စာ)
    def create_round_robin(player_list, division_name):
        n = len(player_list)
        pool = list(player_list)
        for week in range(7):
            current_gw = START_GW + week
            # တစ်ပတ်မှာ ၁၂ ပွဲ (၂၄ ယောက်)
            for i in range(n // 2):
                home, away = pool[i], pool[n - 1 - i]
                
                # Document ID ဥပမာ - GW23_DivisionA_Match1
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
            # Round Robin Rotation: ပထမလူကို ငြိမ်ထားပြီး ကျန်လူများကို လှည့်ခြင်း
            pool = [pool[0]] + [pool[-1]] + pool[1:-1]

    # League Fixtures များ ထည့်သွင်းခြင်း
    create_round_robin(div_a_players, "Division A")
    create_round_robin(div_b_players, "Division B")

    # ၅။ FA Cup Round 1 (GW 23 အတွက် ၄၈ သင်းလုံး ကျပန်းတွဲခြင်း)
    random.shuffle(all_players)
    for i in range(0, len(all_players), 2):
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

    # ၆။ Batch Commit (Database ထဲ သိမ်းခြင်း)
    batch.commit()
    print(f"✅ Fixtures for GW {START_GW} to {START_GW+6} successfully generated!")

if __name__ == "__main__":
    generate_fixtures()
