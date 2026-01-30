import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os, json, random

def initialize_firebase():
    if not firebase_admin._apps:
        # GitHub Secrets ကနေဖတ်မယ်၊ မရှိရင် local JSON ဖိုင်ကနေဖတ်မယ်
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

def setup_tournament():
    print("🚀 Initializing Tournament Setup...")
    
    # ၁။ FPL API မှ Player များဆွဲထုတ်ခြင်း
    try:
        r = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/").json()
        top_48 = sorted(r['standings']['results'], key=lambda x: x['total'], reverse=True)[:48]
    except Exception as e:
        print(f"❌ API Error: {e}")
        return

    batch = db.batch()
    all_players = []

    # ၂။ Division ခွဲခြားခြင်းနှင့် League Table (tw_mm_tournament) တည်ဆောက်ခြင်း
    for index, m in enumerate(top_48):
        entry_id = str(m['entry'])
        # ပထမ ၂၄ ယောက်က Div A၊ ကျန် ၂၄ ယောက်က Div B
        div = "Division A" if index < 24 else "Division B"
        
        player_data = {
            "id": entry_id,
            "name": m['player_name'],
            "team": m['entry_name']
        }
        all_players.append(player_data)
        
        # tw_mm_tournament collection ထဲသို့ ထည့်မည်
        doc_ref = db.collection("tw_mm_tournament").document(entry_id)
        batch.set(doc_ref, {
            **player_data,
            "division": div,
            "tournament_total_net_points": 0,
            "gw_live_points": 0,
            "last_synced_gw": START_GW - 1 # ၂၃ ကနေ အမှတ်စတွက်နိုင်ရန်
        }, merge=True)

    # ၃။ FA Cup Round 1 (fixtures collection) အတွက် တွဲဆိုင်းထုတ်ခြင်း
    random.shuffle(all_players) # Random နှောမည်
    
    for i in range(0, len(all_players), 2):
        h, a = all_players[i], all_players[i+1]
        match_no = (i // 2) + 1
        doc_id = f"FA_GW{START_GW}_Match_{match_no}"
        
        fa_ref = db.collection("fixtures").document(doc_id)
        batch.set(fa_ref, {
            "gameweek": START_GW,
            "type": "fa_cup",
            "home": {**h, "points": 0},
            "away": {**a, "points": 0},
            "status": "upcoming",
            "tie_break_winner": None,
            "division": "FA_CUP"
        })

    batch.commit()
    print(f"✅ Setup Success: 48 Managers mapped to Divisions and FA Cup GW {START_GW} created.")

if __name__ == "__main__":
    setup_tournament()
