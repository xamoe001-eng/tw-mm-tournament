// js/tournament.js
function renderLeagues() {
    const mainRoot = document.getElementById('main-root');
    mainRoot.innerHTML = `<div class="loading">🏆 Rankings ကို ဆွဲယူနေသည်...</div>`;

    // Real-time listener သုံးထားလို့ Data အသစ်ရောက်တာနဲ့ တန်းပြောင်းမယ်
    db.collection("tw_mm_tournament")
      .orderBy("tournament_rank", "asc")
      .onSnapshot((snapshot) => {
        if (snapshot.empty) {
            mainRoot.innerHTML = `<div class="loading">Data မရှိသေးပါ။ (Firebase Rules ကို စစ်ပါ)</div>`;
            return;
        }

        let html = `
            <div style="padding: 10px; animation: fadeIn 0.5s;">
                <h2 style="color: #D4AF37; text-align: center; margin-bottom: 20px;">LEAGUE RANKINGS</h2>
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

        html += `</tbody></table></div>`;
        mainRoot.innerHTML = html;
    }, (error) => {
        console.error("Firestore Error:", error);
        mainRoot.innerHTML = `<div class="loading" style="color:red;">Error: ${error.message}</div>`;
    })
        ;
}
