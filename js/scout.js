/**
 * ၁။ Scout Tab Main Render
 */
window.renderScout = async function() {
    const mainRoot = document.getElementById('main-root');
    
    const scoutStyle = document.createElement('style');
    scoutStyle.innerHTML = `
        .pitch-container {
            background: linear-gradient(to bottom, #0a4d0a 0%, #063306 100%);
            background-image: repeating-linear-gradient(0deg, transparent, transparent 19%, rgba(0,0,0,0.1) 20%);
            border-radius: 12px; padding: 25px 5px; min-height: 420px;
            display: flex; flex-direction: column; justify-content: space-around;
            border: 2px solid #1a3d1a; box-shadow: inset 0 0 50px rgba(0,0,0,0.6);
        }
        
        /* SVG Jersey Styles - Goalkeeper Yellow Fix */
        .jersey-svg { width: 32px; height: 32px; margin: 0 auto; display: block; }
        .jersey-gk-svg { fill: #ffeb3b !important; filter: drop-shadow(0 0 2px rgba(0,0,0,0.5)); }
        .jersey-field-svg { fill: #3bffee !important; }
        .jersey-bench-svg { fill: #ffffff !important; opacity: 0.8; }

        .badge-common {
            position: absolute; top: -8px; right: -5px; font-size: 0.6rem;
            padding: 1px 4px; border-radius: 3px; font-weight: 900;
            z-index: 10; box-shadow: 0 2px 4px rgba(0,0,0,0.5);
        }

        .pos-filter-container { display: flex; gap: 6px; margin-bottom: 15px; padding: 0 10px; overflow-x: auto; }
        .pos-filter-btn {
            background: #1a1a1a; color: #888; border: 1px solid #333;
            padding: 6px 14px; border-radius: 6px; font-size: 0.7rem; font-weight: 800;
        }
        .pos-filter-btn.active { background: var(--gold); color: #000; border-color: var(--gold); }
        
        .pitch-row { display: flex; justify-content: center; gap: 10px; }
        .player-card-mini { text-align: center; width: 68px; position: relative; }
        
        /* Fixture Difficulty Colors */
        .fdr-1 { background: #01fc7a; color: #000; }
        .fdr-2 { background: #01fc7a; color: #000; }
        .fdr-3 { background: #e7e7e7; color: #000; }
        .fdr-4 { background: #ff1751; color: #fff; }
        .fdr-5 { background: #80072d; color: #fff; }
    `;
    document.head.appendChild(scoutStyle);

    mainRoot.innerHTML = `
        <div id="scout-header" style="margin-bottom: 20px;">
            <h3 class="gold-text" style="padding-left:10px;">🔭 SCOUT CENTER</h3>
            <div style="display: flex; gap: 8px; margin-bottom: 15px; padding: 0 10px;">
                <button id="btn-p" class="primary-btn" style="flex:1;" onclick="window.switchTab('p')">PLAYER SCOUT</button>
                <button id="btn-l" class="primary-btn" style="flex:1; background:#222; color:#888;" onclick="window.switchTab('l')">LEAGUE SCOUT</button>
            </div>
        </div>
        <div id="scout-container"></div>
    `;
    window.switchTab('p'); 
};

/**
 * ၂။ Tab Switcher & Data Loading
 */
