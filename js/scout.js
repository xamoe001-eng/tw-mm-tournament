/**
 * Scout Tab Main Logic
 */
window.renderScout = async function() {
    const mainRoot = document.getElementById('main-root');
    mainRoot.innerHTML = `<div class="loading"><div class="spinner"></div><p>Scout Data များ ရယူနေသည်...</p></div>`;

    try {
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
        window.showScoutSection('players');
    } catch (e) { console.error(e); window.showToast("Data Load Error", "error"); }
};

/**
 * Section Switcher
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
 * ၂။ Player Table (Ownership ပါဝင်သော)
 */
async function renderPlayerTable() {
    const container = document.getElementById('scout-content-area');
    container.innerHTML = `<div class="spinner" style="margin:20px auto;"></div>`;

    const snapshot = await db.collection("scout_players").orderBy("total_points", "desc").limit(50).get();
    let players = [];
    snapshot.forEach(doc => players.push({id: doc.id, ...doc.data()}));
    window.currentPlayers = players;

    container.innerHTML = `
        <table class="scout-table">
            <thead>
                <tr>
                    <th align="left">PLAYER</th>
                    <th onclick="window.sortPlayer('gw')" style="cursor:pointer">GW ▽</th>
                    <th onclick="window.sortPlayer('total')" style="cursor:pointer">TOT ▽</th>
                    <th>OWN%</th>
                    <th>PRICE</th>
                </tr>
            </thead>
            <tbody id="player-body"></tbody>
        </table>
    `;
    renderPlayerRows(players);
}

function renderPlayerRows(players) {
    const body = document.getElementById('player-body');
    body.innerHTML = players.map(p => `
        <tr onclick="window.showPlayerDetail('${p.id}')">
            <td>
                <div style="font-weight:bold;">${p.name}</div>
                <div style="font-size:0.6rem; color:#888;">${p.team} | ${p.pos}</div>
            </td>
            <td align="center">${p.form || p.gw_points || 0}</td>
            <td align="center" style="color:var(--gold); font-weight:bold;">${p.total_points}</td>
            <td align="center" style="font-size:0.75rem;">${p.selected_by_percent || '0.0'}%</td>
            <td align="center">£${p.price}m</td>
        </tr>
    `).join('');
}

window.sortPlayer = (type) => {
    const sorted = [...window.currentPlayers].sort((a, b) => 
        type === 'gw' ? (b.form || b.gw_points) - (a.form || a.gw_points) : b.total_points - a.total_points
    );
    renderPlayerRows(sorted);
};

/**
 * ၃။ Player Popup (Stats + Next 3 Matches)
 */
window.showPlayerDetail = async (id) => {
    const p = window.currentPlayers.find(x => x.id === id);
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.onclick = () => modal.remove();
    
    modal.innerHTML = `
        <div class="modal-content profile-card" style="max-width:360px;" onclick="event.stopPropagation()">
            <h2 class="gold-text" style="margin:0;">${p.name}</h2>
            <p style="color:#888; font-size:0.8rem; margin-bottom:15px;">${p.team} - ${p.pos}</p>
            
            <div class="profile-info">
                <div class="info-item"><span class="label">Goals:</span> <span class="val">${p.goals || 0}</span></div>
                <div class="info-item"><span class="label">Assists:</span> <span class="val">${p.assists || 0}</span></div>
                <div class="info-item"><span class="label">Bonus:</span> <span class="val">${p.bonus || 0}</span></div>
                <div class="info-item"><span class="label">CS:</span> <span class="val">${p.clean_sheets || 0}</span></div>
                <div class="info-item"><span class="label">xG:</span> <span class="val">${p.xg || 0.0}</span></div>
                <div class="info-item"><span class="label">ICT:</span> <span class="val">${p.ict || 0.0}</span></div>
            </div>

            <h4 class="gold-text" style="text-align:left; margin:15px 0 8px 0; font-size:0.8rem;">🗓 NEXT 3 MATCHES</h4>
            <div style="display:flex; gap:8px; margin-bottom:20px;">
                ${(p.next_fixtures || ['TBA', 'TBA', 'TBA']).slice(0,3).map(f => `
                    <div style="flex:1; background:#000; padding:8px; border-radius:8px; border:1px solid #333; font-size:0.7rem;">
                        <div style="font-weight:bold;">${f.opponent || f}</div>
                    </div>
                `).join('')}
            </div>
            <button class="primary-btn" onclick="this.parentElement.parentElement.remove()">CLOSE</button>
        </div>
    `;
    document.body.appendChild(modal);
};

