// ၁။ Tournament Standings စာမျက်နှာကို စတင်ဖန်တီးခြင်း
/**
 * ၁။ Tournament Standings Render လုပ်ခြင်း
 */
window.renderLeagues = function() {
    const mainRoot = document.getElementById('main-root');
    if (!mainRoot) return;

    mainRoot.innerHTML = `
        <div style="padding: 10px;">
            <div style="display: flex; background: #111; padding: 5px; border-radius: 50px; margin-bottom: 20px; border: 1px solid #222;">
                <button id="btn-divA" onclick="window.filterDivision('A')" 
                    style="flex: 1; padding: 12px; border: none; border-radius: 40px; font-weight: bold; cursor: pointer; transition: 0.3s; background: #D4AF37; color: #000;">
                    Division 1
                </button>
                <button id="btn-divB" onclick="window.filterDivision('B')" 
                    style="flex: 1; padding: 12px; border: none; border-radius: 40px; font-weight: bold; cursor: pointer; transition: 0.3s; background: transparent; color: #888;">
                    Division 2
                </button>
            </div>

            <div id="league-content">
                <div class="loading" style="text-align:center; padding:50px;">
                    <div class="spinner"></div>
                    <p style="color:#888; font-size:0.8rem; margin-top:10px;">Standings ဒေတာများ ဆွဲယူနေသည်...</p>
                </div>
            </div>
        </div>
    `;

    // ပထမဦးဆုံး Division A ကို ခေါ်ပေးမည်
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

    // Button UI Toggle
    if (divTag === 'A') {
        if(btnA) { btnA.style.background = '#D4AF37'; btnA.style.color = '#000'; }
        if(btnB) { btnB.style.background = 'transparent'; btnB.style.color = '#888'; }
    } else {
        if(btnB) { btnB.style.background = '#C0C0C0'; btnB.style.color = '#000'; }
        if(btnA) { btnA.style.background = 'transparent'; btnA.style.color = '#888'; }
    }

    // Firestore `db` ရှိမရှိ အရင်စစ်မည်
    if (typeof db === 'undefined') {
        content.innerHTML = "<div style='color:red; text-align:center; padding:20px;'>Firebase `db` Error: config.js ကို စစ်ဆေးပါ။</div>";
        return;
    }

    // Real-time Listener
    db.collection("tw_mm_tournament")
      .where("league_tag", "==", divTag)
      .orderBy("h2h_points", "desc") 
      .orderBy("gw_points", "desc") 
      .onSnapshot((snapshot) => {
        if (snapshot.empty) {
            content.innerHTML = `<div style="text-align:center; padding:50px; color:#555;">လက်ရှိတွင် ဒေတာမရှိသေးပါ။</div>`;
            return;
        }

        let html = `
            <div style="display: flex; justify-content: space-between; padding: 0 10px 10px; font-size: 0.7rem; color: #555; font-weight: bold; text-transform: uppercase;">
                <span>Rank & Team</span>
                <span>P - W - D - L / PTS</span>
            </div>
        `;

        let pos = 1;
        snapshot.forEach((doc) => {
            const p = doc.data();
            const rankColor = pos === 1 ? '#D4AF37' : (pos === 2 ? '#C0C0C0' : (pos === 3 ? '#CD7F32' : '#fff'));

            html += `
                <div style="background: #111; margin-bottom: 8px; border-radius: 12px; padding: 12px; display: flex; align-items: center; border: 1px solid #222;">
                    <div style="width: 25px; font-weight: 800; font-size: 1rem; color: ${rankColor}; text-align: center; margin-right: 10px;">
                        ${pos}
                    </div>
                    
                    <div style="flex: 1; min-width: 0;">
                        <div style="font-weight: bold; color: #fff; font-size: 0.9rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                            ${p.team_name}
                        </div>
                        <div style="font-size: 0.7rem; color: #666;">
                            ${p.manager_name}
                        </div>
                    </div>

                    <div style="text-align: right; margin-left: 10px;">
                        <div style="font-size: 0.65rem; color: #555; margin-bottom: 2px;">
                            ${p.played || 0} - ${p.wins || 0} - ${p.draws || 0} - ${p.losses || 0}
                        </div>
                        <div style="font-weight: 900; font-size: 1rem; color: ${divTag === 'A' ? '#D4AF37' : '#C0C0C0'};">
                            ${p.h2h_points || 0} <span style="font-size: 0.6rem; opacity: 0.5;">PTS</span>
                        </div>
                    </div>
                </div>
            `;
            pos++;
        });

        content.innerHTML = html;
      }, (error) => {
          console.error("Firestore Error:", error);
          content.innerHTML = `<div style="color:#ff4d4d; padding:20px; font-size:0.8rem; text-align:center;">⚠️ Index Error: Firebase Console တွင် Index ဆောက်ပေးရန် လိုအပ်သည်။</div>`;
          
      });
};
