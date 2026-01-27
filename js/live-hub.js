// ၁။ Live Hub စာမျက်နှာကို စတင်ဖန်တီးခြင်း
// ၁။ Live Hub စာမျက်နှာကို စတင်ဖန်တီးခြင်း
window.renderLiveHub = function() {
    const mainRoot = document.getElementById('main-root');
    if (!mainRoot) return;

    mainRoot.innerHTML = `
        <div style="padding: 15px; max-width: 600px; margin: 0 auto; font-family: 'Inter', sans-serif;">
            <div style="display: flex; justify-content: center; gap: 10px; margin-bottom: 25px;">
                <button id="nav-league" onclick="window.loadFixtures('league')" 
                    style="flex: 1; background:#D4AF37; color:black; border-radius: 50px; padding: 12px; font-weight:800; border:none; cursor:pointer; font-size: 0.8rem; transition: 0.3s;">
                    LEAGUE
                </button>
                <button id="nav-fa" onclick="window.loadFixtures('fa_cup')" 
                    style="flex: 1; background:#222; color:#888; border-radius: 50px; padding: 12px; font-weight:800; border:none; cursor:pointer; font-size: 0.8rem; transition: 0.3s;">
                    FA CUP
                </button>
            </div>
            <div id="live-content">
                <div class="loading" style="text-align:center; color:#555; padding-top:50px;">🎮 Loading Matches...</div>
            </div>
        </div>
    `;
    window.loadFixtures('league');
};

// ၂။ Fixtures များကို ဆွဲထုတ်ပြီး ပြသခြင်း
window.loadFixtures = function(type) {
    const content = document.getElementById('live-content');
    const navLeague = document.getElementById('nav-league');
    const navFA = document.getElementById('nav-fa');
    if (!content) return;

    if (type === 'league') {
        navLeague.style.background = '#D4AF37'; navLeague.style.color = '#000';
        navFA.style.background = '#222'; navFA.style.color = '#888';
    } else {
        navFA.style.background = '#00ff88'; navFA.style.color = '#000';
        navLeague.style.background = '#222'; navLeague.style.color = '#888';
    }

    content.innerHTML = `<div style="text-align:center; padding:50px; color:#555;">⌛ Fetching Data...</div>`;

    db.collection("fixtures")
      .where("type", "==", type)
      .onSnapshot((fixturesSnapshot) => {
        if (fixturesSnapshot.empty) {
            content.innerHTML = `<div style="padding:50px; text-align:center; color:#444; font-weight:800;">NO FIXTURES FOUND</div>`;
            return;
        }

        db.collection("tw_mm_tournament").onSnapshot((rankSnapshot) => {
            let scores = {};
            rankSnapshot.forEach(doc => {
                scores[doc.id] = doc.data().gw_points || 0;
            });

            let html = `<h2 style="color:#D4AF37; font-size:0.8rem; letter-spacing:1px; margin-bottom:15px; text-transform:uppercase; text-align:center; opacity:0.8;">
                            ${type === 'league' ? 'H2H League Standings' : 'TW FA Cup Tournament'}
                        </h2>`;

            fixturesSnapshot.forEach(doc => {
                const f = doc.data();
                const homePts = scores[f.home.id] || 0;
                const awayPts = scores[f.away.id] || 0;

                const homeStyle = homePts > awayPts ? "color:#00ff88; font-weight:900;" : "color:#fff;";
                const awayStyle = awayPts > homePts ? "color:#00ff88; font-weight:900;" : "color:#fff;";
                
                // Division Label ကို ပိုလင်းအောင်နဲ့ ပိုစစ်ဆေးရလွယ်အောင် ပြင်ခြင်း
                let divisionDisplay = "";
                if (type === 'league') {
                    const divName = (f.division || "A").toUpperCase(); // Division အမြဲ စာလုံးကြီးပြမယ်
                    divisionDisplay = `<span style="background: rgba(212,175,55,0.1); color: #D4AF37; padding: 2px 8px; border-radius: 4px; border: 1px solid rgba(212,175,55,0.3);">DIV: ${divName}</span>`;
                } else {
                    divisionDisplay = `<span style="background: rgba(0,255,136,0.1); color: #00ff88; padding: 2px 8px; border-radius: 4px; border: 1px solid rgba(0,255,136,0.3);">TW FA CUP</span>`;
                }

                html += `
                    <div style="background:#111; border-radius:16px; padding:18px; margin-bottom:12px; border: 1px solid #222; position:relative;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:15px; font-size:0.65rem; font-weight:800; text-transform:uppercase;">
                            <span style="color:#666;">GAMWEEK ${f.gameweek || '??'}</span>
                            ${divisionDisplay}
                        </div>

                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div style="flex:1; text-align:center;">
                                <div style="font-size:0.85rem; margin-bottom:4px; ${homeStyle}">${f.home.name}</div>
                                <div style="font-size:0.65rem; color:#555;">${f.home.manager}</div>
                            </div>

                            <div style="display:flex; align-items:center; background:#1a1a1a; padding:8px 15px; border-radius:10px; border: 1px solid #333; margin:0 15px;">
                                <span style="font-size:1.3rem; font-weight:900; ${homeStyle}">${homePts}</span>
                                <span style="color:#444; margin:0 10px; font-weight:bold;">:</span>
                                <span style="font-size:1.3rem; font-weight:900; ${awayStyle}">${awayPts}</span>
                            </div>

                            <div style="flex:1; text-align:center;">
                                <div style="font-size:0.85rem; margin-bottom:4px; ${awayStyle}">${f.away.name}</div>
                                <div style="font-size:0.65rem; color:#555;">${f.away.manager}</div>
                            </div>
                        </div>
                    </div>
                `;
            });
            content.innerHTML = html;
        }
                                                    );
    });
};
