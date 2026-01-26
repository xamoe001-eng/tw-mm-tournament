/**
 * Firebase Firestore မှ Tournament Rankings များကို ဆွဲယူပြသခြင်း
 */
function renderLeagues() {
    const main = document.getElementById('main-root');
    
    // Loading ပြထားမယ်
    main.innerHTML = `
        <div class="loading">
            <p>🏆 League Rankings ဆွဲယူနေသည်...</p>
            <div style="font-size: 0.8rem; color: #888;">Firestore ချိတ်ဆက်နေပါသည်</div>
        </div>`;

    // Real-time Update ဖြစ်အောင် onSnapshot သုံးထားပါတယ်
    db.collection("tw_mm_tournament")
      .orderBy("tournament_rank", "asc")
      .onSnapshot((snapshot) => {
        
        if (snapshot.empty) {
            main.innerHTML = `
                <div class="loading">
                    <p>Database ထဲမှာ Data မရှိသေးပါ</p>
                    <small>Collection: tw_mm_tournament ကို စစ်ဆေးပါ</small>
                </div>`;
            return;
        }

        // Data များကို Array အဖြစ် ပြောင်းလဲခြင်း
        let players = snapshot.docs.map(doc => {
            const data = doc.data();
            return {
                rank: data.tournament_rank || 0,
                team: data.team_name || 'No Team Name',
                manager: data.manager_name || 'Unknown',
                points: data.fpl_total_points || 0
            };
        });

        // League A (Rank 1-24) နှင့် League B (Rank 25-48) ခွဲခြားခြင်း
        const leagueA = players.filter(p => p.rank <= 24);
        const leagueB = players.filter(p => p.rank > 24);

        main.innerHTML = `
            <div class="tournament-container" style="animation: fadeIn 0.5s ease-in;">
                <h2 style="color: #D4AF37; text-align: center; letter-spacing: 2px;">🏆 LEAGUE A (TOP 24)</h2>
                ${generateTableMarkup(leagueA)}
                
                <h2 style="color: #D4AF37; text-align: center; margin-top: 50px; letter-spacing: 2px;">🛡️ LEAGUE B (RANK 25-48)</h2>
                ${generateTableMarkup(leagueB)}
            </div>
        `;
    }, (error) => {
        console.error("Firestore Error:", error);
        main.innerHTML = `<div class="loading" style="color: #ff4444;">Error: ${error.message}</div>`;
    });
}

/**
 * Rankings Table HTML ဆောက်ပေးသည့် Function
 */
function generateTableMarkup(data) {
    if (data.length === 0) {
        return `<p style="text-align:center; color: #666; padding: 20px;">ဤ League အတွက် Data မရှိသေးပါ။</p>`;
    }

    return `
        <div style="overflow-x: auto; margin-top: 15px;">
            <table class="gold-table">
                <thead>
                    <tr>
                        <th style="width: 60px; text-align: center;">RANK</th>
                        <th>TEAM & MANAGER</th>
                        <th style="text-align: right;">POINTS</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.map(p => `
                        <tr>
                            <td style="text-align: center; font-weight: bold; color: ${p.rank <= 3 ? '#D4AF37' : 'white'};">
                                ${p.rank}
                            </td>
                            <td>
                                <div style="color: #D4AF37; font-weight: bold;">${p.team}</div>
                                <div style="font-size: 0.75rem; color: #888;">${p.manager}</div>
                            </td>
                            <td style="text-align: right; font-weight: bold; font-family: 'Courier New', monospace;">
                                ${p.points.toLocaleString()}
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
   
    `;
}
