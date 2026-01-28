/**
 * ၁။ Tournament Standings Render လုပ်ခြင်း
 */
window.renderLeagues = function() {
    const mainRoot = document.getElementById('main-root');
    if (!mainRoot) return;

    mainRoot.innerHTML = `
        <div style="padding: 12px; max-width: 500px; margin: 0 auto; font-family: 'Inter', sans-serif; background: #000; min-height: 100vh; color: white;">
            <div style="display: flex; background: #111; padding: 4px; border-radius: 50px; margin-bottom: 20px; border: 1px solid #222;">
                <button id="btn-divA" onclick="window.filterDivision('Division A')" 
                    style="flex: 1; padding: 12px; border: none; border-radius: 40px; font-weight: 800; cursor: pointer; transition: 0.3s; background: #D4AF37; color: #000; font-size: 0.7rem;">
                    DIVISION A (Gold)
                </button>
                <button id="btn-divB" onclick="window.filterDivision('Division B')" 
                    style="flex: 1; padding: 12px; border: none; border-radius: 40px; font-weight: 800; cursor: pointer; transition: 0.3s; background: transparent; color: #666; font-size: 0.7rem;">
                    DIVISION B (Silver)
                </button>
            </div>
            <div id="league-content">
                <div style="text-align:center; color:#555; padding-top:50px;">🎮 Loading Standings...</div>
            </div>
        </div>
    `;
    // ပထမဆုံးဝင်ဝင်ချင်း Division A ကိုပြမယ်
    setTimeout(() => { window.filterDivision('Division A'); }, 100);
};

/**
 * ၂။ Division အလိုက် ဒေတာဆွဲထုတ်ခြင်း
 */
window.filterDivision = function(divName) {
    const content = document.getElementById('league-content');
    const btnA = document.getElementById('btn-divA');
    const btnB = document.getElementById('btn-divB');
    if (!content) return;

    // Button UI Toggle
    const isDivA = divName === 'Division A';
    btnA.style.background = isDivA ? '#D4AF37' : 'transparent';
    btnA.style.color = isDivA ? '#000' : '#666';
    btnB.style.background = !isDivA ? '#C0C0C0' : 'transparent';
    btnB.style.color = !isDivA ? '#000' : '#666';

    content.innerHTML = `<div style="text-align:center; padding:50px; color:#555;">⌛ Fetching Data...</div>`;

    db.collection("tw_mm_tournament")
      .where("division", "==", divName) // "Division A" သို့မဟုတ် "Division B" ကိုစစ်သည်
      .onSnapshot((snapshot) => {
        if (snapshot.empty) {
            content.innerHTML = `<div style="text-align:center; padding:50px; color:#444;">NO DATA FOUND FOR ${divName}</div>`;
            return;
        }

        let players = [];
        snapshot.forEach(doc => {
            players.push(doc.data());
        });

        // ⚡ Sorting Logic
        players.sort((a, b) => {
            // ၁။ နိုင်မှတ် (PTS) အရင်စီ
            if ((b.h2h_points || 0) !== (a.h2h_points || 0)) {
                return (b.h2h_points || 0) - (a.h2h_points || 0);
            }
            // ၂။ PTS တူရင် Total Net Points နဲ့ ထပ်စီ
            return (b.tournament_total_net_points || 0) - (a.tournament_total_net_points || 0);
        });

        let html = `
            <div style="display: flex; justify-content: space-between; padding: 0 10px 10px; font-size: 0.6rem; color: #444; font-weight: 800; text-transform: uppercase;">
                <span>RANK / MANAGER</span>
                <span>GW / STATS / PTS</span>
            </div>
        `;

        players.forEach((p, index) => {
            const pos = index + 1;
            const rankColor = pos === 1 ? (isDivA ? '#D4AF37' : '#C0C0C0') : (pos <= 3 ? '#888' : '#444');
            const themeColor = isDivA ? '#D4AF37' : '#C0C0C0';

            html += `
                <div style="background: #111; margin-bottom: 10px; border-radius: 12px; padding: 14px; display: flex; align-items: center; border: 1px solid #222;">
                    <div style="width: 30px; font-weight: 900; font-size: 1rem; color: ${rankColor};">${pos}</div>
                    
                    <div style="flex: 1; min-width: 0; padding-right: 10px;">
                        <div style="font-weight: 800; color: #fff; font-size: 0.85rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                            ${p.team_name || 'Team'}
                        </div>
                        <div style="font-size: 0.65rem; color: #555;">${p.manager_name || 'Manager'}</div>
                    </div>

                    <div style="text-align: right; min-width: 100px;">
                        <div style="display: flex; justify-content: flex-end; gap: 4px; margin-bottom: 4px;">
                            <span style="color: #00ff88; font-size: 0.55rem; font-weight: 800; background: rgba(0,255,136,0.1); padding: 1px 4px; border-radius: 3px;">
                                GW:${p.gw_points || 0}
                            </span>
                            <span style="color: #555; font-size: 0.55rem; font-weight: 800;">P:${p.played || 0}</span>
                        </div>
                        
                        <div style="display: flex; justify-content: flex-end; gap: 4px; font-size: 0.5rem; margin-bottom: 4px; font-weight: 700;">
                             <span style="color: #00ff88;">W:${p.wins || 0}</span>
                             <span style="color: #666;">D:${p.draws || 0}</span>
                             <span style="color: #ff4d4d;">L:${p.losses || 0}</span>
                        </div>

                        <div style="font-weight: 900; font-size: 1.2rem; color: ${themeColor};">
                            ${p.h2h_points || 0}<span style="font-size: 0.55rem; margin-left: 2px; color: #444;">PTS</span>
                        </div>
                    </div>
                </div>
            `;
        });
        content.innerHTML = html;
          
    });
};