/**
 * ၄။ League Table
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
    document.getElementById('l-tab-a').style.background = leagueKey === 'League_A' ? 'var(--gold)' : '#222';
    document.getElementById('l-tab-b').style.background = leagueKey === 'League_B' ? 'var(--gold)' : '#222';

    root.innerHTML = `<div class="spinner" style="margin:20px auto;"></div>`;
    const snapshot = await db.collection(`scout_${leagueKey}`).orderBy("total_points", "desc").limit(50).get();
    let teams = [];
    snapshot.forEach(doc => teams.push(doc.data()));
    window.currentLeagues = teams;

    root.innerHTML = `
        <table class="scout-table">
            <thead>
                <tr>
                    <th align="left">TEAM/MANAGER</th>
                    <th onclick="window.sortLeague('gw')" style="cursor:pointer">GW ▽</th>
                    <th onclick="window.sortLeague('total')" style="cursor:pointer">TOT ▽</th>
                </tr>
            </thead>
            <tbody id="league-body"></tbody>
        </table>
    `;
    renderLeagueRows(teams);
};

window.sortLeague = (type) => {
    const sorted = [...window.currentLeagues].sort((a, b) => 
        type === 'gw' ? b.gw_points - a.gw_points : b.total_points - a.total_points
    );
    renderLeagueRows(sorted);
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
 * ၅။ Correct Formation Pitch View
 */
window.showTeamPitch = (entryId) => {
    const t = window.currentLeagues.find(x => x.entry_id == entryId);
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.onclick = () => modal.remove();

    const lineup = t.lineup || [];
    const starters = lineup.slice(0, 11);
    const subs = lineup.slice(11, 15);

    // Filter by position for proper pitch rows
    const gkp = starters.filter(p => p.pos === 'GKP');
    const def = starters.filter(p => p.pos === 'DEF');
    const mid = starters.filter(p => p.pos === 'MID');
    const fwd = starters.filter(p => p.pos === 'FWD');

    modal.innerHTML = `
        <div class="modal-content profile-card" style="width:98%; max-width:450px; background:#0a2d0a; border: 2px solid var(--gold); padding:15px;" onclick="event.stopPropagation()">
            <div style="display:flex; justify-content:space-between; margin-bottom:10px; text-align:left;">
                <div>
                    <h4 style="margin:0;">${t.team_name}</h4>
                    <div style="font-size:0.65rem; color:#ccc;">Hit: <span style="color:#ff4d4d;">${t.transfer_cost}</span></div>
                </div>
                <div style="background:var(--gold); color:#000; padding:2px 8px; border-radius:5px; font-weight:bold; font-size:0.7rem;">
                    ${t.active_chip || 'No Chip'}
                </div>
            </div>

            <div class="pitch-container" style="display:flex; flex-direction:column-reverse; justify-content:space-around; min-height:320px; border:1px solid #ffffff22; border-radius:10px;">
                <div class="pitch-row">${renderPitchPlayers(fwd)}</div>
                <div class="pitch-row">${renderPitchPlayers(mid)}</div>
                <div class="pitch-row">${renderPitchPlayers(def)}</div>
                <div class="pitch-row">${renderPitchPlayers(gkp)}</div>
            </div>

            <div style="margin-top:10px; background:rgba(0,0,0,0.4); padding:8px; border-radius:8px;">
                <div style="display:flex; justify-content:center; gap:15px;">
                    ${subs.map(p => `
                        <div style="text-align:center;">
                            <div style="font-size:1rem;">👕</div>
                            <div style="font-size:0.5rem; width:45px; overflow:hidden;">${p.name}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
            <button class="primary-btn" style="margin-top:15px; background:#fff; color:#000;" onclick="this.parentElement.parentElement.remove()">CLOSE</button>
        </div>
    `;
    document.body.appendChild(modal);
};

function renderPitchPlayers(players) {
    return players.map(p => `
        <div style="text-align:center; width:60px;">
            <div style="font-size:1.2rem; position:relative;">
                ${p.is_captain ? '<span style="position:absolute; top:-5px; right:5px; font-size:0.6rem;">©️</span>' : ''}
                👕
            </div>
            <div style="background:#000; color:#fff; font-size:0.5rem; padding:1px 2px; border-radius:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${p.name}</div>
            <div style="font-size:0.55rem; color:var(--gold); font-weight:bold;">${p.points}pts</div>
        </div>
    `).join('');
}
