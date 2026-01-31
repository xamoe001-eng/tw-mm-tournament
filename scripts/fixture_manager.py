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

# ⚠️ GW 23 အပြီး winners များကိုယူ၍ GW 24 ပွဲစဉ်သစ်များ ထုတ်ပြန်မည်
PREVIOUS_GW = 23
NEXT_GW = 24

def generate_next_round():
    print(f"🏆 GW {PREVIOUS_GW} Winners များကို စစ်ဆေး၍ GW {NEXT_GW} ပွဲစဉ်များ ထုတ်ပြန်နေသည်...")
    
    # ၁။ အရင်အပတ် (GW 23) က FA Cup ပွဲစဉ်များကို ဆွဲယူခြင်း
    fa_ref = db.collection("fixtures") \
               .where("gameweek", "==", PREVIOUS_GW) \
               .where("type", "==", "FA_CUP").stream()
    
    winners = []
    match_found = False

    for doc in fa_ref:
        match_found = True
        f = doc.to_dict()
        winner_id = str(f.get("tie_break_winner"))
        
        # Winner ID မရှိသေးလျှင် (Sync မလုပ်ရသေးလျှင်) ကျော်သွားမည်
        if not winner_id or winner_id == "None":
            print(f"⚠️ သတိပေးချက်: Match {f.get('match_id')} တွင် Winner မသတ်မှတ်ရသေးပါ။ Sync အရင်လုပ်ပါ။")
            continue

        # Winner data ကို ဆွဲထုတ်ခြင်း
        if str(f['home']['id']) == winner_id:
            winners.append(f['home'])
        else:
            winners.append(f['away'])

    if not match_found or len(winners) == 0:
        print(f"❌ GW {PREVIOUS_GW} အတွက် ပွဲစဉ်များ သို့မဟုတ် Winners များ ရှာမတွေ့ပါ။")
        return

    # ၂။ GW 24 အတွက် (၂၄ ယောက် - ၁၂ ပွဲ) - Lucky Loser မလိုအပ်သေးပါ
    final_players = winners.copy()
    
    print(f"✅ စုစုပေါင်း ကစားသမား {len(final_players)} ဦးဖြင့် GW {NEXT_GW} တွဲဆိုင်းအသစ်များ ပြုလုပ်နေသည်...")

    # ၃။ Random Shuffle ဖြင့် ပွဲစဉ်အသစ် တွဲခြင်း
    random.shuffle(final_players)
    batch = db.batch()
    
    # ၂ ယောက် တစ်တွဲ တွဲမည်
    for i in range(0, len(final_players), 2):
        if i + 1 < len(final_players):
            h, a = final_players[i], final_players[i+1]
            match_no = (i // 2) + 1
            doc_id = f"FA_GW{NEXT_GW}_Match_{match_no:02d}"
            
            # Website Structure အတိုင်း Fixture အသစ် သတ်မှတ်ခြင်း
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
    print(f"🎉 Success: GW {NEXT_GW} အတွက် ပွဲစဉ်သစ် {len(final_players)//2} ပွဲကို Firebase ထဲသို့ ထည့်သွင်းပြီးပါပြီ။")

if __name__ == "__main__":
    generate_next_round()
