import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import random
import requests

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

# ⚠️ အပတ်စဉ် ပြောင်းလဲပေးရန်
PAST_GW = 23    # ပြီးသွားသောအပတ်
NEXT_GW = 24    # ထုတ်မည့်အပတ်
FPL_API = "https://fantasy.premierleague.com/api/"

def get_tie_break_stats(entry_id, gw_num):
    """ အမှတ်တူလျှင် Captain, Vice, GK အမှတ်များကို API မှ ဆွဲယူခြင်း """
    try:
        url = f"{FPL_API}entry/{entry_id}/event/{gw_num}/picks/"
        res = requests.get(url, timeout=10).json()
        picks = res['picks']
        
        cap_id = next(p for p in picks if p['is_captain'])['element']
        vice_id = next(p for p in picks if p['is_vice_captain'])['element']
        gk_id = picks[0]['element']

        def fetch_pts(p_id):
            p_res = requests.get(f"{FPL_API}element-summary/{p_id}/").json()
            return next(e['event_points'] for e in p_res['history'] if e['event'] == gw_num)

        return {
            "cap": fetch_pts(cap_id),
            "vice": fetch_pts(vice_id),
            "gk": fetch_pts(gk_id)
        }
    except:
        return {"cap": 0, "vice": 0, "gk": 0}

def generate_fa_fixtures():
    source_collection = "fixtures" 
    print(f"🏆 FA Cup Manager: Generating GW {NEXT_GW} based on GW {PAST_GW} results...")
    
    winners = []
    losers = []
    
    query = db.collection(source_collection)\
              .where("gameweek", "==", PAST_GW)\
              .where("type", "==", "fa_cup")\
              .stream()
    
    for doc in query:
        f = doc.to_dict()
        h, a = f['home'], f['away']
        h_pts, a_pts = h.get('points', 0), a.get('points', 0)
        
        if h_pts > a_pts:
            winners.append(h); losers.append(a)
        elif a_pts > h_pts:
            winners.append(a); losers.append(h)
        else:
            # 🔥 Tie-breaker Logic
            print(f"⚖️ Tie-break for {h['name']} vs {a['name']}")
            h_stats = get_tie_break_stats(h['id'], PAST_GW)
            a_stats = get_tie_break_stats(a['id'], PAST_GW)
            
            winner = None
            if h_stats['cap'] != a_stats['cap']:
                winner = h if h_stats['cap'] > a_stats['cap'] else a
            elif h_stats['vice'] != a_stats['vice']:
                winner = h if h_stats['vice'] > a_stats['vice'] else a
            elif h_stats['gk'] != a_stats['gk']:
                winner = h if h_stats['gk'] > a_stats['gk'] else a
            else:
                winner = random.choice([h, a]) # အားလုံးတူလျှင် မဲနှိုက်သည်

            loser = a if winner == h else h
            print(f"🏅 Tie-break Winner: {winner['name']}")
            winners.append(winner); losers.append(loser)

    if not winners:
        print(f"❌ GW {PAST_GW} အတွက် FA Cup data မတွေ့ပါ။"); return

    # ၂။ Lucky Loser Logic (GW 26 အထူးပြုချက်)
    if PAST_GW == 26 and len(winners) == 3:
        lucky_loser = max(losers, key=lambda x: x.get('points', 0))
        print(f"🔥 Lucky Loser Found: {lucky_loser['name']} with {lucky_loser.get('points', 0)} pts")
        winners.append(lucky_loser)

    # ၃။ တွဲဆိုင်းသစ်များ ဖန်တီးခြင်း
    random.shuffle(winners)
    batch = db.batch()
    match_count = 1
    
    while len(winners) >= 2:
        home, away = winners.pop(), winners.pop()
        f_id = f"FA_GW{NEXT_GW}_Match_{match_count}"
        f_ref = db.collection("fixtures").document(f_id)
        
        batch.set(f_ref, {
            "gameweek": NEXT_GW,
            "type": "fa_cup",
            "division": "FA_CUP",
            "home": {"id": home['id'], "name": home['name'], "team": home.get('team', ''), "points": 0},
            "away": {"id": away['id'], "name": away['name'], "team": away.get('team', ''), "points": 0},
            "status": "upcoming"
        })
        match_count += 1

    batch.commit()
    print(f"✅ SUCCESS: GW {NEXT_GW} FA Cup Fixtures Created!")

if __name__ == "__main__":
    generate_fa_fixtures()
