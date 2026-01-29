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
            try:
                firebase_admin.initialize_app(credentials.Certificate('serviceAccountKey.json'))
            except:
                print("❌ Firebase Credentials မတွေ့ပါ။ JSON file ကို စစ်ဆေးပါ။")
    return firestore.client()

db = initialize_firebase()

# --- Configuration ---
LEAGUE_ID = "400231"
FPL_API = "https://fantasy.premierleague.com/api/"
START_GW = 23
TOTAL_WEEKS = 7

def generate_fixtures():
    print(f"🚀 Fetching Top 48 Managers & Generating Schedule starting from GW {START_GW}...")

    # ၁။ FPL Standings မှ ထိပ်ဆုံး ၄၈ သင်းကို ဆွဲယူခြင်း
    try:
        r = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/").json()
        # အမှတ်အများဆုံး ၄၈ သင်းကို ယူသည်
        top_48 = sorted(r['standings']['results'], key=lambda x: x['total'], reverse=True)[:48]
    except Exception as e:
        print(f"❌ Error fetching FPL data: {e}"); return

    if len(top_48) < 48:
        print(f"⚠️ Warning: League ထဲမှာ Manager {len(top_48)} ယောက်ပဲ ရှိပါတယ်။ ၄၈ ယောက် မပြည့်ပါ။")

    # Division ခွဲခြင်း (၁-၂၄ သည် Div A, ၂၅-၄၈ သည် Div B)
    div_a = [{"id": str(m['entry']), "name": m['player_name'], "team": m['entry_name']} for m in top_48[:24]]
    div_b = [{"id": str(m['entry']), "name": m['player_name'], "team": m['entry_name']} for m in top_48[24:48]]

    batch = db.batch()

    # ၂။ Round Robin Algorithm (လိဂ်ပွဲစဉ် ၇ ပတ်စာ ကြိုထုတ်ခြင်း)
    def create_league_fixtures(players, division_name):
        pool = list(players)
        n = len(pool)
        for week in range(TOTAL_WEEKS):
            current_gw = START_GW + week
            
            # Round Robin Rotation (ပထမတစ်ယောက်ကို ထားပြီး ကျန်တာကို လှည့်သည့်စနစ်)
            for i in range(n // 2):
                home, away = pool[i], pool[n - 1 - i]
                
                # Document ID ကို ရှာရလွယ်အောင် ပုံစံချခြင်း
                doc_id = f"GW{current_gw}_{division_name.replace(' ', '')}_Match{i+1}"
                f_ref = db.collection("fixtures").document(doc_id)
                
                batch.set(f_ref, {
                    "gameweek": current_gw,
                    "division": division_name,
                    "type": "league",
                    "home": {**home, "points": 0},
                    "away": {**away, "points": 0},
                    "status": "upcoming", # Sync Code က ဤနေရာကို live/completed ပြောင်းပေးမည်
                    "created_at": firestore.SERVER_TIMESTAMP
                })
            
            # Rotate logic for Round Robin
            pool = [pool[0]] + [pool[-1]] + pool[1:-1]

    # Division A & B အတွက် လိဂ်ပွဲစဉ်များ သီးခြားစီ ထုတ်မည်
    print("📅 Generating League Fixtures...")
    create_league_fixtures(div_a, "Division A")
    create_league_fixtures(div_b, "Division B")

    # ၃။ FA Cup Round 1 (GW 23 အတွက် ၄၈ သင်းလုံး ကျပန်း Playoff)
    print("🏆 Generating FA Cup Round 1 Fixtures...")
    all_players = div_a + div_b
    random.shuffle(all_players)
    
    for i in range(0, len(all_players), 2):
        if i + 1 < len(all_players):
            h, a = all_players[i], all_players[i+1]
            fa_id = f"FA_GW{START_GW}_Match_{i//2 + 1}"
            batch.set(db.collection("fixtures").document(fa_id), {
                "gameweek": START_GW,
                "division": "FA_CUP",
                "type": "fa_cup",
                "home": {**h, "points": 0},
                "away": {**a, "points": 0},
                "status": "upcoming",
                "created_at": firestore.SERVER_TIMESTAMP
            })

    # Firestore ထဲသို့ တစ်ပြိုင်နက် သိမ်းဆည်းခြင်း
    batch.commit()
    print(f"✅ SUCCESS: {TOTAL_WEEKS}-Week Schedule and FA Cup Round 1 created in Firestore!")

if __name__ == "__main__":
    generate_fixtures()
