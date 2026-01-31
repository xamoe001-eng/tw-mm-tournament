window.renderLiveHub = function() {
    const mainRoot = document.getElementById('main-root');
    if (!mainRoot) return;

    mainRoot.innerHTML = `
        <div style="padding: 15px; max-width: 600px; margin: 0 auto; font-family: 'Inter', sans-serif; color: white;">
            <div style="display: flex; justify-content: center; gap: 10px; margin-bottom: 25px;">
                <button id="nav-league" onclick="window.loadLeaderboard()" 
                    style="flex: 1; background:#D4AF37; color:black; border-radius: 50px; padding: 12px; font-weight:800; border:none; cursor:pointer; font-size: 0.75rem; transition: 0.3s;">
                    🏆 LIVE RANK (48)
                </button>
                <button id="nav-fa" onclick="window.loadFixtures('FA_CUP')" 
                    style="flex: 1; background:#222; color:#888; border-radius: 50px; padding: 12px; font-weight:800; border:none; cursor:pointer; font-size: 0.75rem; transition: 0.3s;">
                    🏟️ TW FA CUP
                </button>
            </div>
            <div id="live-content">
                <div style="text-align:center; color:#555; padding-top:50px;">🎮 Initializing...</div>
            </div>
        </div>
    `;
    window.loadLeaderboard(); // ပထမဆုံးဖွင့်လျှင် Rank အရင်ပြမည်
};

// --- ၁။ ၄၈ သင်း Live Rank ပြသပေးမည့် Function ---
window.loadLeaderboard = function() {
    const content = document.getElementById('live-content');
    const navLeague = document.getElementById('nav-league');
    const navFA = document.getElementById('nav-fa');
    
    navLeague.style.background = '#D4AF37'; navLeague.style.color = '#000';
    navFA.style.background = '#222'; navFA.style.color = '#888';

    content.innerHTML = `<div style="text-align:center; padding:50px; color:#555;">⌛ Fetching Top 48 Live Points...</div>`;

    db.collection("tw_mm_tournament").onSnapshot((snapshot) => {
        let players = [];
        snapshot.forEach(doc => players.push(doc.data()));

        // Points အများဆုံးလူကို ထိပ်ဆုံးကထား၍ စီမည်
        players.sort((a, b) => (b.gw_live_points || 0) - (a.gw_live_points || 0));

        let html = `<h2 style="color:#444; font-size:0.65rem; letter-spacing:2px; margin-bottom:20px; text-transform:uppercase; text-align:center;">
                        Top 48 Live Leaderboard
                    </h2>`;

        players.forEach((p, index) => {
            const rank = index + 1;
            const rankColor = rank === 1 ? '#D4AF37' : (rank <= 3 ? '#C0C0C0' : '#444');
            
            html += `
                <div style="background:#111; border-radius:12px; padding:12px 18px; margin-bottom:8px; display:flex; align-items:center; border:1px solid #1a1a1a;">
                    <div style="width:30px; font-weight:900; color:${rankColor}; font-size:0.9rem;">${rank}</div>
                    <div style="flex:1; margin-left:10px;">
                        <div style="font-size:0.8rem; font-weight:800; color:#fff;">${p.team}</div>
                        <div style="font-size:0.6rem; color:#555;">${p.name} • <span style="color:#D4AF37;">${p.division}</span></div>
                    </div>
                    <div style="background:#000; padding:6px 12px; border-radius:8px; border:1px solid #222; text-align:center; min-width:45px;">
                        <div style="font-size:0.9rem; font-weight:900; color:#00ff88;">${p.gw_live_points || 0}</div>
                        <div style="font-size:0.45rem; color:#444; font-weight:800;">PTS</div>
                    </div>
                </div>
            `;
        });
        content.innerHTML = html;
    });
};

