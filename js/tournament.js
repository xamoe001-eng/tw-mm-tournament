window.filterDivision = function(divTag) {
    const content = document.getElementById('league-content');
    const btnA = document.getElementById('btn-divA');
    const btnB = document.getElementById('btn-divB');
    if (!content) return;

    // Button UI Toggle
    if (divTag === 'A') {
        btnA.style.background = '#D4AF37'; btnA.style.color = '#000';
        btnB.style.background = 'transparent'; btnB.style.color = '#666';
    } else {
        btnB.style.background = '#C0C0C0'; btnB.style.color = '#000';
        btnA.style.background = 'transparent'; btnA.style.color = '#666';
    }

    // 🛑 Index Error မတက်အောင် orderBy ကို ဖြုတ်ထားပါတယ်
    db.collection("tw_mm_tournament")
      .where("league_tag", "==", divTag)
      .onSnapshot((snapshot) => {
        if (snapshot.empty) {
            content.innerHTML = `<div style="text-align:center; padding:50px; color:#444;">NO DATA IN DIVISION ${divTag}</div>`;
            return;
        }

        // ၁။ ဒေတာများကို Array ထဲထည့်ခြင်း
        let players = [];
        snapshot.forEach((doc) => {
            players.push(doc.data());
        });

        // ၂။ Sorting Logic (အမှတ်တူရင် Week Point များသူကို အပေါ်တင်သည်)
        players.sort((a, b) => {
            // ပထမအဆင့်: H2H Points (PTS) အများဆုံးသူကို အရင်စီသည်
            if ((b.h2h_points || 0) !== (a.h2h_points || 0)) {
                return (b.h2h_points || 0) - (a.h2h_points || 0);
            }
            // ဒုတိယအဆင့် (Tie-breaker): PTS တူရင် GW Points များသူကို အပေါ်တင်သည်
            return (b.gw_points || 0) - (a.gw_points || 0);
        });

        // ၃။ HTML Render လုပ်ခြင်း
        let html = `
            <div style="display: flex; justify-content: space-between; padding: 0 10px 10px; font-size: 0.65rem; color: #555; font-weight: 800; text-transform: uppercase;">
                <span># TEAM INFO</span>
                <span>GW / MATCH STATS / PTS</span>
            </div>
        `;

        players.forEach((p, index) => {
            const pos = index + 1;
            const rankColor = pos === 1 ? '#D4AF37' : (pos === 2 ? '#C0C0C0' : (pos === 3 ? '#CD7F32' : '#fff'));

            html += `
                <div style="background: #111; margin-bottom: 8px; border-radius: 12px; padding: 12px; display: flex; align-items: center; border: 1px solid #222;">
                    <div style="width: 30px; font-weight: 900; font-size: 1rem; color: ${rankColor};">${pos}</div>
                    
                    <div style="flex: 1; min-width: 0; padding-right: 5px;">
                        <div style="font-weight: 800; color: #fff; font-size: 0.85rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                            ${p.team_name || 'No Name'}
                        </div>
                        <div style="font-size: 0.65rem; color: #555;">${p.manager_name || 'Manager'}</div>
                    </div>

                    <div style="text-align: right; min-width: 120px;">
                        <div style="display: flex; justify-content: flex-end; gap: 3px; margin-bottom: 4px; font-size: 0.6rem; font-weight: 800;">
                            <span style="color: #00ff88; padding: 1px 5px; background: rgba(0,255,136,0.15); border: 1px solid rgba(0,255,136,0.2); border-radius: 3px; margin-right: 2px;">GW: ${p.gw_points || 0}</span>
                            <span style="color: #bbb; padding: 1px 4px; background: #222; border-radius: 3px;">P:${p.played || 0}</span>
                        </div>
                        
                        <div style="display: flex; justify-content: flex-end; gap: 3px; margin-bottom: 4px; font-size: 0.55rem; opacity: 0.7;">
                             <span style="color: #00ff88;">W:${p.wins || 0}</span>
                             <span style="color: #ffcc00;">D:${p.draws || 0}</span>
                             <span style="color: #ff4d4d;">L:${p.losses || 0}</span>
                        </div>

                        <div style="font-weight: 900; font-size: 1.1rem; color: ${divTag === 'A' ? '#D4AF37' : '#C0C0C0'};">
                            ${p.h2h_points || 0}<span style="font-size: 0.55rem; margin-left: 2px; color: #666;">PTS</span>
                        </div>
                    </div>
                </div>
            `;
        });

        content.innerHTML = html;
      });
};
