// js/tournament.js
window.renderLeagues = function() {
    const mainRoot = document.getElementById('main-root');
    if (!mainRoot) return;
    
    mainRoot.innerHTML = `<div class="loading">🏆 Rankings ကို ဆွဲယူနေသည်...</div>`;

    // Collection အမည် မှန်/မမှန် ပြန်စစ်ပါ (tw_mm_tournament)
    db.collection("tw_mm_tournament")
      .orderBy("tournament_rank", "asc")
      .onSnapshot((snapshot) => {
        if (snapshot.empty) {
            mainRoot.innerHTML = `<div class="loading">Data မရှိသေးပါ။ Firebase Rules ကို စစ်ပါ။</div>`;
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
                    <td style="text-align: center; font-weight: bold; color: #D4AF37;">${p.tournament_rank || '-'}</td>
                    <td>
                        <div style="font-weight: bold;">${p.team_name || 'No Name'}</div>
                        <div style="font-size: 0.75rem; color: #888;">${p.manager_name || 'Unknown'}</div>
                    </td>
                    <td style="text-align: right; font-weight: bold;">${(p.fpl_total_points || 0).toLocaleString()}</td>
                </tr>`;
        });

        html += `</tbody></table></div>`;
        mainRoot.innerHTML = html;
    }, (error) => {
        console.error("Firestore Error:", error);
        mainRoot.innerHTML = `<div class="loading" style="color:red;">Error: ${error.message}</div>`;
    });
    
};
