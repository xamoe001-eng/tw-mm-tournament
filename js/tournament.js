// ၁။ Tournament စာမျက်နှာကို စတင်ဖန်တီးခြင်း
window.renderLeagues = function() {
    const mainRoot = document.getElementById('main-root');
    if (!mainRoot) return;

    mainRoot.innerHTML = `
        <div style="text-align: center; padding: 15px;">
            <div style="margin-bottom: 25px;">
                <button id="btn-divA" onclick="window.filterDivision('A')" class="nav-btn" 
                    style="background:#D4AF37; color:black; margin:5px; border-radius: 20px; padding: 10px 20px; font-weight:bold; border:none; cursor:pointer;">
                    Division 1
                </button>
                <button id="btn-divB" onclick="window.filterDivision('B')" class="nav-btn" 
                    style="background:#C0C0C0; color:black; margin:5px; border-radius: 20px; padding: 10px 20px; font-weight:bold; border:none; cursor:pointer;">
                    Division 2
                </button>
            </div>

            <div id="league-content" style="min-height: 200px;">
                <div class="loading">🏆 H2H Standings ကို ဆွဲယူနေသည်...</div>
            </div>
        </div>
    `;

    // စဖွင့်ဖွင့်ချင်း Division 1 (A) ကို အလိုအလျောက် ပြမည်
    setTimeout(() => { window.filterDivision('A'); }, 100);
};

// ၂။ Division အလိုက် Table ဆောက်ပေးမည့် Function
window.filterDivision = function(divTag) {
    const content = document.getElementById('league-content');
    if (!content) return;

    // Loading ပြမည်
    content.innerHTML = `<div class="loading" style="color:#D4AF37;">Division ${divTag} Standings ရှာနေသည်...</div>`;

    // Database မှ ဒေတာများကို h2h_points အများဆုံးအတိုင်း စီ၍ ဖတ်မည်
    db.collection("tw_mm_tournament")
      .where("league_tag", "==", divTag)
      .orderBy("h2h_points", "desc") // H2H Points ဖြင့် Rank စီမည်
      .orderBy("gw_points", "desc")   // အမှတ်တူလျှင် Weekly အမှတ်ဖြင့် ထပ်စီမည်
      .onSnapshot((snapshot) => {
        if (snapshot.empty) {
            content.innerHTML = `<div style="padding:40px; color:#888;">ဒေတာ မရှိသေးပါ။ Python Script ကို အရင် Run ပေးပါ။</div>`;
            return;
        }

        let html = `
            <h2 style="color: ${divTag === 'A' ? '#D4AF37' : '#C0C0C0'}; margin-bottom: 15px; font-size: 1.1rem; text-transform: uppercase;">
                DIVISION ${divTag === 'A' ? '1' : '2'} H2H TABLE
            </h2>
            <div style="overflow-x: auto;">
                <table style="width:100%; border-collapse: collapse; text-align: center; font-size: 0.85rem; color: #fff;">
                    <thead>
                        <tr style="border-bottom: 2px solid #444; color: #888;">
                            <th style="padding:10px; text-align:left;">POS</th>
                            <th style="padding:10px; text-align:left;">TEAM</th>
                            <th style="padding:10px;">P</th>
                            <th style="padding:10px;">W</th>
                            <th style="padding:10px;">D</th>
                            <th style="padding:10px;">L</th>
                            <th style="padding:10px; text-align:right;">PTS</th>
                        </tr>
                    </thead>
                    <tbody>`;

        let pos = 1;

        snapshot.forEach((doc) => {
            const p = doc.data();
            
            html += `
                <tr style="border-bottom: 1px solid #222;">
                    <td style="padding: 12px 5px; text-align:left; font-weight:bold; color: ${divTag === 'A' ? '#D4AF37' : '#C0C0C0'};">
                        ${pos}
                    </td>
                    <td style="padding: 12px 5px; text-align:left;">
                        <div style="font-weight: bold; color:#fff;">${p.team_name}</div>
                        <div style="font-size: 0.7rem; color: #888;">${p.manager_name}</div>
                    </td>
                    <td style="padding: 12px 5px;">${p.played || 0}</td>
                    <td style="padding: 12px 5px; color: #00ff88;">${p.wins || 0}</td>
                    <td style="padding: 12px 5px; color: #888;">${p.draws || 0}</td>
                    <td style="padding: 12px 5px; color: #ff4444;">${p.losses || 0}</td>
                    <td style="padding: 12px 5px; text-align:right; font-weight:bold; color:#D4AF37;">
                        ${p.h2h_points || 0}
                    </td>
                </tr>`;
            pos++;
        });

        html += `</tbody></table></div>`;
        content.innerHTML = html;
        
      }, (error) => {
          console.error("Firestore Error:", error);
          content.innerHTML = `<div style="color:#ff4444; padding:20px;">Database Error! Please check Indexing.</div>`;
      });
};
