// js/tournament.js
window.renderLeagues = function() {
    const mainRoot = document.getElementById('main-root');
    if (!mainRoot) return;
    
    mainRoot.innerHTML = `<div class="loading">🏆 Rankings ကို ဆွဲယူနေသည်...</div>`;

    // Python က တင်ပေးလိုက်တဲ့ Collection နာမည် tw_mm_tournament ကို သုံးပါမယ်
    db.collection("tw_mm_tournament")
      .orderBy("tournament_rank", "asc")
      .onSnapshot((snapshot) => {
        if (snapshot.empty) {
            mainRoot.innerHTML = `<div class="loading">Database မှာ Data မရှိသေးပါ။</div>`;
            return;
        }

        let html = `
            <div style="padding: 10px; animation: fadeIn 0.5s;">
                <h2 style="color: #D4AF37; text-align: center; margin-bottom: 20px;">TW MM TOURNAMENT</h2>
                <table class="gold-table">
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Team & Manager</th>
                            <th style="text-align: center;">League</th>
                            <th style="text-align: right;">Points</th>
                        </tr>
                    </thead>
                    <tbody>`;

        snapshot.forEach((doc) => {
            const p = doc.data();
            // League A ဆိုရင် ရွှေရောင်၊ B ဆိုရင် ငွေရောင် သတ်မှတ်မယ်
            const tagColor = p.league_tag === "A" ? "#D4AF37" : "#C0C0C0";

            html += `
                <tr>
                    <td style="text-align: center; font-weight: bold; color: #D4AF37;">${p.tournament_rank}</td>
                    <td>
                        <div style="font-weight: bold;">${p.team_name}</div>
                        <div style="font-size: 0.75rem; color: #888;">${p.manager_name}</div>
                    </td>
                    <td style="text-align: center;">
                        <span style="background: ${tagColor}; color: black; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: bold;">
                            L-${p.league_tag}
                        </span>
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
};