window.switchTab = (tab) => {
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

async function loadPlayerData() {
    const container = document.getElementById('scout-container');
    container.innerHTML = `<div class="spinner"></div>`;
    try {
        const snap = await db.collection("scout_players").orderBy("total_points", "desc").limit(100).get();
        window.allPlayers = snap.docs.map(doc => ({id: doc.id, ...doc.data()}));
        container.innerHTML = `
            <div class="pos-filter-container">
                <button class="pos-filter-btn active" onclick="window.filterByPos('ALL', this)">ALL</button>
                <button class="pos-filter-btn" onclick="window.filterByPos('GKP', this)">GKP</button>
                <button class="pos-filter-btn" onclick="window.filterByPos('DEF', this)">DEF</button>
                <button class="pos-filter-btn" onclick="window.filterByPos('MID', this)">MID</button>
                <button class="pos-filter-btn" onclick="window.filterByPos('FWD', this)">FWD</button>
            </div>
            <table class="scout-table">
                <thead>
                    <tr><th align="left">PLAYER</th><th>GW</th><th>TOT</th><th>OWN%</th></tr>
                </thead>
                <tbody id="p-body"></tbody>
            </table>
        `;
        displayPlayerRows(window.allPlayers);
    } catch (e) { console.error(e); }
}

function displayPlayerRows(data) {
    const body = document.getElementById('p-body');
    body.innerHTML = data.map(p => `
        <tr onclick="window.showPDetail('${p.id}')">
            <td>
                <div style="font-weight:800;">${p.name}</div>
                <div style="font-size:0.6rem; color:#666;">${p.team} | ${p.pos} | £${p.price}m</div>
            </td>
            <td align="center">${p.gw_points || 0}</td>
            <td align="center" style="font-weight:bold;">${p.total_points || 0}</td>
            <td align="center" style="color:var(--gold); font-size:0.7rem;">${p.ownership || '0.0'}%</td>
        </tr>
    `).join('');
}

window.filterByPos = (pos, btn) => {
    document.querySelectorAll('.pos-filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const filtered = pos === 'ALL' ? window.allPlayers : window.allPlayers.filter(p => p.pos === pos);
    displayPlayerRows(filtered);
};

/**
 * ၃။ Player Detail Modal (xG, ICT & Fixtures ပါဝင်သည်)
 */
window.showPDetail = (id) => {
    const p = window.allPlayers.find(x => x.id === id);
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.onclick = () => modal.remove();
    
    // Fixture Rendering with FDR Color
    const fixHtml = (p.fixtures || []).slice(0, 5).map(f => `
        <div class="fdr-${f.difficulty || 3}" style="flex:1; text-align:center; padding:5px 2px; border-radius:4px; font-size:0.6rem; font-weight:bold; min-width:45px;">
            <div>${f.opponent || 'TBC'}</div>
            <div style="font-size:0.5rem; opacity:0.8;">${f.is_home ? '(H)' : '(A)'}</div>
        </div>
    `).join('') || '<div style="color:#555; font-size:0.7rem;">No upcoming fixtures</div>';

    modal.innerHTML = `
        <div class="profile-card" onclick="event.stopPropagation()" style="max-width:450px;">
            <div style="text-align:center; margin-bottom:15px;">
                <h3 class="gold-text" style="margin:0;">${p.full_name || p.name}</h3>
                <small style="color:#888;">${p.team_full || p.team} | ${p.pos}</small>
            </div>
            
            <div class="profile-info" style="display:grid; grid-template-columns: repeat(3, 1fr); gap:8px; background:#000; padding:12px; border-radius:12px;">
                <div class="info-item"><span class="label">xG</span><span class="val">${p.xg || '0.0'}</span></div>
                <div class="info-item"><span class="label">xA</span><span class="val">${p.xa || '0.0'}</span></div>
                <div class="info-item"><span class="label">ICT</span><span class="val">${p.ict_index || '0.0'}</span></div>
                <div class="info-item"><span class="label">GOALS</span><span class="val">${p.goals || 0}</span></div>
                <div class="info-item"><span class="label">ASSISTS</span><span class="val">${p.assists || 0}</span></div>
                <div class="info-item"><span class="label">BONUS</span><span class="val">${p.bonus || 0}</span></div>
            </div>

            <div style="margin:15px 0; background:#111; padding:12px; border-radius:12px; border:1px solid #222;">
                <div style="font-size:0.65rem; color:var(--gold); margin-bottom:10px; font-weight:bold;">NEXT 5 FIXTURES</div>
                <div style="display:flex; gap:5px;">${fixHtml}</div>
            </div>

            <button class="primary-btn" onclick="this.parentElement.parentElement.remove()">CLOSE</button>
        </div>
    `;
    document.body.appendChild(modal);
};

/**
 * ၄။ League & Pitch View (Bench GK Yellow Fix)
 */
window.showTPitch = (id) => {
    const t = window.allLeagues.find(x => x.entry_id == id);
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.onclick = () => modal.remove();

    const starters = (t.lineup || []).filter(p => p.multiplier > 0);
    const bench = (t.lineup || []).filter(p => p.multiplier === 0);
    const realVC = starters.find(p => p.is_vice_captain === true);

    modal.innerHTML = `
        <div class="profile-card" style="width:96%; background:#041a04; border:1px solid #1a3d1a;" onclick="event.stopPropagation()">
            <div style="display:flex; justify-content:space-between; margin-bottom:10px; text-align:left;">
                <div>
                    <h4 style="margin:0; color:var(--gold);">${t.team_name}</h4>
                    <span style="font-size:0.6rem; color:#888;">Hit: -${t.transfer_cost || 0} | GW Points: ${t.gw_points}</span>
                </div>
                <div style="background:var(--gold); color:#000; padding:4px 8px; border-radius:4px; font-weight:900; font-size:0.6rem;">
                    ${t.active_chip ? t.active_chip.toUpperCase() : 'NO CHIP'}
                </div>
            </div>

            <div class="pitch-container">
                <div class="pitch-row">${renderPitchPlayers(starters.filter(p=>p.pos==='FWD'), realVC)}</div>
                <div class="pitch-row">${renderPitchPlayers(starters.filter(p=>p.pos==='MID'), realVC)}</div>
                <div class="pitch-row">${renderPitchPlayers(starters.filter(p=>p.pos==='DEF'), realVC)}</div>
                <div class="pitch-row">${renderPitchPlayers(starters.filter(p=>p.pos==='GKP'), realVC)}</div>
            </div>

            <div style="margin-top:12px; background:rgba(0,0,0,0.7); padding:10px; border-radius:12px; display:flex; justify-content:space-around; border:1px solid #222;">
                ${bench.map(p => {
                    const isGK = p.pos === 'GKP';
                    const jerseyClass = isGK ? 'jersey-gk-svg' : 'jersey-bench-svg';
                    return `
                        <div style="text-align:center; flex:1;">
                            <svg class="jersey-svg ${jerseyClass}" viewBox="0 0 24 24" style="width:24px; height:24px;">
                                <path d="M13,2V4H11V2H8V4H6V7C6,8.1 6.9,9 8,9V22H16V9C17.1,9 18,8.1 18,7V4H16V2H13Z" />
                            </svg>
                            <div style="background:#fff; color:#000; font-size:0.5rem; font-weight:bold; padding:1px 3px; border-radius:2px; margin-top:2px;">${p.name}</div>
                            <div style="font-size:0.65rem; color:#fff; font-weight:900;">${p.points}</div>
                        </div>
                    `;
                }).join('')}
            </div>
            <button class="primary-btn" style="margin-top:15px; background:#fff; color:#000;" onclick="this.parentElement.parentElement.remove()">BACK TO LIST</button>
        </div>
    `;
    document.body.appendChild(modal);
};

function renderPitchPlayers(arr, realVC) {
    return arr.map(p => {
        let capBadge = '';
        if (p.is_captain) {
            capBadge = `<div class="badge-common" style="background:#000; color:var(--gold); border:1px solid var(--gold);">${p.multiplier === 3 ? 'TC' : 'C'}</div>`;
        } else if (realVC && p.id === realVC.id) {
            capBadge = `<div class="badge-common" style="background:#333; color:#fff; border:1px solid #fff;">V</div>`;
        }
        const isGK = p.pos === 'GKP';
        const jerseyClass = isGK ? 'jersey-gk-svg' : 'jersey-field-svg';

        return `
            <div class="player-card-mini">
                <div style="position:relative;">
                    ${capBadge}
                    <svg class="jersey-svg ${jerseyClass}" viewBox="0 0 24 24">
                        <path d="M13,2V4H11V2H8V4H6V7C6,8.1 6.9,9 8,9V22H16V9C17.1,9 18,8.1 18,7V4H16V2H13Z" />
                    </svg>
                </div>
                <div class="player-name-label" style="background:rgba(0,0,0,0.8); color:#fff; font-size:0.55rem; padding:2px; border-radius:2px; margin-top:2px; overflow:hidden;">${p.name}</div>
                <div style="font-size:0.75rem; color:var(--gold); font-weight:900;">${(p.points||0)*(p.multiplier||1)}</div>
            </div>
        `;
    }).join('');
}

// League Loading Logic (Same as before)
window.loadLeagueData = async () => { /* ... fetch league logic ... */ };
window.fetchL = async (key) => { /* ... same logic ... */ };
