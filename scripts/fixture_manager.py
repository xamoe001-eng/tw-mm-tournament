import firebase_admin
from firebase_admin import credentials, firestore
import os, json, random

def initialize_firebase():
    if not firebase_admin._apps:
        # GitHub Secrets သို့မဟုတ် Local Key ဖိုင် စစ်ဆေးခြင်း
        sa_info = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        if sa_info:
            cred = credentials.Certificate(json.loads(sa_info))
        else:
            cred = credentials.Certificate('serviceAccountKey.json')
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firebase()

# ⚠️ အပတ်စဉ်အလိုက် ပြောင်းလဲသတ်မှတ်ရန်
PREVIOUS_GW = 26
NEXT_GW = 27

def generate_next_round():
    print(f"🏆 GW {PREVIOUS_GW} ရလဒ်များကို စစ်ဆေး၍ GW {NEXT_GW} ပွဲစဉ်များ ထုတ်ပြန်နေသည်...")
    
    # ၁။ အရင်အပတ်က FA Cup ပွဲစဉ်များကို ဆွဲယူခြင်း
    fa_ref = db.collection("fixtures") \
               .where("gameweek", "==", PREVIOUS_GW) \
               .where("type", "==", "FA_CUP").stream()
    
    winners = []
    losers = []
    match_found = False

    for doc in fa_ref:
        match_found = True
        f = doc.to_dict()
        winner_id = str(f.get("tie_break_winner"))
        
        # Player data များကို Points ပါဝင်အောင် စုစည်းခြင်း
        home_player = {**f['home'], "points": f['home'].get('points', 0)}
        away_player = {**f['away'], "points": f['away'].get('points', 0)}

        # Winner နှင့် Loser ခွဲခြားခြင်း (Sync Code က ဆုံးဖြတ်ထားသော winner_id ကို သုံးသည်)
        if str(f['home']['id']) == winner_id:
            winners.append(home_player)
            losers.append(away_player)
        else:
            winners.append(away_player)
            losers.append(home_player)

    if not match_found:
        print(f"❌ GW {PREVIOUS_GW} အတွက် ပွဲစဉ်များ ရှာမတွေ့ပါ။ Sync အရင်လုပ်ရန် လိုအပ်သည်။")
        return

    # ၂။ Lucky Loser Logic (GW 26 မှ GW 27 အတွက်သာ)
    final_players = winners.copy()
    if PREVIOUS_GW == 26 and len(losers) > 0:
        # ရှုံးတဲ့သူတွေထဲက Net Points အများဆုံး တစ်ယောက်ကို ရွေးသည်
        lucky_loser = sorted(losers, key=lambda x: x.get('points', 0), reverse=True)[0]
        final_players.append(lucky_loser)
        print(f"✨ Lucky Loser ရွေးချယ်မှု: {lucky_loser['name']} ({lucky_loser['points']} pts)")

    print(f"✅ စုစုပေါင်း ကစားသမား {len(final_players)} ဦးဖြင့် တွဲဆိုင်းအသစ်များ ပြုလုပ်နေသည်...")

    if len(final_players) < 2:
        print("❌ လူဦးရေ မလုံလောက်သည့်အတွက် ပွဲစဉ်ထုတ်၍ မရပါ။"); return

    # ၃။ Random Shuffle ဖြင့် ပွဲစဉ်အသစ် တွဲခြင်း
    random.shuffle(final_players)
    batch = db.batch()
    
    for i in range(0, len(final_players), 2):
        if i + 1 < len(final_players):
            h, a = final_players[i], final_players[i+1]
            match_no = (i // 2) + 1
            doc_id = f"FA_GW{NEXT_GW}_Match_{match_no:02d}"
            
            # Website ပေါ်တွင် Live အမှတ်နှင့် Tie-break ပြသရန် Structure အပြည့်အစုံ
            batch.set(db.collection("fixtures").document(doc_id), {
                "gameweek": NEXT_GW,
                "type": "FA_CUP",
                "match_id": match_no,
                "home": {
                    "id": h['id'],
                    "name": h['name'],
                    "team": h['team'],
                    "points": 0
                },
                "away": {
                    "id": a['id'],
                    "name": a['name'],
                    "team": a['team'],
                    "points": 0
                },
                "status": "upcoming",
                "tie_break_winner": None,
                "tie_break_reason": None,
                "internal_stats": {
                    "home": {"cap": 0, "vice": 0, "gk": 0},
                    "away": {"cap": 0, "vice": 0, "gk": 0}
                },
                "division": "FA_CUP"
            })
            
    batch.commit()
    print(f"🎉 Success: GW {NEXT_GW} (Semi-Final) ပွဲစဉ် ၂ ခုကို Firebase ထဲသို့ ထည့်သွင်းပြီးပါပြီ။")

if __name__ == "__main__":
    generate_next_round()
