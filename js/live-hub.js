// ၁။ Live Hub စာမျက်နှာကို စတင်ဖန်တီးခြင်း
window.renderLiveHub = function() {
    const mainRoot = document.getElementById('main-root');
    if (!mainRoot) return;

    mainRoot.innerHTML = `
        <div style="padding: 15px; max-width: 600px; margin: 0 auto; font-family: 'Inter', sans-serif; color: white;">
            <div style="display: flex; justify-content: center; gap: 10px; margin-bottom: 25px;">
                <button id="nav-league" onclick="window.loadFixtures('league')" 
                    style="flex: 1; background:#D4AF37; color:black; border-radius: 50px; padding: 12px; font-weight:800; border:none; cursor:pointer; font-size: 0.75rem; transition: 0.3s;">
                    H2H LEAGUE
                </button>
                <button id="nav-fa" onclick="window.loadFixtures('fa_cup')" 
                    style="flex: 1; background:#222; color:#888; border-radius: 50px; padding: 12px; font-weight:800; border:none; cursor:pointer; font-size: 0.75rem; transition: 0.3s;">
                    TW FA CUP
                </button>
            </div>
            
            <div id="live-content">
                <div style="text-align:center; color:#555; padding-top:50px;">🎮 Initializing Hub...</div>
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

    // UI Active State ပြောင်းလဲခြင်း
    const isLeague = type === 'league';
    navLeague.style.background = isLeague ? '#D4AF37' : '#222';
    navLeague.style.color = isLeague ? '#000' : '#888';
    navFA.style.background = !isLeague ? '#00ff88' : '#222';
    navFA.style.color = !isLeague ? '#000' : '#888';

    content.innerHTML = `<div style="text-align:center; padding:50px; color:#555;">⌛ Fetching Live Data...</div>`;

    // Fixtures နဲ့ Tournament Standings ကို တစ်ပြိုင်နက် နားထောင်ခြင်း
    db.collection("fixtures")
      .where("type", "==", type)
      .orderBy("gameweek", "asc") // GW အလိုက် စီပြမည်
      .onSnapshot((fixturesSnapshot) => {
        
        db.collection("tw_mm_tournament").onSnapshot((rankSnapshot) => {
            let liveScores = {};
            rankSnapshot.forEach(doc => { liveScores[doc.id] = doc.data().gw_points || 0; });

            if (fixturesSnapshot.empty) {
                content.innerHTML = `<div style="padding:50px; text-align:center; color:#444; font-weight:800;">NO FIXTURES SCHEDULED</div>`;
                return;
            }

            let html = `<h2 style="color:#666; font-size:0.7rem; letter-spacing:2px; margin-bottom:20px; text-transform:uppercase; text-align:center;">
                            ${isLeague ? 'H2H League Season Schedule' : 'TW FA Cup Tournament'}
                        </h2>`;

            fixturesSnapshot.forEach(doc => {
                const f = doc.data();
                
                // Logic: ပွဲပြီးသွားရင် fixture ထဲက points ကိုပြမယ်၊ မပြီးသေးရင် Live Points ကိုပြမယ်
                const isCompleted = f.status === "completed";
                const hPts = isCompleted ? (f.home.points || 0) : (liveScores[f.home.id] || 0);
                const aPts = isCompleted ? (f.away.points || 0) : (liveScores[f.away.id] || 0);

                const hStyle = hPts > aPts ? "color:#00ff88; font-weight:900;" : "color:#fff;";
                const aStyle = aPts > hPts ? "color:#00ff88; font-weight:900;" : "color:#fff;";
                
                // Status Badge Logic
                let statusBadge = "";
                if (isCompleted) {
                    statusBadge = `<span style="color:#555; border:1px solid #333; padding:2px 6px; border-radius:4px; font-size:0.55rem;">FINAL</span>`;
                } else if (f.status === "live") {
                    statusBadge = `<span style="color:#00ff88; border:1px solid #00ff88; padding:2px 6px; border-radius:4px; font-size:0.55rem; animation: pulse 1.5s infinite;">LIVE</span>`;
                } else {
                    statusBadge = `<span style="color:#888; border:1px solid #444; padding:2px 6px; border-radius:4px; font-size:0.55rem;">UPCOMING</span>`;
                }

                // Division Label
                const divTag = isLeague 
                    ? `<span style="color:#D4AF37; margin-left:10px;">DIV: ${(f.division || "A").split(' ')[1] || 'A'}</span>`
                    : `<span style="color:#00ff88; margin-left:10px;">FA CUP</span>`;

                html += `
                    <div style="background: linear-gradient(145deg, #111, #0a0a0a); border-radius:16px; padding:18px; margin-bottom:15px; border: 1px solid #222;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:15px; font-size:0.6rem; font-weight:800; opacity:0.7;">
                            <div>GW ${f.gameweek}${divTag}</div>
                            ${statusBadge}
                        </div>

                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div style="flex:1.2; text-align:center;">
                                <div style="font-size:0.8rem; margin-bottom:2px; ${hStyle} text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">
                                    ${f.home.team || 'Unknown'}
                                </div>
                                <div style="font-size:0.6rem; color:#444;">${f.home.name}</div>
                            </div>

                            <div style="display:flex; align-items:center; background:#000; padding:6px 12px; border-radius:8px; border: 1px solid #333; margin:0 10px; min-width:70px; justify-content:center;">
                                <span style="font-size:1.1rem; font-weight:900; ${hStyle}">${f.status === 'upcoming' ? '-' : hPts}</span>
                                <span style="color:#333; margin:0 6px;">:</span>
                                <span style="font-size:1.1rem; font-weight:900; ${aStyle}">${f.status === 'upcoming' ? '-' : aPts}</span>
                            </div>

                            <div style="flex:1.2; text-align:center;">
                                <div style="font-size:0.8rem; margin-bottom:2px; ${aStyle} text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">
                                    ${f.away.team || 'Unknown'}
                                </div>
                                <div style="font-size:0.6rem; color:#444;">${f.away.name}</div>
                            </div>
                        </div>
                    </div>
                `;
            });
            content.innerHTML = html;
        });
    });
};
