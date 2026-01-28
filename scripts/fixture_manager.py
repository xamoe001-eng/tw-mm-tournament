# fixture_manager.py ထဲက အဓိကအပိုင်း
def generate_next_fa_round(past_gw, next_gw):
    winners = []
    # ၁။ ပြီးခဲ့တဲ့အပတ်က FA ရလဒ်တွေထဲက နိုင်တဲ့သူကို ရှာမယ်
    docs = db.collection("fixtures_history_fa").where("gameweek", "==", past_gw).stream()
    
    for doc in docs:
        f = doc.to_dict()
        if f['home']['points'] > f['away']['points']: winners.append(f['home'])
        elif f['away']['points'] > f['home']['points']: winners.append(f['away'])
        else: winners.append(random.choice([f['home'], f['away']])) # သရေကျရင် random

    # ၂။ နိုင်တဲ့သူတွေကို တွဲပြီး ပွဲစဉ်သစ်ထုတ်မယ်
    random.shuffle(winners)
    for i in range(0, len(winners), 2):
        if i+1 < len(winners):
            h, a = winners[i], winners[i+1]
            f_id = f"FA_GW{next_gw}_Match_{i//2 + 1}"
            db.collection("fixtures").document(f_id).set({
                "gameweek": next_gw,
                "type": "fa_cup",
                "division": "FA_CUP",
                "home": {**h, "points": 0},
                "away": {**a, "points": 0},
                "status": "upcoming"
            })
          
