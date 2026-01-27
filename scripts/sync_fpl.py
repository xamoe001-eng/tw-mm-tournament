import requests
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

# ၁။ Firebase ချိတ်ဆက်ခြင်း
def initialize_firebase():
    if not firebase_admin._apps:
        cred_path = os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json')
        if not os.path.exists(cred_path):
            cred_path = 'serviceAccountKey.json'
        try:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            print(f"Error: Firebase Key file missing. {e}")
            return None
    return firestore.client()

db = initialize_firebase()

# ၂။ Configuration
LEAGUE_ID = "400231"
FPL_API = "https://fantasy.premierleague.com/api/"
TOTAL_OFFICIALS = 48 
START_GW = 23 # 👈 တစ်ပတ်ချင်းစီအတွက် ဒီမှာ Gameweek ပြောင်းပေးပါ

def sync_data():
    if not db: return
    print(f"--- 🚀 FPL Tournament Sync Started: GW {START_GW} ---")
    
    try:
        r = requests.get(f"{FPL_API}leagues-classic/{LEAGUE_ID}/standings/")
        r.raise_for_status()
        all_players = r.json()['standings']['results']
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    # Fixtures ဖတ်ခြင်း (Live Hub အတွက် လက်ရှိ GW ပွဲစဉ်များ)
    fixtures_data = {}
    try:
        f_ref = db.collection("fixtures").where("gameweek", "==", START_GW).stream()
        fixtures_data = {f.id: f.to_dict() for f in f_ref}
    except: pass

    batch = db.batch()
    players_for_history = []

    for player in all_players:
        entry_id = str(player['entry'])
        
        # Net Points တွက်ချက်ခြင်း (-4 hit နှုတ်ပြီးသား)
        transfer_cost = player.get('event_transfers_cost', 0)
        net_gw_points = player['event_total'] - transfer_cost

        # H2H Logic (ပတ်စဉ် နိုင်/ရှုံး တွက်ရန်)
        played, wins, draws, losses, h2h_points = 0, 0, 0, 0, 0
        
        # လက်ရှိအသင်း၏ Fixture ရှိမရှိစစ်ဆေးခြင်း
        active_fixture = None
        for fid, f in fixtures_data.items():
            if f['home']['id'] == player['entry'] or f['away']['id'] == player['entry']:
                active_fixture = f
                break

        if active_fixture:
            is_home = active_fixture['home']['id'] == player['entry']
            opp_id = active_fixture['away']['id'] if is_home else active_fixture['home']['id']
            opp_player = next((p for p in all_players if p['entry'] == opp_id), None)
            
            if opp_player:
                opp_net = opp_player['event_total'] - opp_player.get('event_transfers_cost', 0)
                if active_fixture['type'] == 'league':
                    played = 1
                    if net_gw_points > opp_net: wins, h2h_points = 1, 3
                    elif net_gw_points == opp_net: draws, h2h_points = 1, 1
                    else: losses = 1

        # ၃။ Database သို့ သိမ်းဆည်းမည့် Data
        # firestore.Increment ကို သုံး၍ ၇ ပတ်စာ အမှတ်များကို ပေါင်းသွားမည်
        data = {
            "fpl_id": player['entry'],
            "manager_name": player['player_name'],
            "team_name": player['entry_name'],
            "played": firestore.Increment(played),
            "wins": firestore.Increment(wins),
            "draws": firestore.Increment(draws),
            "losses": firestore.Increment(losses),
            "h2h_points": firestore.Increment(h2h_points),
            "tournament_total_net_points": firestore.Increment(net_gw_points), # ၇ ပတ်စာရမှတ်ပေါင်း
            "fpl_total_points": player['total'], # Overall Season (Tie-breaker)
            "last_gw_points": net_gw_points,
            "last_updated": firestore.SERVER_TIMESTAMP
        }

        doc_ref = db.collection("tw_mm_tournament").document(entry_id)
        batch.set(doc_ref, data, merge=True)
        players_for_history.append({**data, "entry": player['entry']})

    # ၄။ History သိမ်းဆည်းခြင်းနှင့် Live Update ထုတ်ခြင်း
    if players_for_history:
        archive_fixtures(players_for_history, fixtures_data)

    # ၅။ GW 29 Auto Promotion/Relegation (၇ ပတ်မြောက်မှ အလုပ်လုပ်မည်)
    if START_GW == 29:
        handle_promotion_relegation()

    batch.commit()
    print(f"✅ Sync Success for GW {START_GW}")

def archive_fixtures(players_data, fixtures_data):
    """League နှင့် FA Cup History ကို ခွဲသိမ်းပြီး Live Update လုပ်ပေးခြင်း"""
    for fid, f in fixtures_data.items():
        h_p = next((p for p in players_data if p['entry'] == f['home']['id']), None)
        a_p = next((p for p in players_data if p['entry'] == f['away']['id']), None)

        if h_p and a_p:
            payload = {
                "fixture_id": fid,
                "gameweek": START_GW,
                "type": f['type'],
                "division": f.get('division', 'Mixed'),
                "home": {**f['home'], "points": h_p['last_gw_points']},
                "away": {**f['away'], "points": a_p['last_gw_points']},
                "status": "completed"
            }
            
            # ၁။ Live Update (Live Hub အတွက်)
            db.collection("fixtures").document(fid).set(payload, merge=True)
            
            # ၂။ League History (GW အလိုက် ခွဲသိမ်းသည်)
            if f['type'] == 'league':
                db.collection(f"fixtures_history_gw_{START_GW}").document(fid).set(payload, merge=True)
            
            # ၃။ FA Cup History (သီးသန့် စုသိမ်းသည်)
            if f['type'] == 'fa_cup':
                db.collection("fixtures_history_fa").document(f"gw_{START_GW}_{fid}").set(payload, merge=True)

def handle_promotion_relegation():
    """GW 29 တွင် တန်းတက်/တန်းဆင်း ၄ သင်းစီ Auto ပြုလုပ်ပေးခြင်း"""
    print("🔄 Processing Final Promotion/Relegation...")
    teams = [d.to_dict() for d in db.collection("tw_mm_tournament").stream()]

    # Tie-breaker Ranking Logic
    def rank_val(x):
        return (x.get('h2h_points', 0), x.get('tournament_total_net_points', 0), x.get('fpl_total_points', 0))

    div_a = sorted([t for t in teams if t.get('league_tag') == 'A'], key=rank_val, reverse=True)
    div_b = sorted([t for t in teams if t.get('league_tag') == 'B'], key=rank_val, reverse=True)

    # Div A အောက်ဆုံး ၄ သင်း -> B သို့ ဆင်း
    for t in div_a[-4:]:
        db.collection("tw_mm_tournament").document(str(t['fpl_id'])).update({"league_tag": "B", "status": "Relegated"})
    
    # Div B အပေါ်ဆုံး ၄ သင်း -> A သို့ တက်
    for t in div_b[:4]:
        db.collection("tw_mm_tournament").document(str(t['fpl_id'])).update({"league_tag": "A", "status": "Promoted"})

if __name__ == "__main__":
    sync_data()
