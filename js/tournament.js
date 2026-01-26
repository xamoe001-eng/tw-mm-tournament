// ၁။ Tournament Standings စာမျက်နှာကို စတင်ဖန်တီးခြင်း
window.renderLeagues = function() {
    const mainRoot = document.getElementById('main-root');
    if (!mainRoot) return;

    mainRoot.innerHTML = `
        <div style="text-align: center; padding: 15px;">
            <div style="margin-bottom: 25px; display: flex; justify-content: center; gap: 10px;">
                <button id="btn-divA" onclick="window.filterDivision('A')" class="nav-btn" 
                    style="background:#D4AF37; color:black; border-radius: 20px; padding: 10px 25px; font-weight:bold; border:none; cursor:pointer; transition: 0.3s;">
                    Division 1
                </button>
                <button id="btn-divB" onclick="window.filterDivision('B')" class="nav-btn" 
                    style="background:#C0C0C0; color:black; border-radius: 20px; padding: 10px 25px; font-weight:bold; border:none; cursor:pointer; transition: 0.3s;">
                    Division 2
                </button>
            </div>

            <div id="league-content" style="min-height: 300px; background: rgba(0,0,0,0.2); border-radius: 15px; padding: 10px;">
                <div class="loading" style="padding: 50px; color: #888;">📊 Standings ဒေတာများကို စစ်ဆေးနေသည်...</div>
            </div>
        </div>
    `;

    // စဖွင့်ဖွင့်ချင်း Division 1 (A) ကို အလိုအလျောက် ပြသမည်
    setTimeout(() => { window.filterDivision('A'); }, 100);
};

// ၂။ Division အလိုက် H2H Table ဆောက်ပေးမည့် Function
window.filterDivision = function(divTag) {
    const content = document.getElementById('league-content');
    if (!content) return;

    // Loading State ပြသခြင်း
    content.innerHTML = `<div class="loading" style="padding: 50px; color: ${divTag === 'A' ? '#D4AF37' : '#C0C0C0'};">Division ${divTag} Standings ရှာဖွေနေသည်...</div>`;

    // Button UI Update လုပ်ခြင်း
    const btnA = document.getElementById('btn-divA');
    const btnB = document.getElementById('btn-divB');
    if (btnA && btnB) {
        btnA.style.transform = (divTag === 'A') ? 'scale(1.1)' : 'scale(1)';
        btnA.style.boxShadow = (divTag === 'A') ? '0 0 15px rgba(212, 175, 55, 0.5)' : 'none';
        btnB.style.transform = (divTag === 'B') ? 'scale(1.1)' : 'scale(1)';
        btnB.style.boxShadow = (divTag === 'B') ? '0 0 15px rgba(192, 192, 192, 0.5)' : 'none';
    }

    // Firestore Query: h2h_points ဖြင့် အရင်စီပြီး အမှတ်တူလျှင် gw_points ဖြင့် ထပ်စီမည်
    db.collection("tw_mm_tournament")
      .where("league_tag", "==", divTag)
      .orderBy("h2h_points", "desc") 
      .orderBy("gw_points", "desc") 
      .onSnapshot((snapshot) => {
        if (snapshot.empty) {
            content.innerHTML = `<div style="padding:50px; color:#888;">လက်ရှိတွင် ဒေတာမရှိသေးပါ။ Python Sync ကို အရင်လုပ်ဆောင်ပေးပါ။</div>`;
            return;
        }

        let html = `
            <h2 style="color: ${divTag === 'A' ? '#D4AF37' : '#C0C0C0'}; margin: 15px 0; font-size: 1.2rem; letter-spacing: 1px;">
                DIVISION ${divTag === 'A' ? 'ONE' : 'TWO'} STANDINGS
            </h2>
            <div style="overflow-x: auto;">
                <table style="width:100%; border-collapse: collapse; text-align: center; font-size: 0.85rem; color: #eee;">
                    <thead>
                        <tr style="border-bottom: 2px solid #333; color: #999; font-size: 0.75rem;">
                            <th style="padding:12px 5px; text-align:left;">POS</th>
                            <th style="padding:12px 5px; text-align:left;">TEAM / MANAGER</th>
                            <th style="padding:12px 5px;">P</th>
                            <th style="padding:12px 5px;">W</th>
                            <th style="padding:12px 5px;">D</th>
                            <th style="padding:12px 5px;">L</th>
                            <th style="padding:12px 5px; text-align:right;">PTS</th>
                        </tr>
                    </thead>
                    <tbody>`;

        let pos = 1;
        snapshot.forEach((doc) => {
            const p = doc.data();
            
            // Rank အလိုက် အရောင်ခွဲခြားခြင်း (Top 3 ကို Highlight ပေးရန်)
            let posColor = "#fff";
            if (pos === 1) posColor = "#FFD700"; // Gold
            else if (pos === 2) posColor = "#C0C0C0"; // Silver
            else if (pos === 3) posColor = "#CD7F32"; // Bronze

            html += `
                <tr style="border-bottom: 1px solid #222; background: ${pos % 2 === 0 ? 'rgba(255,255,255,0.02)' : 'transparent'};">
                    <td style="padding: 15px 5px; text-align:left; font-weight:bold; color: ${posColor};">
                        ${pos}
                    </td>
                    <td style="padding: 15px 5px; text-align:left;">
                        <div style="font-weight: bold; color:#fff; font-size: 0.9rem;">${p.team_name}</div>
                        <div style="font-size: 0.7rem; color: #666;">${p.manager_name}</div>
                    </td>
                    <td style="padding: 15px 5px; font-weight: 500;">${p.played || 0}</td>
                    <td style="padding: 15px 5px; color: #00ff88; font-weight: 500;">${p.wins || 0}</td>
                    <td style="padding: 15px 5px; color: #aaa;">${p.draws || 0}</td>
                    <td style="padding: 15px 5px; color: #ff4d4d;">${p.losses || 0}</td>
                    <td style="padding: 15px 5px; text-align:right; font-weight:bold; color: ${divTag === 'A' ? '#D4AF37' : '#C0C0C0'}; font-size: 1rem;">
                        ${p.h2h_points || 0}
                    </td>
                </tr>`;
            pos++;
        });

        html += `</tbody></table></div>
                 <p style="font-size: 0.65rem; color: #555; margin-top: 15px; text-align: left; padding-left: 10px;">
                    * Tie-breaker: Weekly Points (GW Points) are used if H2H points are level.
                 </p>`;
        content.innerHTML = html;
        
      }, (error) => {
          console.error("Firestore Error:", error);
          content.innerHTML = `
            <div style="color:#ff4d4d; padding:40px; font-size:0.85rem;">
                <p>⚠️ ဒေတာဆွဲယူမှု အမှားရှိနေပါသည်။</p>
                <p style="color:#666; font-size: 0.75rem;">Index ဆောက်ပြီးပါက ၁ မိနစ်ခန့် စောင့်ပေးပါရန်။</p>
            </div>`;
      });
};
