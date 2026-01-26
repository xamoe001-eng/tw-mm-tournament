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

    content.innerHTML = `<div class="loading" style="color:#D4AF37;">Division ${divTag} Standings ရှာနေသည်...</div>`;

    // Button အရောင်များ ပြောင်းလဲခြင်း
    document.getElementById('btn-divA').style.opacity = (divTag === 'A') ? '1' : '0.5';
    document.getElementById('btn-divB').style.opacity = (divTag === 'B') ? '1' : '0.5';

    // Query Logic - h2h_points ဖြင့် အဓိကစီမည်
    // သတိပေးချက် - Console ထဲက Index Link ကို မဖြစ်မနေ နှိပ်ပေးရန် လိုအပ်သည်
    db.collection("tw_mm_tournament")
      .where("league_tag", "==", divTag)
      .orderBy("h2h_points", "desc") 
      .orderBy("gw_points", "desc") 
      .onSnapshot((snapshot) => {
        if (snapshot.empty) {
            content.innerHTML = `<div style="padding:40px; color:#888;">ဒေတာ မရှိသေးပါ။ Python ကို GW 23 ဖြင့် အရင် Run ပေးပါ။</div>`;
            return;
        }

        let html = `
            <h2 style="color: ${divTag === 'A' ? '#D4AF37' : '#C0C0C0'}; margin-bottom: 15px; font-size: 1.1rem; text-transform: uppercase;">
                DIVISION ${divTag === 'A' ? '1' : '2'} H2H TABLE
            </h2>
            <div style="overflow-x: auto;">
                <table style="width:100%; border-collapse: collapse; text-align: center; font-size: 0.85rem; color: #fff;">
                    <thead>
                        <tr style="border-bottom: 2px solid #444; color: #888; font-size: 0.7rem;">
                            <th style="padding:10px; text-align:left;">POS</th>
                            <th style="padding:10px; text-align:left;">TEAM</th>
                            <th style="padding:5px;">P</th>
                            <th style="padding:5px;">W</th>
                            <th style="padding:5px;">D</th>
                            <th style="padding:5px;">L</th>
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
                        <div style="font-weight: bold; color:#fff; font-size: 0.85rem;">${p.team_name}</div>
                        <div style="font-size: 0.65rem; color: #777;">${p.manager_name}</div>
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
          // Error ဖြစ်လျှင် Index ဆောက်ရန် Link ကို Console မှာကြည့်ရန် ညွှန်ကြားချက်ပြမည်
          content.innerHTML = `
            <div style="color:#ff4444; padding:20px; font-size:0.8rem;">
                <p>⚠️ Database Index လိုအပ်နေပါသည်။</p>
                <p style="color:#888;">Browser Console (F12) ထဲက Link ကိုနှိပ်ပြီး Index ဆောက်ပေးပါခင်ဗျာ။</p>
            </div>`;
      });
};
