import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import random

# ... (initialize_firebase logic အဟောင်းအတိုင်းထားပါ) ...

def generate_fa_fixtures():
    # ၁။ အချက်အလက်ဆွဲယူမည့် Collection ကို သေချာသတ်မှတ်ပါ
    # အမှတ်သွင်းတုန်းက fixtures ထဲမှာပဲ သိမ်းခဲ့ရင် fixtures ကိုပဲ သုံးရပါမယ်
    source_collection = "fixtures" 
    
    print(f"🏆 FA Cup Manager: Generating GW {NEXT_GW} based on GW {PAST_GW} results...")
    
    winners = []
    losers = []
    
    # PAST_GW က FA Cup ပွဲစဉ်တွေကိုပဲ ဆွဲထုတ်မယ်
    query = db.collection(source_collection)\
              .where("gameweek", "==", PAST_GW)\
              .where("type", "==", "fa_cup")\
              .stream()
    
    for doc in query:
        f = doc.to_dict()
        # Nested Object (home.points) ဖြစ်တဲ့အတွက် data structure ကို ဂရုစိုက်ပါ
        h = f['home']
        a = f['away']
        
        h_pts = h.get('points', 0)
        a_pts = a.get('points', 0)
        
        if h_pts > a_pts:
            winners.append(h)
            losers.append(a)
        elif a_pts > h_pts:
            winners.append(a)
            losers.append(h)
        else:
            lucky, unlucky = random.sample([h, a], 2)
            winners.append(lucky)
            losers.append(unlucky)

    if not winners:
        print(f"❌ GW {PAST_GW} အတွက် FA Cup data မတွေ့ပါ။ Sync အရင်လုပ်ထားသလား စစ်ပေးပါ။")
        return

    # ၂။ Lucky Loser Logic (GW 26 ဖြစ်ခဲ့လျှင်)
    if PAST_GW == 26 and len(winners) == 3:
        # Losers ထဲက အမှတ်အများဆုံးလူကို ရှာမယ်
        lucky_loser = max(losers, key=lambda x: x.get('points', 0))
        print(f"🔥 Lucky Loser Found: {lucky_loser['name']} with {lucky_loser.get('points', 0)} pts")
        winners.append(lucky_loser)

    # ၃။ တွဲဆိုင်းအသစ်ထုတ်ခြင်း (Shuffle winners for random draw)
    random.shuffle(winners)
    batch = db.batch()
    match_count = 1
    
    while len(winners) >= 2:
        home = winners.pop()
        away = winners.pop()
        
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
    print(f"✅ GW {NEXT_GW} FA Cup Fixtures Created!")
