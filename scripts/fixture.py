import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import random

def initialize_firebase():
    if not firebase_admin._apps:
        service_account_info = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        if service_account_info:
            cred = credentials.Certificate(json.loads(service_account_info))
            firebase_admin.initialize_app(cred)
        else:
            firebase_admin.initialize_app(credentials.Certificate('serviceAccountKey.json'))
    return firestore.client()

db = initialize_firebase()

# Configuration
LEAGUE_ID = "400231"
FPL_API = "https://fantasy.premierleague.com/api/"
START_GW = 23
TOTAL_WEEKS = 7

def generate_fixtures():
    print("🚀 Fetching Top 48 Managers & Generating Season Schedule...")

    # ၁။ FPL Standings မှ ထိပ်ဆုံး ၄၈ သင်းကို ဆွဲယူခြင်း
    try:
        r = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/").json()
        top_48 = sorted(r['standings']['results'], key=lambda x: x['total'], reverse=True)[:48]
    except Exception as e:
        print(f"❌ Error: {e}")
        return

    div_a = [{"id": str(m['entry']), "name": m['player_name'], "team": m['entry_name']} for m in top_48[:24]]
    div_b = [{"id": str(m['entry']), "name": m['player_name'], "team": m['entry_name']} for m in top_48[24:48]]

    batch = db.batch()

    # ၂။ Round Robin Algorithm (လိဂ်ပွဲစဉ် ၇ ပတ်စာ ကြိုထုတ်ခြင်း)
    def create_league_fixtures(players, division_name):
        pool = list(players)
        n = len(pool)
        for week in range(TOTAL_WEEKS):
            current_gw = START_GW + week
            # တွဲဆိုင်းများ ထုတ်ယူခြင်း
            for i in range(n // 2):
                home, away = pool[i], pool[n - 1 - i]
                doc_id = f"GW{current_gw}_{division_name.replace(' ', '')}_M{i+1}"
                f_ref = db.collection("fixtures").document(doc_id)
                batch.set(f_ref, {
                    "gameweek": current_gw,
                    "division": division_name,
                    "type": "league",
                    "home": {**home, "points": 0},
                    "away": {**away, "points": 0},
                    "status": "upcoming"
                })
            # Rotation (ပထမတစ်ယောက်ကို ထားပြီး ကျန်တာကို လှည့်သည်)
            pool = [pool[0]] + [pool[-1]] + pool[1:-1]

    # Div A & B အတွက် လိဂ်ပွဲစဉ်များ ထုတ်မည်
    create_league_fixtures(div_a, "Division A")
    create_league_fixtures(div_b, "Division B")

    # ၃။ FA Cup Round 1 (GW 23 အတွက် ၄၈ သင်းလုံး ကျပန်း Playoff တွဲပေးခြင်း)
    all_players = div_a + div_b
    random.shuffle(all_players)
    for i in range(0, len(all_players), 2):
        h, a = all_players[i], all_players[i+1]
        fa_id = f"FA_GW{START_GW}_Match_{i//2 + 1}"
        batch.set(db.collection("fixtures").document(fa_id), {
            "gameweek": START_GW,
            "division": "FA_CUP",
            "type": "fa_cup",
            "home": {**h, "points": 0},
            "away": {**a, "points": 0},
            "status": "upcoming"
        })

    batch.commit()
    print(f"✅ SUCCESS: 7-Week League & FA Cup Round 1 Created!")

if __name__ == "__main__":
    generate_fixtures()
