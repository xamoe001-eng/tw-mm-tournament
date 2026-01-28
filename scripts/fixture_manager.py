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

# ⚠️ အပတ်စဉ် နှိပ်ခါနီးတိုင်း ပြီးသွားတဲ့အပတ် (PAST) နဲ့ ထုတ်မယ့်အပတ် (NEXT) ကို ပြင်ပေးပါ
PAST_GW = 26    # ဥပမာ - GW 26 ပြီးသွားချိန်
NEXT_GW = 27    # GW 27 (Semi-Final) ထွက်လာမည်

def generate_fa_fixtures():
    print(f"🏆 FA Cup Manager: Generating GW {NEXT_GW} based on GW {PAST_GW} results...")
    
    winners = []
    losers = []
    
    # ၁။ အရင်အပတ်က FA Cup ရလဒ်များကို History မှ ဆွဲထုတ်ခြင်း
    history_ref = db.collection("fixtures_history_fa").where("gameweek", "==", PAST_GW).stream()
    
    for doc in history_ref:
        f = doc.to_dict()
        h = f['home']
        a = f['away']
        
        # နိုင်သူ/ရှုံးသူ ခွဲခြားခြင်း
        if h.get('points', 0) > a.get('points', 0):
            winners.append(h)
            losers.append(a)
        elif a.get('points', 0) > h.get('points', 0):
            winners.append(a)
            losers.append(h)
        else:
            # အမှတ်တူနေလျှင် ကျပန်းရွေးပြီး ကျန်သူကို Loser ထဲထည့်မည်
            lucky, unlucky = random.sample([h, a], 2)
            winners.append(lucky)
            losers.append(unlucky)

    if not winners:
        print("❌ No data found in history. Sync the GW first!")
        return

    # ၂။ Lucky Loser Logic: GW 26 မှာ အသင်း ၃ သင်းပဲ နိုင်တဲ့အခါ ၄ သင်းပြည့်အောင် ၁ သင်း ပြန်ခေါ်မည်
    if PAST_GW == 26 and len(winners) == 3:
        print("🎯 Selecting Lucky Loser from GW 26 Losers...")
        # ရှုံးတဲ့သူ ၃ ယောက်ထဲက အမှတ်အများဆုံး (Highest Points) ကို ယူမည်
        # အမှတ်တူနေလျှင် ပထမဆုံးတစ်ယောက်ကို ယူမည်
        lucky_loser = max(losers, key=lambda x: x.get('points', 0))
        print(f"🔥 Lucky Loser: {lucky_loser['name']} ({lucky_loser.get('points', 0)} pts)")
        winners.append(lucky_loser)

    # ၃။ တွဲဆိုင်းအသစ်များ ထုတ်ပြန်ခြင်း
    print(f"✨ Total Teams for GW {NEXT_GW}: {len(winners)}")
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

    # ၄။ တစ်သင်းကျန်နေသေးလျှင် (Bye Logic - GW 26 မဟုတ်တဲ့အပတ်များအတွက်)
    if len(winners) == 1:
        bye_player = winners[0]
        print(f"🎁 BYE: {bye_player['name']} automatically through to GW {NEXT_GW + 1}")
        # Bye ရသူကို History ထဲ နိုင်သူအဖြစ် ကြိုထည့်ထားမည်
        db.collection("fixtures_history_fa").document(f"FA_GW{NEXT_GW}_BYE").set({
            "gameweek": NEXT_GW,
            "type": "fa_cup",
            "home": {**bye_player, "points": 1},
            
            "away":
