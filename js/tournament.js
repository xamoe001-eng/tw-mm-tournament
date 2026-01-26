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
                <div class="loading">🏆 Rankings ကို ဆွဲယူနေသည်...</div>
            </div>
        </div>
    `;

    // စဖွင့်ဖွင့်ချင်း Division 1 (A) ကို အလိုအလျောက် ပြခိုင်းမယ်
    setTimeout(() => { window.filterDivision('A'); }, 100);
};

// ၂။ ခလုတ်နှိပ်လိုက်ရင် Division အလိုက် Filter လုပ်ပေးမယ့် Function
window.filterDivision = function(divTag) {
    console.log("Filtering Division:", divTag);
    const content = document.getElementById('league-content');
    if (!content) return;

    // Loading အရင်ပြမယ်
    content.innerHTML = `<div class="loading" style="color:#D4AF37;">Division ${divTag} အချက်အလက်များ ရှာနေသည်...</div>`;

    // Firestore Database ထဲက league_tag (A သို့မဟုတ် B) ကို ရှာခြင်း
    db.collection("tw_mm_tournament")
      .where("league_tag", "==", divTag)
      .orderBy("tournament_rank", "asc")
      .onSnapshot((snapshot) => {
        if (snapshot.empty) {
            content.innerHTML = `
                <div style="padding:40px; color:#888;">
                    <p>Division ${divTag} မှာ အချက်အလက် မတွေ့ပါ။</p>
                    <small>Python Script ကနေ league_tag: "${divTag}" လို့ ပို့ထားဖို့ လိုပါတယ်။</small>
                </div>`;
            return;
        }

        // ဇယား (Table) စတင်တည်ဆောက်ခြင်း
        let html = `
            <h2 style="color: ${divTag === 'A' ? '#D4AF37' : '#C0C0C0'}; margin-bottom: 15px; font-size: 1.2rem;">
                DIVISION ${divTag === 'A' ? '1' : '2'} RANKINGS
            </h2>
            <table class="gold-table" style="width:100%; border-collapse: collapse; text-align: left;">
                <thead>
                    <tr style="border-bottom: 2px solid #444; color: #888; font-size: 0.8rem;">
                        <th style="padding:10px;">RANK</th>
                        <th style="padding:10px;">TEAM & MANAGER</th>
                        <th style="padding:10px; text-align: right;">PTS</th>
                    </tr>
                </thead>
                <tbody>`;

        // စဉ်စီနံပါတ်အတွက် ၁ ကနေ စသတ်မှတ်ခြင်း
        let serialNo = 1;

        snapshot.forEach((doc) => {
            const p = doc.data();
            
            // Division 2 (B) ဆိုလျှင် serialNo (1,2,3...) ကိုပြမည်၊ 
            // Division 1 (A) ဆိုလျှင် rank အစစ် (1-24) အတိုင်းပြမည်
            const displayRank = (divTag === 'B') ? serialNo : p.tournament_rank;

            html += `
                <tr style="border-bottom: 1px solid #222;">
                    <td style="padding: 15px 10px; font-weight: bold; color: ${divTag === 'A' ? '#D4AF37' : '#C0C0C0'};">
                        #${displayRank}
                    </td>
                    <td style="padding: 15px 10px;">
                        <div style="font-weight: bold; color:#fff;">${p.team_name}</div>
                        <div style="font-size: 0.75rem; color: #888;">${p.manager_name}</div>
                    </td>
                    <td style="padding: 15px 10px; text-align: right; font-weight: bold; color:#fff;">
                        ${p.fpl_total_points.toLocaleString()}
                    </td>
                </tr>`;
            
            // တစ်ကြောင်းပြီးတိုင်း နံပါတ်ကို ၁ တိုးပေးသွားမည်
            serialNo++;
        });

        html += `</tbody></table>`;
        content.innerHTML = html;
        
      }, (error) => {
          console.error("Firestore Error:", error);
          content.innerHTML = `
            <div style="color:#ff4444; padding:20px; font-size: 0.8rem; border: 1px dashed #ff4444; border-radius: 10px;">
                <strong>Database Error!</strong><br>
                Rank စီရန် Index လိုအပ်နေသည်။ Browser Console (F12) ရှိ Link ကို နှိပ်၍ Index ဆောက်ပေးပါ။
            </div>`;
      });
};
