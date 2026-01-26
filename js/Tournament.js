function renderLeagues() {
    const main = document.getElementById('main-root');
    main.innerHTML = `<div class="loading">🏆 Rankings ကို ဆွဲယူနေသည်...</div>`;

    // Collection အမည် 'tw_mm_tournament' ဖြစ်ရပါမယ်
    db.collection("tw_mm_tournament")
      .orderBy("tournament_rank", "asc")
      .onSnapshot((snapshot) => {
        if (snapshot.empty) {
            main.innerHTML = `<div class="loading">Data မရှိသေးပါ။ Rules ကို Publish လုပ်ထားလား စစ်ပေးပါ။</div>`;
            return;
        }

        let html = `
            <div style="padding: 10px; animation: fadeIn 0.5s;">
                <h2 style="color: #D4AF37; text-align: center; text-transform: uppercase;">League Rankings</h2>
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
                    <td style="text-align: center; font-weight: bold;">${p.tournament_rank}</td>
                    <td>
                        <div style="color: #D4AF37; font-weight: bold;">${p.team_name}</div>
                        <div style="font-size: 0.75rem; color: #888;">${p.manager_name}</div>
                    </td>
                    <td style="text-align: right; font-weight: bold;">${p.fpl_total_points.toLocaleString()}</td>
                </tr>`;
        });

        html += `</tbody></table></div>`;
        main.innerHTML = html;
    }, (error) => {
        main.innerHTML = `<div class="loading" style="color:red;">Error: ${error.message}</div>`;
    })
        ;
}
