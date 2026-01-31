import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os, json, random

def initialize_firebase():
    if not firebase_admin._apps:
        # GitHub Secrets မှ ဖတ်ရန်၊ မရှိပါက local JSON ဖိုင်မှ ဖတ်မည်
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
START_GW = 23 # FA Cup စတင်မည့်အပတ်

def setup_fa_cup_fixtures():
    print(f"🚀 Initializing TW FPL FA Cup Fixtures for GW {START_GW}...")
    
    # ၁။ FPL API မှ League Standings ဆွဲထုတ်ပြီး Top 48 ကိုယူခြင်း
    try:
        r = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/").json()
        all_standings = r['standings']['results']
        
        if len(all_standings) < 48:
            print(f"⚠️ Warning: League မှာ လူ {len(all_standings)} ယောက်ပဲ ရှိပါတယ်။ ရှိသလောက်နဲ့ပဲ Fixture ဆွဲပါမယ်။")
            top_players = all_standings
        else:
            top_players = all_standings[:48]
            
    except Exception as e:
        print(f"❌ API Error: {e}")
        return

    batch = db.batch()
    players_list = []

    # Player အချက်အလက်များကို Fixture အတွက် ပြင်ဆင်ခြင်း
    for m in top_players:
        players_list.append({
            "id": str(m['entry']),
            "name": m['player_name'],
            "team": m['entry_name']
        })

    # ၂။ TW FA Cup (Play-off) အတွက် Random နှောခြင်း
    random.shuffle(players_list)
    
    print(f"🏟️ Generating 24 Matchups...")
    
    # ၃။ Fixtures collection ထဲသို့ သွင်းခြင်း
    match_count = 0
    for i in range(0, len(players_list), 2):
        # အကယ်၍ လူဦးရေ မစုံပါက (Odd number ဖြစ်နေပါက) နောက်ဆုံးတစ်ယောက်ကို Bye ပေးရန် သို့မဟုတ် ကျန်ခဲ့ရန်
        if i+1 < len(players_list):
            h, a = players_list[i], players_list[i+1]
            match_no = (i // 2) + 1
            doc_id = f"FA_GW{START_GW}_Match_{match_no:02d}"
            
            fa_ref = db.collection("fixtures").document(doc_id)
            batch.set(fa_ref, {
                "gameweek": START_GW,
                "type": "FA_CUP",
                "match_id": match_no,
                "home": {**h, "points": 0},
                "away": {**a, "points": 0},
                "status": "upcoming",
                "winner": None,
                "division": "FA_CUP"
            })
            match_count += 1

    # Database ထဲသို့ Commit လုပ်ခြင်း
    batch.commit()
    print(f"---")
    print(f"✅ Setup Success!")
    print(f"🏆 {match_count} FA Cup Fixtures created in 'fixtures' collection.")
    print(f"📅 Ready for Game Week {START_GW}")

if __name__ == "__main__":
    setup_fa_cup_fixtures()
