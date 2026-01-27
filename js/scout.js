/**
 * Scout Tab Main Logic
 */
window.renderScout = async function() {
    const mainRoot = document.getElementById('main-root');
    mainRoot.innerHTML = `
        <div class="loading"><div class="spinner"></div><p>Scout Data များ ရယူနေသည်...</p></div>
    `;

    try {
        // --- ၁။ UI Structure ---
        mainRoot.innerHTML = `
            <div id="scout-header" style="margin-bottom: 20px;">
                <h3 class="gold-text">🔭 SCOUT CENTER</h3>
                <div style="display: flex; gap: 10px; margin-bottom: 15px;">
                    <button id="btn-scout-players" class="primary-btn" style="flex:1; font-size:0.8rem;" onclick="window.showScoutSection('players')">PLAYER SCOUT</button>
                    <button id="btn-scout-leagues" class="primary-btn" style="flex:1; font-size:0.8rem; background:#222; color:#fff;" onclick="window.showScoutSection('leagues')">LEAGUE SCOUT</button>
                </div>
            </div>

            <div id="scout-content-area"></div>
        `;

        // အစပိုင်းမှာ Player Section ကို အရင်ပြမယ်
        window.showScoutSection('players');

    } catch (e) { console.error(e); window.showToast("Data Load Error", "error"); }
};

/**
 * Section ပြောင်းလဲခြင်း (Players vs Leagues)
 */
window.showScoutSection = function(section) {
    const container = document.getElementById('scout-content-area');
    const btnP = document.getElementById('btn-scout-players');
    const btnL = document.getElementById('btn-scout-leagues');

    if(section === 'players') {
        btnP.style.background = "var(--gold)"; btnP.style.color = "#000";
        btnL.style.background = "#222"; btnL.style.color = "#fff";
        renderPlayerTable();
    } else {
        btnL.style.background = "var(--gold)"; btnL.style.color = "#000";
        btnP.style.background = "#222"; btnP.style.color = "#fff";
        renderLeagueSection();
    }
};

/**
 * ၂။ Player Scout Table (Sorting ပါဝင်သော)
 */
async function renderPlayerTable() {
    const container = document.getElementById('scout-content-area');
    container.innerHTML = `<div class="spinner" style="margin:20px auto;"></div>`;

    const snapshot = await db.collection("scout_players").orderBy("total_points", "desc").limit(50).get();
    let players = [];
    snapshot.forEach(doc => players.push({id: doc.id, ...doc.data()}));

    container.innerHTML = `
        <table class="scout-table" id="player-table">
            <thead>
                <tr>
                    <th align="left">PLAYER</th>
                    <th onclick="window.sortPlayer('gw')" style="cursor:pointer">GW ▽</th>
                    <th onclick="window.sortPlayer('total')" style="cursor:pointer">OVERALL ▽</th>
                    <th>PRICE</th>
                </tr>
            </thead>
            <tbody id="player-body"></tbody>
        </table>
    `;
    window.currentPlayers = players;
    renderPlayerRows(players);
}

function renderPlayerRows(players) {
    const body = document.getElementById('player-body');
    body.innerHTML = players.map(p => `
        <tr onclick="window.showPlayerDetail('${p.id}')">
            <td>
                <div style="font-weight:bold;">${p.name}</div>
                <div style="font-size:0.65rem; color:#888;">${p.team} | ${p.pos}</div>
            </td>
            <td align="center">${p.form || 0}</td>
            <td align="center" style="color:var(--gold); font-weight:bold;">${p.total_points}</td>
            <td align="center">£${p.price}m</td>
        </tr>
    `).join('');
}

// Player Sorting
window.sortPlayer = (type) => {
    const sorted = [...window.currentPlayers].sort((a, b) => 
        type === 'gw' ? b.form - a.form : b.total_points - a.total_points
    );
    renderPlayerRows(sorted);
};

/**
 * ၃။ Player Detail Popup
 */
window.showPlayerDetail = async (id) => {
    const p = window.currentPlayers.find(x => x.id === id);
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.onclick = () => modal.remove();
    
    modal.innerHTML = `
        <div class="modal-content profile-card" style="max-width:350px;" onclick="event.stopPropagation()">
            <h2 class="gold-text">${p.name}</h2>
            <p style="margin-top:-10px; color:#888;">${p.team} (${p.pos})</p>
            <div class="profile-info" style="display:grid; grid-template-columns:1fr 1fr; gap:10px; text-align:left;">
                <div class="info-item"><span class="label">Goals:</span> <span>${p.goals || 0}</span></div>
                <div class="info-item"><span class="label">Assists:</span> <span>${p.assists || 0}</span></div>
                <div class="info-item"><span class="label">xG:</span> <span>${p.xg || 0.0}</span></div>
                <div class="info-item"><span class="label">ICT:</span> <span>${p.ict || 0.0}</span></div>
                <div class="info-item"><span class="label">Bonus:</span> <span>${p.bonus || 0}</span></div>
                <div class="info-item"><span class="label">CS:</span> <span>${p.clean_sheets || 0}</span></div>
                <div class="info-item"><span class="label">Yellow:</span> <span>${p.yellow_cards || 0}</span></div>
                <div class="info-item"><span class="label">Red:</span> <span>${p.red_cards || 0}</span></div>
            </div>
            <button class="primary-btn" onclick="this.parentElement.parentElement.remove()">CLOSE</button>
        </div>
    `;
    document.body.appendChild(modal);
};

