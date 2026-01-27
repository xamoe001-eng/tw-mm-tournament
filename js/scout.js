/**
 * ၁။ Scout Tab Main Render
 */
window.renderScout = async function() {
    const mainRoot = document.getElementById('main-root');
    mainRoot.innerHTML = `<div class="spinner"></div>`;

    mainRoot.innerHTML = `
        <div id="scout-header" style="margin-bottom: 20px;">
            <h3 class="gold-text">🔭 SCOUT CENTER</h3>
            <div style="display: flex; gap: 8px; margin-bottom: 15px;">
                <button id="btn-p" class="primary-btn" style="flex:1; font-size:0.75rem;" onclick="window.switchTab('p')">PLAYER SCOUT</button>
                <button id="btn-l" class="primary-btn" style="flex:1; font-size:0.75rem; background:#222; color:#888;" onclick="window.switchTab('l')">LEAGUE SCOUT</button>
            </div>
        </div>
        <div id="scout-container"></div>
    `;
    window.switchTab('p'); 
};

/**
 * ၂။ Tab Switcher Logic
 */
window.switchTab = function(tab) {
    const container = document.getElementById('scout-container');
    const btnP = document.getElementById('btn-p');
    const btnL = document.getElementById('btn-l');

    if(tab === 'p') {
        btnP.style.background = "var(--gold)"; btnP.style.color = "#000";
        btnL.style.background = "#222"; btnL.style.color = "#888";
        loadPlayerData();
    } else {
        btnL.style.background = "var(--gold)"; btnL.style.color = "#000";
        btnP.style.background = "#222"; btnP.style.color = "#888";
        loadLeagueData();
    }
};

/**
 * ၃။ Player Table (Sorting & Ownership ပါဝင်သော)
 */
async function loadPlayerData() {
    const container = document.getElementById('scout-container');
    container.innerHTML = `<div class="spinner"></div>`;

    const snapshot = await db.collection("scout_players").orderBy("total_points", "desc").limit(50).get();
    let players = [];
    snapshot.forEach(doc => players.push({id: doc.id, ...doc.data()}));
    window.allPlayers = players;

    container.innerHTML = `
        <table class="scout-table">
            <thead>
                <tr>
                    <th align="left">PLAYER</th>
                    <th onclick="window.reSortP('gw')" style="color:var(--gold)">GW ▽</th>
                    <th onclick="window.reSortP('tot')" style="color:var(--gold)">TOT ▽</th>
                    <th>OWN%</th>
                </tr>
            </thead>
            <tbody id="p-body"></tbody>
        </table>
    `;
    displayPlayerRows(players);
}

function displayPlayerRows(data) {
    const body = document.getElementById('p-body');
    body.innerHTML = data.map(p => `
        <tr onclick="window.showPDetail('${p.id}')">
            <td>
                <div style="font-weight:800; font-size:0.85rem;">${p.name}</div>
                <div style="font-size:0.6rem; color:#666;">${p.team} | ${p.pos} | £${p.price}m</div>
            </td>
            <td align="center">${p.form || p.gw_points || 0}</td>
            <td align="center" style="font-weight:bold;">${p.total_points || 0}</td>
            <td align="center" style="font-size:0.7rem; color:var(--gold);">${p.selected_by_percent || '0.0'}%</td>
        </tr>
    `).join('');
}

window.reSortP = (t) => {
    const sorted = [...window.allPlayers].sort((a,b) => t==='gw' ? (b.form||0)-(a.form||0) : b.total_points-a.total_points);
    displayPlayerRows(sorted);
};

/**
 * ၄။ Player Detail Popup (Next 3 Matches ပါဝင်သော)
 */
window.showPDetail = (id) => {
    const p = window.allPlayers.find(x => x.id === id);
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.onclick = () => modal.remove();
    modal.innerHTML = `
        <div class="profile-card" style="max-width:350px;" onclick="event.stopPropagation()">
            <h3 class="gold-text">${p.name}</h3>
            <div class="profile-info">
                <div class="info-item"><span class="label">Goals:</span> <span class="val">${p.goals||0}</span></div>
                <div class="info-item"><span class="label">Assists:</span> <span class="val">${p.assists||0}</span></div>
                <div class="info-item"><span class="label">Bonus:</span> <span class="val">${p.bonus||0}</span></div>
                <div class="info-item"><span class="label">xG:</span> <span class="val">${p.xg||0.0}</span></div>
            </div>
            <h4 class="gold-text" style="text-align:left; font-size:0.7rem; margin:15px 0 5px;">🗓 NEXT 3 MATCHES</h4>
            <div style="display:flex; gap:5px;">
                ${(p.next_fixtures || ['TBA','TBA','TBA']).slice(0,3).map(f => `
                    <div style="flex:1; background:#000; padding:5px; border-radius:5px; font-size:0.6rem; border:1px solid #222;">
                        ${f.opponent || f}
                    </div>
                `).join('')}
            </div>
            <button class="primary-btn" style="margin-top:20px;" onclick="this.parentElement.parentElement.remove()">CLOSE</button>
        </div>
    `;
    document.body.appendChild(modal);
};

