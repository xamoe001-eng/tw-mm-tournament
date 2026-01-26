// Function ကို Window Level မှာ ကြေညာမှ HTML က လှမ်းခေါ်လို့ရမှာပါ
window.renderLeagues = function() {
    const mainRoot = document.getElementById('main-root');
    if (!mainRoot) return;

    mainRoot.innerHTML = `
        <div style="text-align: center; padding: 15px;">
            <div style="margin-bottom: 20px;">
                <button id="btn-divA" onclick="filterDivision('A')" class="nav-btn" style="background:#D4AF37; color:black; margin:5px; border-radius: 20px; padding: 10px 20px; cursor:pointer; border:none; font-weight:bold;">Division 1</button>
                <button id="btn-divB" onclick="filterDivision('B')" class="nav-btn" style="background:#C0C0C0; color:black; margin:5px; border-radius: 20px; padding: 10px 20px; cursor:pointer; border:none; font-weight:bold;">Division 2</button>
            </div>
            <div id="league-content" style="min-height: 200px;">
                <div class="loading">🏆 Rankings ကို ဆွဲယူနေသည်...</div>
            </div>
        </div>
    `;

    // စဖွင့်ချင်း Division A ကို အလိုအလျောက် ခေါ်ခိုင်းမယ်
    setTimeout(() => { window.filterDivision('A'); }, 100);
};

window.filterDivision = function(divTag) {
    const content = document.getElementById('league-content');
    if (!content) return;

    // Loading ပြမယ်
    content.innerHTML = `<div class="loading" style="color:#D4AF37;">Loading Division ${divTag}...</div>`;

    // Firestore Query
    db.collection("tw_mm_tournament")
      .where("league_tag", "==", divTag)
      .orderBy("tournament_rank", "asc")
      .onSnapshot((snapshot) => {
        if (snapshot.empty) {
            content.innerHTML = `<div style="padding:40px; color:#888;">Division ${divTag} မှာ အချက်အလက် မရှိသေးပါ။</div>`;
            return;
        }

        let html = `
            <h2 style="color: ${divTag === 'A' ? '#D4AF37' : '#C0C0C0'}; text-align: center; margin: 15px 0; font-size: 1.2rem;">
                DIVISION ${divTag === 'A' ? '1' : '2'}
            </h2>
            <table class="gold-table" style="width:100%; border-collapse: collapse;">
                <thead>
                    <tr style="text-align:left; border-bottom: 1px solid #444;">
                        <th style="padding:10px;">Rank</th>
                        <th style="padding:10px;">Team & Manager</th>
                        <th style="padding:10px; text-align: right;">Pts</th>
                    </tr>
                </thead>
                <tbody>`;

        snapshot.forEach((doc) => {
            const p = doc.data();
            html += `
                <tr style="border-bottom: 1px solid #222;">
                    <td style="padding: 12px 10px; font-weight: bold; color: ${divTag === 'A' ? '#D4AF37' : '#C0C0C0'};">#${p.tournament_rank}</td>
                    <td style="padding: 12px 10px;">
                        <div style="font-weight: bold; color:#fff;">${p.team_name}</div>
                        <div style="font-size: 0.75rem; color: #888;">${p.manager_name}</div>
                    </td>
                    <td style="padding: 12px 10px; text-align: right; font-weight: bold; color:#fff;">${p.fpl_total_points.toLocaleString()}</td>
                </tr>`;
        });

        html += `</tbody></table>`;
        content.innerHTML = html;
        
      }, (error) => {
          console.error("Firestore Error:", error);
          content.innerHTML = `<div style="color:red; padding:20px;">Error: Data ဆွဲယူ၍ မရပါ။ (Console တွင် Index Error ရှိမရှိ စစ်ပါ)</div>`;
     
      });
};
