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
            
            <div style="background: rgba(255,255,255,0.03); border: 1px dashed #333; border-radius: 10px; padding: 10px; margin-bottom: 15px; text-align: center;">
                <div style="font-size: 0.6rem; color: #888; text-transform: uppercase; letter-spacing: 1px;">Live League Standings (Weekly Points Ranking)</div>
            </div>

            <div id="league-content">
                <div style="text-align:center; color:#555; padding-top:50px;">🎮 Loading Standings...</div>
            </div>
        </div>
    `;
    // ပထမဆုံးဖွင့်လျှင် Division A အရင်ပြမည်
    setTimeout(() => { window.filterDivision('Division A'); }, 100);
};

/**
 * ၂။ Division အလိုက် ဒေတာဆွဲထုတ်ခြင်း (Sorting logic ပါဝင်သည်)
 */
window.filterDivision = function(divName) {
    const content = document.getElementById('league-content');
    const btnA = document.getElementById('btn-divA');
    const btnB = document.getElementById('btn-divB');
    if (!content) return;

    const isDivA = divName === 'Division A';
    
    // Button Colors ပြောင်းလဲခြင်း
    btnA.style.background = isDivA ? '#D4AF37' : 'transparent';
    btnA.style.color = isDivA ? '#000' : '#666';
    btnB.style.background = !isDivA ? '#C0C0C0' : 'transparent';
    btnB.style.color = !isDivA ? '#000' : '#666';

    content.innerHTML = `<div style="text-align:center; padding:50px; color:#555;">⌛ Fetching Data...</div>`;

    db.collection("tw_mm_tournament")
      .where("division", "==", divName)
      .onSnapshot((snapshot) => {
        if (snapshot.empty) {
            content.innerHTML = `<div style="text-align:center; padding:50px; color:#444;">NO DATA FOUND FOR ${divName}</div>`;
            return;
        }

        let players = [];
        snapshot.forEach(doc => {
            players.push(doc.data());
        });

        // 🔥 အဓိကပြင်ဆင်ချက်- Week Point (gw_live_points) အများဆုံးလူကို ထိပ်ဆုံးကထား၍ စီမည်
        players.sort((a, b) => (b.gw_live_points || 0) - (a.gw_live_points || 0));

        let html = `
            <div style="display: flex; justify-content: space-between; padding: 0 10px 10px; font-size: 0.6rem; color: #444; font-weight: 800; text-transform: uppercase;">
                <span>RANK / TEAM NAME</span>
                <span>WEEK PTS / TOTAL NET</span>
            </div>
        `;

        players.forEach((p, index) => {
            const pos = index + 1;
            const themeColor = isDivA ? '#D4AF37' : '#C0C0C0';
            const rankColor = pos === 1 ? themeColor : (pos <= 3 ? '#fff' : '#444');

            html += `
                <div style="background: #111; margin-bottom: 8px; border-radius: 12px; padding: 14px; display: flex; align-items: center; border: 1px solid #1a1a1a;">
                    <div style="width: 25px; font-weight: 900; font-size: 1rem; color: ${rankColor}; text-align: center;">${pos}</div>
                    
                    <div style="flex: 1; min-width: 0; padding-right: 10px; margin-left: 12px;">
                        <div style="font-weight: 800; color: #fff; font-size: 0.85rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                            ${p.team || 'Unknown Team'}
                        </div>
                        <div style="font-size: 0.6rem; color: #555; text-transform: uppercase;">${p.name || 'Manager'}</div>
                    </div>

                    <div style="text-align: right;">
                        <div style="font-weight: 900; font-size: 1.4rem; color: #00ff88; line-height: 1;">
                            ${p.gw_live_points || 0}
                        </div>
                        <div style="margin-top: 4px;">
                            <span style="font-size: 0.55rem; font-weight: 800; color: #888; background: rgba(255,255,255,0.05); padding: 2px 6px; border-radius: 4px;">
                                NET: ${p.tournament_total_net_points || 0}
                            </span>
                        </div>
                    </div>
                </div>
            `;
        });
        content.innerHTML = html
            ;
    });
};
