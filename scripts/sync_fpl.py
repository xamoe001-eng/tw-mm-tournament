import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os, json

def initialize_firebase():
    if not firebase_admin._apps:
        sa_info = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
        cred = credentials.Certificate(json.loads(sa_info)) if sa_info else credentials.Certificate('serviceAccountKey.json')
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firebase()
FPL_API = "https://fantasy.premierleague.com/api/"

# ⚠️ အပတ်စဉ် ပြောင်းပေးရန် (ဥပမာ- ၂၃ ပွဲကစားနေချိန် ၂၃ ထားပါ၊ ၂၃ ပြီးလို့ ၂၄ စရင် ၂၄ ပြောင်းပါ)
CURRENT_GW = 23  

def get_detailed_stats(entry_id, gw_num):
    """ Net Points နှင့် Tie-break အတွက် လိုအပ်သော stats များကိုယူသည် """
    try:
        url = f"{FPL_API}entry/{entry_id}/event/{gw_num}/picks/"
        res = requests.get(url, timeout=15).json()
        
        # Net Points = Total Points - Transfer Cost
        net_pts = res['entry_history']['points'] - res['entry_history']['event_transfers_cost']
        
        # Captain, Vice, GK ID များရှာခြင်း
        picks = res['picks']
        cap_id = next(p for p in picks if p['is_captain'])['element']
        vice_id = next(p for p in picks if p['is_vice_captain'])['element']
        gk_id = next(p for p in picks if p['position'] == 1)['element']

        def fetch_pts(p_id):
            p_res = requests.get(f"{FPL_API}element-summary/{p_id}/").json()
            return next(e['event_points'] for e in p_res['history'] if e['event'] == gw_num)

        return {
            "net_pts": net_pts,
            "cap_pts": fetch_pts(cap_id),
            "vice_pts": fetch_pts(vice_id),
            "gk_pts": fetch_pts(gk_id)
        }
    except Exception as e:
        print(f"⚠️ Error fetching stats for {entry_id}: {e}")
        return {"net_pts": 0, "cap_pts": 0, "vice_pts": 0, "gk_pts": 0}

def sync_fpl():
    print(f"--- 🔄 Syncing GW {CURRENT_GW} (League & FA Cup) ---")
    
    # ၁။ အပတ်ကူးမကူး စစ်ဆေးခြင်း
    # (တကယ်လို့ လက်ရှိ GW က Database ထဲက နောက်ဆုံး Sync ထားတဲ့ GW ထက် ကြီးနေရင် finalize လုပ်မယ်)
    sample_doc = db.collection("tw_mm_tournament").limit(1).get()[0].to_dict()
    last_gw_in_db = sample_doc.get('last_synced_gw', 0)
    
    # အပတ်အသစ်ရောက်ပြီဆိုရင် Finalize လုပ်ဖို့ flag ထောင်မယ်
    should_finalize = (CURRENT_GW > last_gw_in_db and last_gw_in_db != 0)

    # ၂။ FA Cup (fixtures collection) ကို Update လုပ်ခြင်း
    fa_fixtures = db.collection("fixtures").where("gameweek", "==", CURRENT_GW).stream()
    
    for f_doc in fa_fixtures:
        f = f_doc.to_dict()
        h_id, a_id = str(f['home']['id']), str(f['away']['id'])
        h_s = get_detailed_stats(h_id, CURRENT_GW)
        a_s = get_detailed_stats(a_id, CURRENT_GW)
        
        # Winner ဆုံးဖြတ်ခြင်း Logic (Tie-break ပါဝင်သည်)
        winner = None
        if h_s['net_pts'] > a_s['net_pts']:
            winner = h_id
        elif a_s['net_pts'] > h_s['net_pts']:
            winner = a_id
        else: # Tie-break: Cap > VCap > GK
            if h_s['cap_pts'] != a_s['cap_pts']:
                winner = h_id if h_s['cap_pts'] > a_s['cap_pts'] else a_id
            elif h_s['vice_pts'] != a_s['vice_pts']:
                winner = h_id if h_s['vice_pts'] > a_s['vice_pts'] else a_id
            else:
                winner = h_id if h_s['gk_pts'] >= a_s['gk_pts'] else a_id

        # Live Update လုပ်ခြင်း
        db.collection("fixtures").document(f_doc.id).update({
            "home.points": h_s['net_pts'],
            "away.points": a_s['net_pts'],
            "status": "live",
            "tie_break_winner": winner,
            "internal_tie_break": {
                "home": {"cap": h_s['cap_pts'], "vice": h_s['vice_pts'], "gk": h_s['gk_pts']},
                "away": {"cap": a_s['cap_pts'], "vice": a_s['vice_pts'], "gk": a_s['gk_pts']}
            }
        })

    # ၃။ League Table (tw_mm_tournament) ကို Update လုပ်ခြင်း
    managers = db.collection("tw_mm_tournament").stream()
    for m in managers:
        s = get_detailed_stats(m.id, CURRENT_GW)
        
        # အပတ်ကူးသွားပြီဆိုရင် အမှတ်ဟောင်းကို အရင်ပေါင်းမယ်
        if should_finalize:
            # အရင်အပတ် (last_gw_in_db) ရဲ့ stats ကို ပြန်ယူပြီး total ထဲပေါင်းထည့်
            old_stats = get_detailed_stats(m.id, last_gw_in_db)
            db.collection("tw_mm_tournament").document(m.id).update({
                "tournament_total_net_points": firestore.Increment(old_stats['net_pts'])
            })
            
            # အရင်အပတ်က FA ပွဲစဉ်တွေကို status: completed ပြောင်းသည်
            old_fixtures = db.collection("fixtures").where("gameweek", "==", last_gw_in_db).stream()
            for old_f in old_fixtures:
                db.collection("fixtures").document(old_f.id).update({"status": "completed"})

        # လက်ရှိ GW အတွက် live အမှတ်ကို update လုပ်မယ်
        db.collection("tw_mm_tournament").document(m.id).update({
            "gw_live_points": s['net_pts'],
            "last_synced_gw": CURRENT_GW
        })

    if should_finalize:
        print(f"✅ GW {last_gw_in_db} finalized and points added to total.")
    
    print(f"🏁 GW {CURRENT_GW} Sync Success!")

if __name__ == "__main__":
  
    sync_fpl()
