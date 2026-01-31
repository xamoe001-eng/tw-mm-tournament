import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os, json, random

def initialize_firebase():
    if not firebase_admin._apps:
        sa_info = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        if sa_info:
            cred = credentials.Certificate(json.loads(sa_info))
        else:
            cred = credentials.Certificate('serviceAccountKey.json')
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firebase()
LEAGUE_ID = "400231"
FPL_API = "https://fantasy.premierleague.com/api/"
START_GW = 23 

def setup_fa_cup_fixtures():
    print(f"🚀 Initializing TW FPL FA Cup Fixtures for GW {START_GW}...")
    
    try:
        r = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/").json()
        all_standings = r['standings']['results']
        top_players = all_standings[:48] if len(all_standings) >= 48 else all_standings
            
    except Exception as e:
        print(f"❌ API Error: {e}")
        return

    batch = db.batch()
    players_list = []

    for m in top_players:
        players_list.append({
            "id": str(m['entry']),
            "name": m['player_name'],
            "team": m['entry_name']
        })

    # ၂။ TW FA Cup အတွက် Random နှောခြင်း
    random.shuffle(players_list)
    
    print(f"🏟️ Generating 24 Matchups with Tie-break readiness...")
    
    match_count = 0
    for i in range(0, len(players_list), 2):
        if i+1 < len(players_list):
            h, a = players_list[i], players_list[i+1]
            match_no = (i // 2) + 1
            doc_id = f"FA_GW{START_GW}_Match_{match_no:02d}"
            
            fa_ref = db.collection("fixtures").document(doc_id)
            
            # Fixture structure ထဲမှာ tie_break အတွက် field တွေပါ ထည့်ပေးထားမယ်
            batch.set(fa_ref, {
                "gameweek": START_GW,
                "type": "FA_CUP",
                "match_id": match_no,
                "home": {**h, "points": 0},
                "away": {**a, "points": 0},
                "status": "upcoming",
                "winner": None,
                "tie_break_reason": None, # ဥပမာ- "Captain Points" ကြောင့် နိုင်သည်
                "internal_stats": {
                    "home": {"cap": 0, "vice": 0, "gk": 0},
                    "away": {"cap": 0, "vice": 0, "gk": 0}
                },
                "division": "FA_CUP"
            })
            match_count += 1

    batch.commit()
    print(f"---")
    print(f"✅ Setup Success!")
    print(f"🏆 {match_count} Fixtures created with Tie-break support.")

if __name__ == "__main__":
    setup_fa_cup_fixtures()
