/**
 * ၁။ Scout Tab Main Render
 */
window.renderScout = async function() {
    const mainRoot = document.getElementById('main-root');
    
    // CSS Header နဲ့ Pitch Design များ
    const scoutStyle = document.createElement('style');
    scoutStyle.innerHTML = `
        .pitch-container {
            background: linear-gradient(to bottom, #0a4d0a 0%, #063306 100%);
            background-image: repeating-linear-gradient(0deg, transparent, transparent 19%, rgba(0,0,0,0.1) 20%);
            border-radius: 8px;
            padding: 20px 5px;
            min-height: 400px;
            display: flex;
            flex-direction: column;
            justify-content: space-around;
            border: 2px solid #1a3d1a;
            box-shadow: inset 0 0 50px rgba(0,0,0,0.5);
        }
        .jersey-icon {
            font-size: 1.8rem;
            position: relative;
            margin-bottom: 2px;
            transition: transform 0.2s;
        }
        .jersey-gk { color: #f9d71c; } /* Goalkeeper - Yellow */
        .jersey-field { color: #3bffee; } /* Outfield - Cyan/Blue */
        .jersey-bench { color: #ffffff; opacity: 0.8; } /* Bench - White */
        
        .badge-common {
            position: absolute;
            top: -12px;
            right: -5px;
            font-size: 0.6rem;
            padding: 1px 4px;
            border-radius: 3px;
            font-weight: 900;
            z-index: 5;
            box-shadow: 0 2px 4px rgba(0,0,0,0.5);
        }
    `;
    document.head.appendChild(scoutStyle);

    mainRoot.innerHTML = `
        <div id="scout-header" style="margin-bottom: 20px; padding: 10px;">
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
 * ၂။ Tab Switcher
 */
window.switchTab = function(tab) {
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
 * ၃။ Player Scout Section
 */
async function loadPlayerData() {
    const container = document.getElementById('scout-container');
    container.innerHTML = `<div class="spinner"></div>`;
    const snapshot = await db.collection("scout_players").orderBy("total_points", "desc").limit(100).get();
    let players = [];
    snapshot.forEach(doc => players.push({id: doc.id, ...doc.data()}));
    window.allPlayers = players;

    container.innerHTML = `
        <table class="scout-table">
            <thead>
                <tr>
                    <th align="left">PLAYER</th>
                    <th onclick="window.reSortP('gw')" style="color:var(--gold); cursor:pointer;">GW ▽</th>
                    <th onclick="window.reSortP('tot')" style="color:var(--gold); cursor:pointer;">TOT ▽</th>
                    <th onclick="window.reSortP('own')" style="color:var(--gold); cursor:pointer;">OWN% ▽</th>
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
            <td align="center">${p.gw_points || 0}</td> 
            <td align="center" style="font-weight:bold;">${p.total_points || 0}</td>
            <td align="center" style="font-size:0.75rem; color:var(--gold);">${p.ownership || '0.0'}%</td>
        </tr>
    `).join('');
}

window.reSortP = (t) => {
    let sorted = [...window.allPlayers];
    if (t === 'gw') sorted.sort((a,b) => (b.gw_points || 0) - (a.gw_points || 0));
    else if (t === 'tot') sorted.sort((a,b) => b.total_points - a.total_points);
    else if (t === 'own') sorted.sort((a,b) => parseFloat(b.ownership || 0) - parseFloat(a.ownership || 0));
    displayPlayerRows(sorted);
};

window.showPDetail = (id) => {
    const p = window.allPlayers.find(x => x.id === id);
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.onclick = () => modal.remove();
    
    const fixtureHtml = p.fixtures ? p.fixtures.slice(0, 5).map(f => `
        <div style="flex:1; background:${f.bg || '#333'}; color:${f.text || '#fff'}; text-align:center; padding:5px 2px; border-radius:4px; font-size:0.6rem; font-weight:bold; min-width:45px; border:1px solid rgba(255,255,255,0.1);">
            <div>${f.opponent || 'TBC'}</div>
            <div style="font-size:0.5rem; opacity:0.8;">${f.is_home ? '(H)' : '(A)'}</div>
        </div>
    `).join('') : '<div style="color:#555; font-size:0.7rem;">No upcoming fixtures</div>';

    modal.innerHTML = `
        <div class="profile-card" style="max-width:340px; border: 1px solid #333;" onclick="event.stopPropagation()">
            <div style="text-align:center; margin-bottom:15px;">
                <h3 class="gold-text" style="margin:0; font-size:1.2rem;">${p.full_name || p.name}</h3>
                <small style="color:#888; text-transform:uppercase; letter-spacing:1px;">${p.team_full || p.team} | ${p.pos}</small>
            </div>
            
            <div class="profile-info" style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin-bottom:15px;">
                <div class="info-item"><span class="label">GOALS</span><span class="val">${p.goals||0}</span></div>
                <div class="info-item"><span class="label">ASSISTS</span><span class="val">${p.assists||0}</span></div>
                <div class="info-item"><span class="label">CS</span><span class="val">${p.clean_sheets||0}</span></div>
                <div class="info-item"><span class="label">BONUS</span><span class="val">${p.bonus||0}</span></div>
                <div class="info-item"><span class="label">xG</span><span class="val">${p.xg||0.0}</span></div>
                <div class="info-item"><span class="label">ICT</span><span class="val">${p.ict||0.0}</span></div>
            </div>

            <div style="margin-bottom:15px; background:rgba(212,175,55,0.05); padding:10px; border-radius:8px; border:1px solid #222;">
                <div style="font-size:0.65rem; color:var(--gold); margin-bottom:8px; font-weight:bold; letter-spacing:1px;">NEXT 5 MATCHES</div>
                <div style="display:flex; gap:4px; justify-content:space-between;">${fixtureHtml}</div>
            </div>

            <div style="background:#000; padding:10px; border-radius:8px; border:1px solid #222; display:flex; justify-content:space-between; font-size:0.7rem;">
                <span>Price: <b>£${p.price}m</b></span>
                <span>Ownership: <b style="color:var(--gold);">${p.ownership}%</b></span>
            </div>
            <button class="primary-btn" style="margin-top:15px; width:100%; border-radius:6px;" onclick="this.parentElement.parentElement.remove()">CLOSE</button>
        </div>
    `;
    document.body.appendChild(modal);
};

/**
 * ၄။ League Scout
 */
async function loadLeagueData() {
    const container = document.getElementById('scout-container');
    container.innerHTML = `
        <div style="display:flex; gap:5px; margin-bottom:12px; padding: 0 5px;">
            <button id="l-a" class="primary-btn" style="flex:1; height:38px; font-size:0.7rem;" onclick="window.fetchL('League_A')">LEAGUE A</button>
            <button id="l-b" class="primary-btn" style="flex:1; height:38px; font-size:0.7rem; background:#222;" onclick="window.fetchL('League_B')">LEAGUE B</button>
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
    const snap = await db.collection(`scout_${key}`).orderBy("total_points", "desc").get();
    let teams = [];
    snap.forEach(d => teams.push(d.data()));
    window.allLeagues = teams;

    root.innerHTML = `
        <table class="scout-table">
            <thead>
                <tr>
                    <th align="left">MANAGER</th>
                    <th onclick="window.reSortL('gw')" style="color:var(--gold); cursor:pointer;">GW</th>
                    <th onclick="window.reSortL('tot')" style="color:var(--gold); cursor:pointer;">TOT ▽</th>
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
                <div style="font-weight:bold; font-size:0.85rem;">${t.team_name}</div>
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

/**
 * ၅။ Pitch View (Official Styling)
 */
window.showTPitch = (id) => {
    const t = window.allLeagues.find(x => x.entry_id == id);
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.onclick = () => modal.remove();

    const lineup = t.lineup || [];
    const starters = lineup.filter(p => p.multiplier > 0);
    const bench = lineup.filter(p => p.multiplier === 0);

    // VC ရှာဖွေခြင်း
    const realVC = starters.find(p => p.is_vice_captain === true);

    modal.innerHTML = `
        <div class="profile-card" style="width:96%; max-width:400px; padding:15px; background:#041a04; border:1px solid #1a3d1a;" onclick="event.stopPropagation()">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px;">
                <div>
                    <h4 style="margin:0; font-size:1rem; color:var(--gold);">${t.team_name}</h4>
                    <span style="font-size:0.65rem; color:#888;">Hit: <span style="color:#ff4444;">-${t.transfer_cost || 0}</span> | GW: ${t.gw_points}</span>
                </div>
                <div style="background:${t.active_chip?'var(--gold)':'#222'}; color:${t.active_chip?'#000':'#888'}; padding:4px 10px; border-radius:4px; font-weight:900; font-size:0.7rem;">
                    ${t.active_chip ? t.active_chip.toUpperCase() : 'NO CHIP'}
                </div>
            </div>

            <div class="pitch-container">
                <div style="display:flex; justify-content:center; gap:5px;">${renderPitchPlayers(starters.filter(p=>p.pos==='FWD'), realVC)}</div>
                <div style="display:flex; justify-content:center; gap:5px;">${renderPitchPlayers(starters.filter(p=>p.pos==='MID'), realVC)}</div>
                <div style="display:flex; justify-content:center; gap:5px;">${renderPitchPlayers(starters.filter(p=>p.pos==='DEF'), realVC)}</div>
                <div style="display:flex; justify-content:center; gap:5px;">${renderPitchPlayers(starters.filter(p=>p.pos==='GKP'), realVC)}</div>
            </div>

            <div style="margin-top:12px; background:rgba(0,0,0,0.6); padding:12px; border-radius:12px; display:flex; justify-content:space-between; border:1px solid rgba(255,255,255,0.1); gap:5px;">
                ${bench.map(p => `
                    <div style="text-align:center; flex:1;">
                        <div class="jersey-icon jersey-bench">👕</div>
                        <div style="background:#fff; color:#000; font-size:0.55rem; font-weight:bold; padding:1px 2px; border-radius:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; width:100%;">${p.name}</div>
                        <div style="font-size:0.7rem; color:#fff; font-weight:900;">${p.points}</div>
                    </div>
                `).join('')}
            </div>
            
            <button class="primary-btn" style="margin-top:15px; width:100%; background:#fff; color:#000; font-weight:900; height:45px; border-radius:8px;" onclick="this.parentElement.parentElement.remove()">BACK TO LIST</button>
        </div>
    `;
    document.body.appendChild(modal);
};

function renderPitchPlayers(arr, realVC) {
    return arr.map(p => {
        let capBadge = '';
        
        // Captain Badge Logic
        if (p.is_captain) {
            const label = p.multiplier === 3 ? 'TC' : 'C';
            const bg = p.multiplier === 3 ? '#ff4444' : '#000';
            capBadge = `<div class="badge-common" style="background:${bg}; color:var(--gold); border:1px solid var(--gold);">${label}</div>`;
        } 
        // Vice Captain Badge Logic
        else if (realVC && p.id === realVC.id) { 
            capBadge = `<div class="badge-common" style="background:#333; color:#fff; border:1px solid #fff;">V</div>`;
        }

        const score = (p.points || 0) * (p.multiplier || 1);
        // GK ကို Yellow Jersey ပေးခြင်း
        const jerseyType = p.pos === 'GKP' ? 'jersey-gk' : 'jersey-field';

        return `
            <div style="text-align:center; width:68px; position:relative;">
                <div class="jersey-icon ${jerseyType}">
                    ${capBadge}
                    👕
                </div>
                <div style="background:rgba(0,0,0,0.9); color:#fff; font-size:0.55rem; padding:2px 3px; border-radius:2px; width:100%; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; border:0.5px solid #444; font-weight:bold;">
                    ${p.name}
                </div>
                <div style="font-size:0.8rem; color:var(--gold); font-weight:900; text-shadow: 1px 1px 2px #000; margin-top:1px;">
                    ${score}
                </div>
            </div>
        `;
    }).join('');
}
