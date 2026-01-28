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
START_GW = 23  # 👈 Update လုပ်မည့် Gameweek

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

    # Fixtures ဖတ်ခြင်း
    fixtures_data = {}
    try:
        # START_GW ကို Number အနေနဲ့ရော String အနေနဲ့ရော စစ်ထုတ်နိုင်အောင် stream လုပ်သည်
        f_ref = db.collection("fixtures").where("gameweek", "==", START_GW).stream()
        fixtures_data = {f.id: f.to_dict() for f in f_ref}
    except Exception as e:
        print(f"Error fetching fixtures: {e}")

    batch = db.batch()
    players_for_history = []

    for player in all_players:
        entry_id = str(player['entry'])
        doc_ref = db.collection("tw_mm_tournament").document(entry_id)
        doc = doc_ref.get()
        
        current_data = doc.to_dict() if doc.exists else {}
        last_synced_gw = current_data.get("last_synced_gw", 0)

        # အမှတ်တွက်ချက်ခြင်း (-4 hit နှုတ်ပြီးသား)
        transfer_cost = player.get('event_transfers_cost', 0)
        net_gw_points = player['event_total'] - transfer_cost

        # H2H Logic Initialize
        played, wins, draws, losses, h2h_points = 0, 0, 0, 0, 0
        active_fixture = None
        
        # START_GW နဲ့ ကိုက်ညီတဲ့ ပွဲကိုရှာသည်
        for fid, f in fixtures_data.items():
            if f.get('gameweek') == START_GW:
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

        # 🛑 Duplicate Sync Protection
        if last_synced_gw < START_GW:
            update_payload = {
                "fpl_id": player['entry'],
                "manager_name": player['player_name'],
                "team_name": player['entry_name'],
                "played": firestore.Increment(played),
                "wins": firestore.Increment(wins),
                "draws": firestore.Increment(draws),
                "losses": firestore.Increment(losses),
                "h2h_points": firestore.Increment(h2h_points),
                "gw_points": net_gw_points,
                "tournament_total_net_points": firestore.Increment(net_gw_points),
                "fpl_total_points": player['total'],
                "last_synced_gw": START_GW,
                "last_updated": firestore.SERVER_TIMESTAMP
            }
            
            # 🔥 Division Tag Logic အသစ် (A နှင့် B ကို တိကျစွာ ခွဲခြားရန်)
            if active_fixture and 'division' in active_fixture:
                div_str = str(active_fixture['division']).upper()
                # Division 1 (သို့) Div 1 (သို့) A ပါရင် A လို့ သတ်မှတ်မည်
                if "1" in div_str or "A" in div_str:
                    tag = "A"
                # Division 2 (သို့) Div 2 (သို့) B ပါရင် B လို့ သတ်မှတ်မည်
                elif "2" in div_str or "B" in div_str:
                    tag = "B"
                else:
                    tag = "B" # Default
                
                update_payload["league_tag"] = tag

            batch.set(doc_ref, update_payload, merge=True)
            
            players_for_history.append({
                "entry": player['entry'], 
                "last_gw_points": net_gw_points,
                "division": active_fixture.get('division', 'Mixed') if active_fixture else 'Mixed'
            })
        else:
            # Sync လုပ်ပြီးသားသူများအတွက် league_tag ကိုပဲ update ပြန်လုပ်ပေးချင်ရင် ဒီမှာ ထည့်နိုင်သည်
            print(f"⚠️ GW {START_GW} already synced for {player['player_name']}. Skip accumulation.")

    if players_for_history:
        archive_fixtures(players_for_history, fixtures_data)

    batch.commit()
    print(f"✅ Sync Success for GW {START_GW}")

def archive_fixtures(players_data, fixtures_data):
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
                "status": "completed",
                "updated_at": firestore.SERVER_TIMESTAMP
            }
            if f['type'] == 'league':
                db.collection(f"fixtures_history_gw_{START_GW}").document(fid).set(payload, merge=True)
            if f['type'] == 'fa_cup':
                db.collection("fixtures_history_fa").document(f"gw_{START_GW}_{fid}").set(payload, merge=True)

if __name__ == "__main__":
    sync_data()