/**
 * ၄။ League Scout Section (Manager 50)
 */
async function renderLeagueSection() {
    const container = document.getElementById('scout-content-area');
    container.innerHTML = `
        <div style="display:flex; gap:5px; margin-bottom:15px;">
            <button id="l-tab-a" class="primary-btn" style="flex:1; font-size:0.7rem;" onclick="window.fetchLeagueTable('League_A')">LEAGUE A</button>
            <button id="l-tab-b" class="primary-btn" style="flex:1; font-size:0.7rem; background:#222;" onclick="window.fetchLeagueTable('League_B')">LEAGUE B</button>
        </div>
        <div id="league-table-root"></div>
    `;
    window.fetchLeagueTable('League_A');
}

window.fetchLeagueTable = async (leagueKey) => {
    const root = document.getElementById('league-table-root');
    const btnA = document.getElementById('l-tab-a');
    const btnB = document.getElementById('l-tab-b');

    // Tab Style
    btnA.style.background = leagueKey === 'League_A' ? 'var(--gold)' : '#222';
    btnB.style.background = leagueKey === 'League_B' ? 'var(--gold)' : '#222';

    root.innerHTML = `<div class="spinner" style="margin:20px auto;"></div>`;

    const snapshot = await db.collection(`scout_${leagueKey}`).orderBy("total_points", "desc").limit(50).get();
    let teams = [];
    snapshot.forEach(doc => teams.push(doc.data()));

    root.innerHTML = `
        <table class="scout-table">
            <thead>
                <tr>
                    <th align="left">TEAM/MANAGER</th>
                    <th onclick="window.sortLeague('gw')" style="cursor:pointer">GW</th>
                    <th onclick="window.sortLeague('total')" style="cursor:pointer">TOTAL ▽</th>
                </tr>
            </thead>
            <tbody id="league-body"></tbody>
        </table>
    `;
    window.currentLeagues = teams;
    renderLeagueRows(teams);
};

function renderLeagueRows(teams) {
    const body = document.getElementById('league-body');
    body.innerHTML = teams.map(t => `
        <tr onclick="window.showTeamPitch('${t.entry_id}')">
            <td>
                <div style="font-weight:bold;">${t.team_name}</div>
                <div style="font-size:0.65rem; color:#888;">${t.manager}</div>
            </td>
            <td align="center">${t.gw_points}</td>
            <td align="center" style="color:var(--gold); font-weight:bold;">${t.total_points}</td>
        </tr>
    `).join('');
}

/**
 * ၅။ Team Pitch View Popup (Formation & Chips)
 */
window.showTeamPitch = (entryId) => {
    const t = window.currentLeagues.find(x => x.entry_id == entryId);
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.onclick = () => modal.remove();

    const lineup = t.lineup || [];
    const starters = lineup.slice(0, 11);
    const subs = lineup.slice(11, 15);

    modal.innerHTML = `
        <div class="modal-content profile-card" style="width:95%; max-width:450px; background:#0a2d0a; border: 2px solid var(--gold);" onclick="event.stopPropagation()">
            <div style="text-align:left; margin-bottom:15px;">
                <h3 style="margin:0;">${t.team_name}</h3>
                <span style="font-size:0.7rem; background:var(--gold); color:#000; padding:2px 6px; border-radius:4px; font-weight:bold;">
                    ${t.active_chip || 'No Chip'}
                </span>
                <span style="font-size:0.7rem; color:#ff4d4d; margin-left:10px;">Hits: ${t.transfer_cost}</span>
            </div>

            <div style="background: rgba(255,255,255,0.1); border-radius:10px; padding:15px; display:grid; grid-template-columns: repeat(5, 1fr); gap:10px; border:1px solid #ffffff33;">
                ${starters.map(p => `
                    <div style="text-align:center;">
                        <div style="font-size:1.2rem;">${p.is_captain ? '👑' : '👕'}</div>
                        <div style="font-size:0.6rem; font-weight:bold; white-space:nowrap; overflow:hidden;">${p.name}</div>
                        <div style="font-size:0.55rem; color:var(--gold);">${p.points}pts</div>
                    </div>
                `).join('')}
            </div>

            <div style="margin-top:15px; display:flex; justify-content:center; gap:10px; background:#00000055; padding:10px; border-radius:8px;">
                ${subs.map(p => `
                    <div style="text-align:center; opacity:0.7;">
                        <div style="font-size:0.8rem;">🪑</div>
                        <div style="font-size:0.55rem;">${p.name}</div>
                    </div>
                `).join('')}
            </div>

            <button class="primary-btn" style="margin-top:20px; background:#fff; color:#000;" onclick="this.parentElement.parentElement.remove()">BACK TO TABLE</button>
        </div>
    `;
    document.body.appendChild(modal);
};