// --- ၂။ FA Cup Fixtures ပြသပေးမည့် Function (မူလ Logic မပျက်) ---
window.loadFixtures = function(type) {
    const content = document.getElementById('live-content');
    const navLeague = document.getElementById('nav-league');
    const navFA = document.getElementById('nav-fa');

    navLeague.style.background = '#222'; navLeague.style.color = '#888';
    navFA.style.background = '#00ff88'; navFA.style.color = '#000';

    content.innerHTML = `<div style="text-align:center; padding:50px; color:#555;">⌛ Fetching FA Cup Brackets...</div>`;

    db.collection("fixtures").where("type", "==", type).onSnapshot((fixturesSnapshot) => {
        db.collection("tw_mm_tournament").onSnapshot((rankSnapshot) => {
            let liveScores = {};
            rankSnapshot.forEach(doc => { liveScores[doc.id] = doc.data().gw_live_points || 0; });

            let html = `<h2 style="color:#444; font-size:0.65rem; letter-spacing:2px; margin-bottom:20px; text-transform:uppercase; text-align:center;">
                            TW FA Cup Tournament
                        </h2>`;

            const sortedDocs = fixturesSnapshot.docs.sort((a, b) => a.id.localeCompare(b.id, undefined, {numeric: true}));

            sortedDocs.forEach(doc => {
                const f = doc.data();
                const isCompleted = f.status === "completed";
                const isLive = f.status === "live";

                const hPts = (isLive || !isCompleted) ? (liveScores[f.home.id] || 0) : (f.home.points || 0);
                const aPts = (isLive || !isCompleted) ? (liveScores[f.away.id] || 0) : (f.away.points || 0);

                const winnerId = f.tie_break_winner ? String(f.tie_break_winner) : null;
                const hWin = winnerId ? (String(f.home.id) === winnerId) : (hPts > aPts);
                const aWin = winnerId ? (String(f.away.id) === winnerId) : (aPts > hPts);
                
                let statusBadge = isCompleted 
                    ? `<span style="background:#222; color:#555; padding:2px 8px; border-radius:4px; font-size:0.55rem; font-weight:900;">FINAL</span>`
                    : (isLive 
                        ? `<span style="background:rgba(0,255,136,0.1); color:#00ff88; border:1px solid rgba(0,255,136,0.3); padding:2px 8px; border-radius:4px; font-size:0.55rem; font-weight:900;">LIVE</span>`
                        : `<span style="color:#444; border:1px solid #222; padding:2px 8px; border-radius:4px; font-size:0.55rem; font-weight:900;">UPCOMING</span>`);

                html += `
                    <div style="background:linear-gradient(145deg, #111, #080808); border-radius:18px; padding:20px; margin-bottom:15px; border: 1px solid #1a1a1a; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:18px; font-size:0.6rem; font-weight:800; text-transform:uppercase;">
                            <div style="color:#888;">GW ${f.gameweek} <span style="color:#00ff88; margin-left:8px; opacity:0.8;">FA CUP</span></div>
                            ${statusBadge}
                        </div>
                        <div style="display:flex; align-items:center; justify-content:space-between; gap:10px;">
                            <div style="flex:1; display:flex; flex-direction:column; align-items:center; min-width:0;">
                                <div style="font-size:0.85rem; font-weight:800; color:${hWin ? '#00ff88' : '#fff'}; text-align:center;">${f.home.team}</div>
                                <div style="font-size:0.6rem; color:#555;">${f.home.name}</div>
                            </div>
                            <div style="display:grid; grid-template-columns: 1fr auto 1fr; align-items:center; background:#000; padding:10px 14px; border-radius:12px; border:1px solid #222; min-width:85px;">
                                <div style="font-size:1.3rem; font-weight:900; text-align:right; color:${hWin ? '#00ff88' : '#fff'};">${hPts}</div>
                                <div style="font-size:0.8rem; color:#333; font-weight:900; padding:0 8px;">:</div>
                                <div style="font-size:1.3rem; font-weight:900; text-align:left; color:${aWin ? '#00ff88' : '#fff'};">${aPts}</div>
                            </div>
                            <div style="flex:1; display:flex; flex-direction:column; align-items:center; min-width:0;">
                                <div style="font-size:0.85rem; font-weight:800; color:${aWin ? '#00ff88' : '#fff'}; text-align:center;">${f.away.team}</div>
                                <div style="font-size:0.6rem; color:#555;">${f.away.name}</div>
                            </div>
                        </div>
                        ${f.tie_break_reason && (isLive || isCompleted) ? `<div style="text-align:center; font-size:0.55rem; color:#D4AF37; margin-top:10px; font-weight:bold;">🛡️ ${f.tie_break_reason}</div>` : ''}
                    </div>
                `;
            });
            content.innerHTML = html;
      
        });
    });
};