/**
 * ၅။ League Section & Pitch View
 */
async function loadLeagueData() {
    const container = document.getElementById('scout-container');
    container.innerHTML = `
        <div style="display:flex; gap:5px; margin-bottom:10px;">
            <button id="l-a" class="primary-btn" style="height:35px; font-size:0.7rem;" onclick="window.fetchL('League_A')">LEAGUE A</button>
            <button id="l-b" class="primary-btn" style="height:35px; font-size:0.7rem; background:#222;" onclick="window.fetchL('League_B')">LEAGUE B</button>
        </div>
        <div id="l-root"></div>
    `;
    window.fetchL('League_A');
}

window.fetchL = async (key) => {
    const root = document.getElementById('l-root');
    document.getElementById('l-a').style.background = key==='League_A' ? 'var(--gold)' : '#222';
    document.getElementById('l-b').style.background = key==='League_B' ? 'var(--gold)' : '#222';
    
    root.innerHTML = `<div class="spinner"></div>`;
    const snap = await db.collection(`scout_${key}`).orderBy("total_points", "desc").limit(50).get();
    let teams = [];
    snap.forEach(d => teams.push(d.data()));
    window.allLeagues = teams;

    root.innerHTML = `
        <table class="scout-table">
            <thead>
                <tr>
                    <th align="left">TEAM/MANAGER</th>
                    <th onclick="window.reSortL('gw')" style="color:var(--gold)">GW</th>
                    <th onclick="window.reSortL('tot')" style="color:var(--gold)">TOT ▽</th>
                </tr>
            </thead>
            <tbody id="l-body"></tbody>
        </table>
    `;
    displayLeagueRows(teams);
};

function displayLeagueRows(data) {
    const body = document.getElementById('l-body');
    body.innerHTML = data.map(t => `
        <tr onclick="window.showTPitch('${t.entry_id}')">
            <td>
                <div style="font-weight:bold;">${t.team_name}</div>
                <div style="font-size:0.65rem; color:#666;">${t.manager}</div>
            </td>
            <td align="center">${t.gw_points || 0}</td>
            <td align="center" style="color:var(--gold); font-weight:800;">${t.total_points || 0}</td>
        </tr>
    `).join('');
}

window.reSortL = (t) => {
    const sorted = [...window.allLeagues].sort((a,b) => t==='gw' ? (b.gw_points||0)-(a.gw_points||0) : b.total_points-a.total_points);
    displayLeagueRows(sorted);
};

window.showTPitch = (id) => {
    const t = window.allLeagues.find(x => x.entry_id == id);
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.onclick = () => modal.remove();

    const lineup = t.lineup || [];
    const starters = lineup.slice(0, 11);
    const gkp = starters.filter(p => p.pos === 'GKP');
    const def = starters.filter(p => p.pos === 'DEF');
    const mid = starters.filter(p => p.pos === 'MID');
    const fwd = starters.filter(p => p.pos === 'FWD');

    modal.innerHTML = `
        <div class="profile-card" style="width:95%; max-width:450px; background:#072107; border:1px solid var(--gold);" onclick="event.stopPropagation()">
            <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                <div style="text-align:left;"><h4 style="margin:0;">${t.team_name}</h4><small>Hit: ${t.transfer_cost || 0}</small></div>
                <div style="background:var(--gold); color:#000; padding:2px 8px; border-radius:4px; font-weight:800; font-size:0.7rem;">${t.active_chip || 'No Chip'}</div>
            </div>
            <div class="pitch-container" style="display:flex; flex-direction:column-reverse; gap:10px; min-height:300px; padding:10px; background:rgba(255,255,255,0.05); border-radius:10px;">
                <div class="pitch-row">${renderPlayers(fwd)}</div>
                <div class="pitch-row">${renderPlayers(mid)}</div>
                <div class="pitch-row">${renderPlayers(def)}</div>
                <div class="pitch-row">${renderPlayers(gkp)}</div>
            </div>
            <div style="margin-top:10px; display:flex; justify-content:center; gap:8px;">
                ${lineup.slice(11,15).map(p => `<div style="font-size:0.5rem; text-align:center;">👕<br>${p.name}</div>`).join('')}
            </div>
            <button class="primary-btn" style="margin-top:15px; background:#fff; color:#000;" onclick="this.parentElement.parentElement.remove()">BACK</button>
        </div>
    `;
    document.body.appendChild(modal);
};

function renderPlayers(arr) {
    return arr.map(p => `
        <div style="text-align:center; width:60px;">
            <div style="font-size:1.1rem; position:relative;">${p.is_captain?'👑':''}👕</div>
            <div style="background:#000; color:#fff; font-size:0.5rem; white-space:nowrap; overflow:hidden;">${p.name}</div>
            <div style="font-size:0.55rem; color:var(--gold); font-weight:bold;">${p.points}pts</div>
        </div>
    `).join('');
}
