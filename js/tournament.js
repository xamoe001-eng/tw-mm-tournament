// js/tournament.js
window.renderLeagues = function() {
    const mainRoot = document.getElementById('main-root');
    if (!mainRoot) return;

    // အစပိုင်းမှာ ခလုတ် ၂ ခု အရင်ပြမယ်
    mainRoot.innerHTML = `
        <div style="text-align: center; padding: 15px;">
            <button onclick="filterDivision('A')" class="nav-btn" style="background:#D4AF37; color:black; margin:5px; border-radius: 5px;">Division 1</button>
            <button onclick="filterDivision('B')" class="nav-btn" style="background:#C0C0C0; color:black; margin:5px; border-radius: 5px;">Division 2</button>
            <div id="league-content" class="loading">🏆 Rankings ကို ဆွဲယူနေသည်...</div>
        </div>
    `;

    // ပထမဆုံးဝင်ဝင်ချင်း Division 1 (A) ကို အရင်ပြထားမယ်
    window.filterDivision('A');
};

window.filterDivision = function(divTag) {
    const content = document.getElementById('league-content');
    content.innerHTML = `<div class="loading">Loading Division ${divTag}...</div>`;

    // Firestore ကနေ league_tag အလိုက် Filter လုပ်ပြီး ဆွဲထုတ်မယ်
    db.collection("tw_mm_tournament")
      .where("league_tag", "==", divTag)
      .orderBy("tournament_rank", "asc")
      .onSnapshot((snapshot) => {
        if (snapshot.empty) {
            content.innerHTML = `<div class="loading">ဒီ Division မှာ Data မရှိသေးပါ။</div>`;
            return;
        }

        let html = `
            <h2 style="color: ${divTag === 'A' ? '#D4AF37' : '#C0C0C0'}; text-align: center; margin: 15px 0;">
                DIVISION ${divTag === 'A' ? '1' : '2'}
            </h2>
            <table class="gold-table">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Team & Manager</th>
                        <th style="text-align: right;">Points</th>
                    </tr>
                </thead>
                <tbody>`;

        snapshot.forEach((doc) => {
            const p = doc.data();
            html += `
                <tr>
                    <td style="text-align: center; font-weight: bold; color: #D4AF37;">${p.tournament_rank}</td>
                    <td>
                        <div style="font-weight: bold;">${p.team_name}</div>
                        <div style="font-size: 0.75rem; color: #888;">${p.manager_name}</div>
                    </td>
                    <td style="text-align: right; font-weight: bold;">${p.fpl_total_points.toLocaleString()}</td>
                </tr>`;
        });

        html += `</tbody></table>`;
        content.innerHTML = html;
    
      });
};
