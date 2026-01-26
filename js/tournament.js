/**
 * ၁။ Tournament Standings စာမျက်နှာကို စတင်ဖန်တီးခြင်း
 */
window.renderLeagues = function() {
    const mainRoot = document.getElementById('main-root');
    if (!mainRoot) return;

    mainRoot.innerHTML = `
        <div style="padding: 12px; max-width: 500px; margin: 0 auto; font-family: 'Inter', sans-serif;">
            <div style="display: flex; background: #161616; padding: 4px; border-radius: 50px; margin-bottom: 18px; border: 1px solid #222; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
                <button id="btn-divA" onclick="window.filterDivision('A')" 
                    style="flex: 1; padding: 10px; border: none; border-radius: 40px; font-weight: 800; cursor: pointer; transition: all 0.3s ease; background: #D4AF37; color: #000; font-size: 0.8rem; letter-spacing: 1px;">
                    DIVISION 1
                </button>
                <button id="btn-divB" onclick="window.filterDivision('B')" 
                    style="flex: 1; padding: 10px; border: none; border-radius: 40px; font-weight: 800; cursor: pointer; transition: all 0.3s ease; background: transparent; color: #666; font-size: 0.8rem; letter-spacing: 1px;">
                    DIVISION 2
                </button>
            </div>

            <div id="league-content">
                <div style="text-align:center; padding:50px;">
                    <div class="spinner"></div>
                    <p style="color:#888; font-size:0.7rem; margin-top:12px;">LOADING DATA...</p>
                </div>
            </div>
        </div>
    `;

    setTimeout(() => { window.filterDivision('A'); }, 100);
};

/**
 * ၂။ Division အလိုက် ဒေတာ စစ်ထုတ်ပြသခြင်း
 */
window.filterDivision = function(divTag) {
    const content = document.getElementById('league-content');
    const btnA = document.getElementById('btn-divA');
    const btnB = document.getElementById('btn-divB');

    if (!content) return;

    // UI Feedback
    if (divTag === 'A') {
        if(btnA) { btnA.style.background = '#D4AF37'; btnA.style.color = '#000'; }
        if(btnB) { btnB.style.background = 'transparent'; btnB.style.color = '#666'; }
    } else {
        if(btnB) { btnB.style.background = '#C0C0C0'; btnB.style.color = '#000'; }
        if(btnA) { btnA.style.background = 'transparent'; btnA.style.color = '#666'; }
    }

    if (typeof db === 'undefined') return;

    db.collection("tw_mm_tournament")
      .where("league_tag", "==", divTag)
      .orderBy("h2h_points", "desc") 
      .orderBy("gw_points", "desc") 
      .onSnapshot((snapshot) => {
        if (snapshot.empty) {
            content.innerHTML = `<div style="text-align:center; padding:60px; color:#444; font-size: 0.8rem; font-weight: 600;">NO DATA FOUND</div>`;
            return;
        }

        let html = `
            <div style="display: flex; justify-content: space-between; padding: 0 12px 10px; font-size: 0.65rem; color: #777; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">
                <span># TEAM INFO</span>
                <span>STATS / PTS</span>
            </div>
        `;

        let pos = 1;
        snapshot.forEach((doc) => {
            const p = doc.data();
            const rankColor = pos === 1 ? '#D4AF37' : (pos === 2 ? '#C0C0C0' : (pos === 3 ? '#CD7F32' : '#fff'));

            html += `
                <div style="background: #111; margin-bottom: 8px; border-radius: 12px; padding: 12px 14px; display: flex; align-items: center; border: 1px solid #222; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
                    <div style="width: 32px; font-weight: 900; font-size: 1rem; color: ${rankColor};">
                        ${pos}
                    </div>
                    
                    <div style="flex: 1; min-width: 0;">
                        <div style="font-weight: 800; color: #fff; font-size: 0.85rem; text-transform: uppercase;">
                            ${p.team_name}
                        </div>
                        <div style="font-size: 0.65rem; color: #666; font-weight: 600;">
                            ${p.manager_name}
                        </div>
                    </div>

                    <div style="text-align: right; min-width: 95px;">
                        <div style="font-size: 0.7rem; color: #ddd; margin-bottom: 3px; font-weight: 700; font-family: 'Inter', sans-serif;">
                            <span style="color: #666; font-size: 0.6rem;">P</span>${p.played || 0} 
                            <span style="color: #00ff88; font-size: 0.6rem; margin-left: 2px;">W</span>${p.wins || 0} 
                            <span style="color: #ffcc00; font-size: 0.6rem; margin-left: 2px;">D</span>${p.draws || 0} 
                            <span style="color: #ff4d4d; font-size: 0.6rem; margin-left: 2px;">L</span>${p.losses || 0}
                        </div>
                        <div style="font-weight: 900; font-size: 1.1rem; color: ${divTag === 'A' ? '#D4AF37' : '#C0C0C0'};">
                            ${p.h2h_points || 0}<span style="font-size: 0.6rem; margin-left: 2px; color: #555;">PTS</span>
                        </div>
                    </div>
                </div>
            `;
            pos++;
        });

        content.innerHTML = html;

      });
};
