/**
 * League Rankings များကို Firestore မှ ဆွဲယူပြီး Tab တွင် ပြသပေးသော Function
 */
function renderLeagues() {
    const main = document.getElementById('main-root');
    main.innerHTML = `<div class="loading">League Rankings ဆွဲယူနေသည်...</div>`;

    // .onSnapshot ကိုသုံးထားလို့ Database ပြောင်းလဲတာနဲ့ Website မှာ တန်းပေါ်ပါလိမ့်မယ်
    db.collection("tw_mm_tournament")
      .orderBy("tournament_rank", "asc")
      .onSnapshot((snapshot) => {
        
        if (snapshot.empty) {
            console.warn("No data found in 'tw_mm_tournament' collection.");
            main.innerHTML = `
                <div class="loading">
                    <p>Data မရှိသေးပါ (Python Sync ကို အရင်စစ်ပါ)</p>
                    <small style="color: gray;">Collection Name: tw_mm_tournament</small>
                </div>`;
            return;
        }

        // Data များကို Array အဖြစ် ပြောင်းလဲခြင်း
        let players = snapshot.docs.map(doc => {
            const data = doc.data();
            return {
                tournament_rank: data.tournament_rank || 0,
                team_name: data.team_name || 'Unknown Team',
                manager_name: data.manager_name || 'Unknown Manager',
                fpl_total_points: data.fpl_total_points || 0
            };
        });

        console.log("Fetched Players:", players.length);

        // League A (Rank 1-24) နှင့် League B (Rank 25-48) ခွဲခြားခြင်း
        const leagueA = players.filter(p => p.tournament_rank <= 24);
        const leagueB = players.filter(p => p.tournament_rank > 24);

        main.innerHTML = `
            <div style="padding: 10px; animation: fadeIn 0.5s;">
                <h2 style="color: #D4AF37; text-align: center; text-transform: uppercase; letter-spacing: 1px;">
                    🏆 League A (Top 24)
                </h2>
                ${generateTableMarkup(leagueA)}
                
                <h2 style="color: #D4AF37; text-align: center; margin-top: 40px; text-transform: uppercase; letter-spacing: 1px;">
                    🛡️ League B (Rank 25-48)
                </h2>
                ${generateTableMarkup(leagueB)}
            </div>
        `;
    }, (error) => {
        console.error("Firestore Error:", error);
        main.innerHTML = `<div class="loading" style="color: #ff4444;">Error: ${error.message}</div>`;
    });
}

/**
 * Table HTML ဆောက်ပေးသော Helper Function
 */
function generateTableMarkup(data) {
    if (data.length === 0) {
        return `<p style="text-align:center; color:gray; padding: 20px;">ဤ League အတွက် Data မရှိသေးပါ။</p>`;
    }

    return `
        <div style="overflow-x: auto;">
            <table class="gold-table">
                <thead>
                    <tr>
                        <th style="width: 50px;">Rank</th>
                        <th>Team & Manager</th>
                        <th style="text-align: right;">Points</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.map(p => `
                        <tr>
                            <td style="text-align: center; font-weight: bold; color: ${p.tournament_rank <= 3 ? '#D4AF37' : 'white'};">
                                ${p.tournament_rank}
                            </td>
                            <td>
                                <div style="color: #D4AF37; font-weight: bold; font-size: 0.95rem;">${p.team_name}</div>
                                <div style="color: #888; font-size: 0.8rem;">${p.manager_name}</div>
                            </td>
                            <td style="text-align: right; font-weight: bold; font-family: monospace; font-size: 1rem;">
                                ${p.fpl_total_points.toLocaleString()}
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
  
    `;
}
