/**
 * ၁။ Tournament Standings Render လုပ်ခြင်း
 */
window.renderLeagues = function() {
    const mainRoot = document.getElementById('main-root');
    if (!mainRoot) return;

    // Table Design အတွက် CSS Inject လုပ်ခြင်း
    const leagueStyle = document.createElement('style');
    leagueStyle.innerHTML = `
        .league-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            color: #eee;
            font-size: 0.8rem;
        }
        .league-table th {
            text-align: center;
            padding: 10px 5px;
            color: #555;
            font-size: 0.65rem;
            text-transform: uppercase;
            border-bottom: 1px solid #222;
        }
        .league-table td {
            padding: 12px 5px;
            border-bottom: 1px solid #1a1a1a;
            vertical-align: middle;
        }
        .rank-cell { width: 30px; font-weight: 900; text-align: center; font-size: 0.9rem; }
        .team-cell { text-align: left !important; padding-left: 10px !important; }
        .team-title { font-weight: 800; color: #fff; display: block; max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .mgr-title { font-size: 0.65rem; color: #555; }
        .stat-cell { text-align: center; width: 45px; font-family: 'Monaco', monospace; }
        .gw-box { color: #00ff88; font-weight: bold; }
        .pts-box { font-weight: 900; font-size: 1.1rem; }
        
        /* W-D-L Colors */
        .w-text { color: #00ff88; font-weight: bold; } /* နိုင် - အစိမ်း */
        .d-text { color: #ffcc00; font-weight: bold; } /* သရေ - အဝါ */
        .l-text { color: #ff4d4d; font-weight: bold; } /* ရှုံး - အနီ */
        .dash { color: #444; margin: 0 1px; }
    `;
    document.head.appendChild(leagueStyle);

    mainRoot.innerHTML = `
        <div style="padding: 12px; max-width: 500px; margin: 0 auto; font-family: 'Inter', sans-serif; background: #000; min-height: 100vh;">
            <div style="display: flex; background: #111; padding: 4px; border-radius: 12px; margin-bottom: 15px; border: 1px solid #222;">
                <button id="btn-divA" onclick="window.filterDivision('A')" 
                    style="flex: 1; padding: 12px; border: none; border-radius: 10px; font-weight: 800; cursor: pointer; transition: 0.3s; background: #D4AF37; color: #000; font-size: 0.75rem;">
                    DIVISION 1
                </button>
                <button id="btn-divB" onclick="window.filterDivision('B')" 
                    style="flex: 1; padding: 12px; border: none; border-radius: 10px; font-weight: 800; cursor: pointer; transition: 0.3s; background: transparent; color: #666; font-size: 0.75rem;">
                    DIVISION 2
                </button>
            </div>
            
            <div id="league-content" style="background: #0a0a0a; border-radius: 15px; border: 1px solid #111; padding: 5px;"></div>
        </div>
    `;
    setTimeout(() => { window.filterDivision('A'); }, 100);
};

/**
 * ၂။ Division အလိုက် ဒေတာပြသခြင်း
 */
window.filterDivision = function(divTag) {
    const content = document.getElementById('league-content');
    const btnA = document.getElementById('btn-divA');
    const btnB = document.getElementById('btn-divB');
    if (!content) return;

    if (divTag === 'A') {
        btnA.style.background = '#D4AF37'; btnA.style.color = '#000';
        btnB.style.background = 'transparent'; btnB.style.color = '#666';
    } else {
        btnB.style.background = '#C0C0C0'; btnB.style.color = '#000';
        btnA.style.background = 'transparent'; btnA.style.color = '#666';
    }

    db.collection("tw_mm_tournament")
      .where("league_tag", "==", divTag)
      .orderBy("h2h_points", "desc") 
      .orderBy("gw_points", "desc") 
      .onSnapshot((snapshot) => {
        if (snapshot.empty) {
            content.innerHTML = `<div style="text-align:center; padding:50px; color:#444; font-size: 0.8rem;">NO DATA AVAILABLE</div>`;
            return;
        }

        let html = `
            <table class="league-table">
                <thead>
                    <tr>
                        <th class="rank-cell">#</th>
                        <th class="team-cell">TEAM / MGR</th>
                        <th class="stat-cell">GW</th>
                        <th class="stat-cell" style="width: 70px;">P / W-D-L</th>
                        <th class="stat-cell">PTS</th>
                    </tr>
                </thead>
                <tbody>
        `;

        let pos = 1;
        snapshot.forEach((doc) => {
            const p = doc.data();
            const rankColor = pos === 1 ? '#D4AF37' : (pos === 2 ? '#C0C0C0' : (pos === 3 ? '#CD7F32' : '#666'));
            const ptsColor = divTag === 'A' ? '#D4AF37' : '#C0C0C0';

            html += `
                <tr>
                    <td class="rank-cell" style="color: ${rankColor};">${pos}</td>
                    <td class="team-cell">
                        <span class="team-title">${p.team_name || 'Unknown'}</span>
                        <span class="mgr-title">${p.manager_name || 'User'}</span>
                    </td>
                    <td class="stat-cell gw-box">${p.gw_points || 0}</td>
                    <td class="stat-cell">
                        <div style="color: #bbb; font-weight: bold; font-size: 0.75rem; margin-bottom: 2px;">${p.played || 0}</div>
                        <div style="font-size: 0.65rem;">
                            <span class="w-text">${p.wins || 0}</span><span class="dash">-</span><span class="d-text">${p.draws || 0}</span><span class="dash">-</span><span class="l-text">${p.losses || 0}</span>
                        </div>
                    </td>
                    <td class="stat-cell pts-box" style="color: ${ptsColor};">${p.h2h_points || 0}</td>
                </tr>
            `;
            pos++;
        });

        html += `</tbody></table>`;
        content.innerHTML = html;
    
      });
};
