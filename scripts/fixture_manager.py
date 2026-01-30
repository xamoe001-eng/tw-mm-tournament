import firebase_admin
from firebase_admin import credentials, firestore
import os, json, random

def initialize_firebase():
    if not firebase_admin._apps:
        sa_info = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        cred = credentials.Certificate(json.loads(sa_info)) if sa_info else credentials.Certificate('serviceAccountKey.json')
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firebase()

# ⚠️ GW 26 ပြီးလို့ ၂၇ အတွက် ထုတ်တဲ့အခါ ဒါကို သုံးပါ
PREVIOUS_GW = 26
NEXT_GW = 27

def generate_next_round():
    print(f"🏆 GW {PREVIOUS_GW} Winners နှင့် Lucky Loser ကို ရှာဖွေနေသည်...")
    
    fa_ref = db.collection("fixtures") \
               .where("gameweek", "==", PREVIOUS_GW) \
               .where("type", "==", "fa_cup").stream()
    
    winners = []
    losers = []

    for doc in fa_ref:
        f = doc.to_dict()
        winner_id = f.get("tie_break_winner")
        
        # Winner နဲ့ Loser ကို ခွဲထုတ်ခြင်း
        if str(f['home']['id']) == str(winner_id):
            winners.append(f['home'])
            losers.append(f['away'])
        else:
            winners.append(f['away'])
            losers.append(f['home'])

    # GW 26 ဆိုရင် Lucky Loser (အမှတ်အများဆုံး ရှုံးတဲ့လူ) ၁ ယောက် ထည့်မယ်
    final_players = winners.copy()
    if PREVIOUS_GW == 26 and len(losers) > 0:
        # Losers တွေကို points အလိုက် ကြီးစဉ်ငယ်လိုက် စီပြီး ထိပ်ဆုံးတစ်ယောက်ယူမယ်
        lucky_loser = sorted(losers, key=lambda x: x.get('points', 0), reverse=True)[0]
        final_players.append(lucky_loser)
        print(f"✨ Lucky Loser: {lucky_loser['name']} ({lucky_loser['points']} pts) ကို ရွေးချယ်ပြီးပါပြီ။")

    print(f"✅ စုစုပေါင်း ကစားသမား {len(final_players)} ဦးဖြင့် ပွဲစဉ်တွဲပါမည်။")

    if len(final_players) < 2:
        print("❌ လူမလုံလောက်ပါ။"); return

    random.shuffle(final_players)
    batch = db.batch()
    
    for i in range(0, len(final_players), 2):
        if i + 1 < len(final_players):
            h, a = final_players[i], final_players[i+1]
            match_no = (i // 2) + 1
            doc_id = f"FA_GW{NEXT_GW}_Match_{match_no}"
            
            batch.set(db.collection("fixtures").document(doc_id), {
                "gameweek": NEXT_GW,
                "type": "fa_cup",
                "home": {**h, "points": 0},
                "away": {**a, "points": 0},
                "status": "upcoming",
                "tie_break_winner": None
            })
            
    batch.commit()
    print(f"🎉 GW {NEXT_GW} Semi-Final (4 Players) Created!")

if __name__ == "__main__":
    generate_next_round()
