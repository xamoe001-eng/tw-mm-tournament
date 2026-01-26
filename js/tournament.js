// ၁။ Tournament Standings စာမျက်နှာကို စတင်ဖန်တီးခြင်း
/**
/**
 * ၁။ Tournament Standings Render လုပ်ခြင်း
 */
window.renderLeagues = function() {
    const mainRoot = document.getElementById('main-root');
    if (!mainRoot) return;

    mainRoot.innerHTML = `
        <div style="padding: 12px; max-width: 500px; margin: 0 auto;">
            <div style="display: flex; background: #161616; padding: 4px; border-radius: 50px; margin-bottom: 15px; border: 1px solid #222;">
                <button id="btn-divA" onclick="window.filterDivision('A')" 
                    style="flex: 1; padding: 10px; border: none; border-radius: 40px; font-weight: 800; cursor: pointer; transition: 0.3s; background: #D4AF37; color: #000; font-size: 0.85rem;">
                    DIVISION 1
                </button>
                <button id="btn-divB" onclick="window.filterDivision('B')" 
                    style="flex: 1; padding: 10px; border: none; border-radius: 40px; font-weight: 800; cursor: pointer; transition: 0.3s; background: transparent; color: #666; font-size: 0.85rem;">
                    DIVISION 2
                </button>
            </div>

            <div id="league-content">
                <div class="loading" style="text-align:center; padding:40px;">
                    <div class="spinner"></div>
                    <p style="color:#555; font-size:0.75rem; margin-top:10px; letter-spacing: 1px;">LOADING DATA...</p>
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

    // UI Toggle
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
            content.innerHTML = `<div style="text-align:center; padding:50px; color:#444; font-size: 0.8rem;">NO DATA AVAILABLE</div>`;
            return;
        }

        let html = `
            <div style="display: flex; justify-content: space-between; padding: 0 10px 8px; font-size: 0.65rem; color: #444; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">
                <span># TEAM</span>
                <span>P - W - D - L / PTS</span>
            </div>
        `;

        let pos = 1;
        snapshot.forEach((doc) => {
            const p = doc.data();
            const rankColor = pos === 1 ? '#D4AF37' : (pos === 2 ? '#C0C0C0' : (pos === 3 ? '#CD7F32' : '#fff'));

            html += `
                <div style="background: linear-gradient(90deg, #111 0%, #0a0a0a 100%); margin-bottom: 6px; border-radius: 10px; padding: 10px 12px; display: flex; align-items: center; border: 1px solid #1a1a1a;">
                    <div style="width: 28px; font-weight: 900; font-size: 0.95rem; color: ${rankColor}; text-align: left;">
                        ${pos}
                    </div>
                    
                    <div style="flex: 1; min-width: 0; padding-right: 10px;">
                        <div style="font-weight: 700; color: #fff; font-size: 0.85rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; letter-spacing: 0.2px;">
                            ${p.team_name}
                        </div>
                        <div style="font-size: 0.65rem; color: #555; margin-top: 1px; font-weight: 500;">
                            ${p.manager_name}
                        </div>
                    </div>

                    <div style="text-align: right;">
                        <div style="font-size: 0.6rem; color: #444; margin-bottom: 1px; font-family: monospace; font-weight: bold;">
                            ${p.played || 0} - ${p.wins || 0} - ${p.draws || 0} - ${p.losses || 0}
                        </div>
                        <div style="font-weight: 900; font-size: 1rem; color: ${divTag === 'A' ? '#D4AF37' : '#C0C0C0'};">
                            ${p.h2h_points || 0}<span style="font-size: 0.55rem; margin-left: 2px; opacity: 0.6;">PTS</span>
                        </div>
                    </div>
                </div>
            `;
            pos++;
        });

        content.innerHTML = html;
      }, (error) => {
          console.error("Firestore Error:", error);
          content.innerHTML = `<div style="color:#ff4d4d; padding:20px; font-size:0.75rem; text-align:center; background: rgba(255,0,0,0.05); border-radius: 10px;">⚠️ Please create Firestore Index in Firebase Console.</div>`;
          
      });
};
