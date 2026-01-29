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
                <div style="text-align:center; color:#555; padding-top:50px;">🎮 Initializing...</div>
            </div>
        </div>
    `;
    window.loadFixtures('league');
};

window.loadFixtures = function(type) {
    const content = document.getElementById('live-content');
    const navLeague = document.getElementById('nav-league');
    const navFA = document.getElementById('nav-fa');
    if (!content) return;

    const isLeague = type === 'league';
    navLeague.style.background = isLeague ? '#D4AF37' : '#222';
    navLeague.style.color = isLeague ? '#000' : '#888';
    navFA.style.background = !isLeague ? '#00ff88' : '#222';
    navFA.style.color = !isLeague ? '#000' : '#888';

    content.innerHTML = `<div style="text-align:center; padding:50px; color:#555;">⌛ Fetching Real-time Data...</div>`;

    // Fixtures နှင့် Live Points များကို ချိတ်ဆက်ခြင်း
    db.collection("fixtures")
      .where("type", "==", type)
      .onSnapshot((fixturesSnapshot) => {
        
        db.collection("tw_mm_tournament").onSnapshot((rankSnapshot) => {
            let liveScores = {};
            rankSnapshot.forEach(doc => { 
                // Python sync_tournament တွင် သုံးထားသော gw_live_points ကို ဖတ်သည်
                liveScores[doc.id] = doc.data().gw_live_points || 0; 
            });

            if (fixturesSnapshot.empty) {
                content.innerHTML = `<div style="padding:50px; text-align:center; color:#444; font-weight:800;">NO FIXTURES FOUND</div>`;
                return;
            }

            let html = `<h2 style="color:#444; font-size:0.65rem; letter-spacing:2px; margin-bottom:20px; text-transform:uppercase; text-align:center;">
                            ${isLeague ? 'H2H League Season' : 'TW FA Cup Tournament'}
                        </h2>`;

            // Gameweek အလိုက် စီခြင်း
            const sortedDocs = fixturesSnapshot.docs.sort((a, b) => a.data().gameweek - b.data().gameweek);

            sortedDocs.forEach(doc => {
                const f = doc.data();
                const isCompleted = f.status === "completed";
                const isLive = f.status === "live";

                // အမှတ်များကို သတ်မှတ်ခြင်း (Completed ဆိုလျှင် Fixture ထဲမှယူ၊ Live ဆိုလျှင် Tournament ထဲမှယူ)
                const hPts = isCompleted ? (f.home.points || 0) : (liveScores[f.home.id] || 0);
                const aPts = isCompleted ? (f.away.points || 0) : (liveScores[f.away.id] || 0);

                const hWin = hPts > aPts;
                const aWin = aPts > hPts;
                
                let statusBadge = isCompleted 
                    ? `<span style="background:#222; color:#555; padding:2px 8px; border-radius:4px; font-size:0.55rem; font-weight:900;">FINAL</span>`
                    : (isLive 
                        ? `<span style="background:rgba(0,255,136,0.1); color:#00ff88; border:1px solid rgba(0,255,136,0.3); padding:2px 8px; border-radius:4px; font-size:0.55rem; font-weight:900;">LIVE</span>`
                        : `<span style="color:#444; border:1px solid #222; padding:2px 8px; border-radius:4px; font-size:0.55rem; font-weight:900;">UPCOMING</span>`);

                const divTag = isLeague 
                    ? `<span style="color:#D4AF37; margin-left:8px; opacity:0.8;">${f.division || "Division A"}</span>`
                    : `<span style="color:#00ff88; margin-left:8px; opacity:0.8;">FA CUP</span>`;

                html += `
                    <div style="background:linear-gradient(145deg, #111, #080808); border-radius:18px; padding:20px; margin-bottom:15px; border: 1px solid #1a1a1a; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:18px; font-size:0.6rem; font-weight:800; text-transform:uppercase;">
                            <div style="color:#888;">GW ${f.gameweek}${divTag}</div>
                            ${statusBadge}
                        </div>

                        <div style="display:flex; align-items:center; justify-content:space-between; gap:10px;">
                            <div style="flex:1; display:flex; flex-direction:column; align-items:center; min-width:0;">
                                <div style="font-size:0.85rem; font-weight:800; color:${hWin ? '#00ff88' : '#fff'}; text-align:center; overflow:hidden; text-overflow:ellipsis; width:100%; white-space:nowrap; margin-bottom:4px;">
                                    ${f.home.team || 'Team'}
                                </div>
                                <div style="font-size:0.6rem; color:#555; overflow:hidden; text-overflow:ellipsis; width:100%; text-align:center; white-space:nowrap;">
                                    ${f.home.name}
                                </div>
                            </div>

                            <div style="display:grid; grid-template-columns: 1fr auto 1fr; align-items:center; background:#000; padding:10px 14px; border-radius:12px; border:1px solid #222; min-width:85px;">
                                <div style="font-size:1.3rem; font-weight:900; text-align:right; color:${hWin ? '#00ff88' : '#fff'};">
                                    ${f.status === 'upcoming' ? '-' : hPts}
                                </div>
                                <div style="font-size:0.8rem; color:#333; font-weight:900; padding:0 8px;">:</div>
                                <div style="font-size:1.3rem; font-weight:900; text-align:left; color:${aWin ? '#00ff88' : '#fff'};">
                                    ${f.status === 'upcoming' ? '-' : aPts}
                                </div>
                            </div>

                            <div style="flex:1; display:flex; flex-direction:column; align-items:center; min-width:0;">
                                <div style="font-size:0.85rem; font-weight:800; color:${aWin ? '#00ff88' : '#fff'}; text-align:center; overflow:hidden; text-overflow:ellipsis; width:100%; white-space:nowrap; margin-bottom:4px;">
                                    ${f.away.team || 'Team'}
                                </div>
                                <div style="font-size:0.6rem; color:#555; overflow:hidden; text-overflow:ellipsis; width:100%; text-align:center; white-space:nowrap;">
                                    ${f.away.name}
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
            content.innerHTML = html;
      
        });
    });
};
