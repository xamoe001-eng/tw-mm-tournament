/**
 * ၁။ Tournament Standings Render လုပ်ခြင်း
 */
window.renderLeagues = function() {
    const mainRoot = document.getElementById('main-root');
    if (!mainRoot) return;

    mainRoot.innerHTML = `
        <div style="padding: 12px; max-width: 500px; margin: 0 auto; font-family: 'Inter', sans-serif; background: #000; min-height: 100vh;">
            <div style="display: flex; background: #111; padding: 4px; border-radius: 50px; margin-bottom: 18px; border: 1px solid #222;">
                <button id="btn-divA" onclick="window.filterDivision('A')" 
                    style="flex: 1; padding: 10px; border: none; border-radius: 40px; font-weight: 800; cursor: pointer; transition: 0.3s; background: #D4AF37; color: #000; font-size: 0.8rem;">
                    DIVISION 1
                </button>
                <button id="btn-divB" onclick="window.filterDivision('B')" 
                    style="flex: 1; padding: 10px; border: none; border-radius: 40px; font-weight: 800; cursor: pointer; transition: 0.3s; background: transparent; color: #666; font-size: 0.8rem;">
                    DIVISION 2
                </button>
            </div>
            <div id="league-content"></div>
        </div>
    `;
    setTimeout(() => { window.filterDivision('A'); }, 100);
};

/**
 * ၂။ Division အလိုက် ဒေတာပြသခြင်း (Manual Sorting Version)
 */
window.filterDivision = function(divTag) {
    const content = document.getElementById('league-content');
    const btnA = document.getElementById('btn-divA');
    const btnB = document.getElementById('btn-divB');
    if (!content) return;

    // Active Button Style
    if (divTag === 'A') {
        btnA.style.background = '#D4AF37'; btnA.style.color = '#000';
        btnB.style.background = 'transparent'; btnB.style.color = '#666';
    } else {
        btnB.style.background = '#C0C0C0'; btnB.style.color = '#000';
        btnA.style.background = 'transparent'; btnA.style.color = '#666';
    }

    // 🔥 Index Error မတက်အောင် orderBy မသုံးဘဲ ဆွဲထုတ်သည်
    db.collection("tw_mm_tournament")
      .where("league_tag", "==", divTag)
      .onSnapshot((snapshot) => {
        if (snapshot.empty) {
            content.innerHTML = `<div style="text-align:center; padding:50px; color:#444;">NO DATA FOR DIV ${divTag}</div>`;
            return;
        }

        let players = [];
        snapshot.forEach(doc => players.push(doc.data()));

        // ⚡ Sorting: နိုင်မှတ် (PTS) အရင်စီ၊ တူရင် GW Points နဲ့ ထပ်စီသည်
        players.sort((a, b) => {
            if ((b.h2h_points || 0) !== (a.h2h_points || 0)) {
                return (b.h2h_points || 0) - (a.h2h_points || 0);
            }
            return (b.gw_points || 0) - (a.gw_points || 0);
        });

        let html = `
            <div style="display: flex; justify-content: space-between; padding: 0 10px 10px; font-size: 0.65rem; color: #555; font-weight: 800; text-transform: uppercase;">
                <span># TEAM INFO</span>
                <span>GW / STATS / PTS</span>
            </div>
        `;

        players.forEach((p, index) => {
            const pos = index + 1;
            const rankColor = pos === 1 ? '#D4AF37' : (pos === 2 ? '#C0C0C0' : (pos === 3 ? '#CD7F32' : '#fff'));

            html += `
                <div style="background: #111; margin-bottom: 8px; border-radius: 12px; padding: 12px; display: flex; align-items: center; border: 1px solid #222;">
                    <div style="width: 30px; font-weight: 900; font-size: 1rem; color: ${rankColor};">${pos}</div>
                    
                    <div style="flex: 1; min-width: 0; padding-right: 5px;">
                        <div style="font-weight: 800; color: #fff; font-size: 0.85rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                            ${p.team_name || 'No Name'}
                        </div>
                        <div style="font-size: 0.65rem; color: #555;">${p.manager_name || 'User'}</div>
                    </div>

                    <div style="text-align: right; min-width: 110px;">
                        <div style="display: flex; justify-content: flex-end; gap: 4px; margin-bottom: 4px; font-size: 0.6rem; font-weight: 800;">
                            <span style="color: #00ff88; padding: 1px 5px; background: rgba(0,255,136,0.1); border-radius: 3px;">GW: ${p.gw_points || 0}</span>
                            <span style="color: #bbb;">P:${p.played || 0}</span>
                        </div>
                        
                        <div style="display: flex; justify-content: flex-end; gap: 3px; font-size: 0.55rem; margin-bottom: 4px;">
                             <span style="color: #00ff88;">W:${p.wins || 0}</span>
                             <span style="color: #ffcc00;">D:${p.draws || 0}</span>
                             <span style="color: #ff4d4d;">L:${p.losses || 0}</span>
                        </div>

                        <div style="font-weight: 900; font-size: 1.1rem; color: ${divTag === 'A' ? '#D4AF37' : '#C0C0C0'};">
                            ${p.h2h_points || 0}<span style="font-size: 0.55rem; margin-left: 2px; color: #666;">PTS</span>
                        </div>
                    </div>
                </div>
            `;
        });
        content.innerHTML = html;
    }, (err) => {
        console.error("Standings Error:", err);
        content.innerHTML = `<div style="color:red; text-align:center;">Error: ${err.message}</div>`;
    });
};
