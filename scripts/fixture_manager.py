import firebase_admin
from firebase_admin import credentials, firestore
import random

def initialize_firebase():
    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.Certificate('serviceAccountKey.json'))
    return firestore.client()

db = initialize_firebase()
PREVIOUS_GW = 23 # ပြီးသွားသော GW
NEXT_GW = 24     # ထုတ်မည့် GW

def generate_next_fa_round():
    print(f"🏆 Generating FA Cup Fixtures for GW {NEXT_GW}...")
    fa_ref = db.collection("fixtures").where("gameweek", "==", PREVIOUS_GW).where("type", "==", "fa_cup").stream()
    
    winners = []
    for doc in fa_ref:
        f = doc.to_dict()
        w_id = f.get("tie_break_winner")
        if w_id:
            winners.append(f['home'] if str(f['home']['id']) == w_id else f['away'])

    if len(winners) < 2:
        print("❌ Winners မလုံလောက်ပါ သို့မဟုတ် Sync မပြီးသေးပါ။"); return

    random.shuffle(winners)
    batch = db.batch()
    for i in range(0, len(winners), 2):
        if i + 1 < len(winners):
            h, a = winners[i], winners[i+1]
            f_ref = db.collection("fixtures").document(f"FA_GW{NEXT_GW}_Match_{(i//2)+1}")
            batch.set(f_ref, {
                "gameweek": NEXT_GW, "type": "fa_cup", "division": "FA_CUP",
                "home": {**h, "points": 0}, "away": {**a, "points": 0},
                "status": "upcoming", "tie_break_winner": None
            })
    batch.commit()
    print(f"🎉 Success: GW {NEXT_GW} FA Cup Fixtures Created!")

if __name__ == "__main__":
    generate_next_fa_round()
