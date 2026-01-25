function renderLeagues() {
    const main = document.getElementById('main-root');
    main.innerHTML = `<div class="loading">League Rankings ဆွဲယူနေသည်...</div>`;

    // Python က ပို့ထားတဲ့ Database မှ Data ကို ခေါ်ယူခြင်း
    db.collection("tw_mm_tournament").orderBy("tournament_rank", "asc").get().then(snapshot => {
        if (snapshot.empty) {
            main.innerHTML = `<div class="loading">Data မရှိသေးပါ (Python Sync ကို အရင်စစ်ပါ)</div>`;
            return;
        }

        let players = snapshot.docs.map(doc => doc.data());
        
        // League A နဲ့ B ကို Rank အလိုက် ခွဲခြားခြင်း
        let leagueA = players.slice(0, 24);
        let leagueB = players.slice(24, 48);

        main.innerHTML = `
            <div style="padding: 10px;">
                <h2 style="color: #D4AF37; text-align: center;">LEAGUE A (TOP 24)</h2>
                ${generateTableMarkup(leagueA)}
                
                <h2 style="color: #D4AF37; text-align: center; margin-top: 40px;">LEAGUE B (RANK 25-48)</h2>
                ${generateTableMarkup(leagueB)}
            </div>
        `;
    }).catch(err => {
        main.innerHTML = `<div class="loading" style="color: red;">Error: ${err.message}</div>`;
    });
}

function generateTableMarkup(data) {
    return `
        <table class="gold-table">
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Team Name</th>
                    <th>Manager</th>
                    <th>Points</th>
                </tr>
            </thead>
            <tbody>
                ${data.map(p => `
                    <tr>
                        <td>${p.tournament_rank}</td>
                        <td style="color: #D4AF37; font-weight: bold;">${p.team_name}</td>
                        <td>${p.manager_name}</td>
                        <td>${p.fpl_total_points}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `
      ;
}
