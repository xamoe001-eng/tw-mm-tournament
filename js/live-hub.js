// ၁။ Live Hub စာမျက်နှာကို စတင်ဖန်တီးခြင်း
window.renderLiveHub = function() {
    const mainRoot = document.getElementById('main-root');
    if (!mainRoot) return;

    mainRoot.innerHTML = `
        <div style="text-align: center; padding: 15px;">
            <div style="margin-bottom: 25px;">
                <button onclick="window.loadFixtures('league')" class="nav-btn" 
                    style="background:#D4AF37; color:black; margin:5px; border-radius: 20px; padding: 10px 20px; font-weight:bold; border:none; cursor:pointer;">
                    League Matches
                </button>
                <button onclick="window.loadFixtures('fa_cup')" class="nav-btn" 
                    style="background:#00ff88; color:black; margin:5px; border-radius: 20px; padding: 10px 20px; font-weight:bold; border:none; cursor:pointer;">
                    TW FA Cup
                </button>
            </div>
            <div id="live-content" style="min-height: 300px;">
                <div class="loading">🎮 ပွဲစဉ်ဇယားများကို စစ်ဆေးနေသည်...</div>
            </div>
        </div>
    `;
    // ပထမဆုံးဝင်ဝင်ချင်း League Matches ကို ပြမည်
    window.loadFixtures('league');
};

// ၂။ Fixtures များကို ဆွဲထုတ်ပြီး Live အမှတ်များနှင့် ချိတ်ဆက်ပြသခြင်း
window.loadFixtures = function(type) {
    const content = document.getElementById('live-content');
    if (!content) return;

    content.innerHTML = `<div class="loading">⌛ ${type === 'league' ? 'League' : 'FA Cup'} ပွဲစဉ်များ ဆွဲယူနေသည်...</div>`;

    // Fixtures များကို ဖတ်ခြင်း
    db.collection("fixtures")
      .where("type", "==", type)
      .onSnapshot((fixturesSnapshot) => {
        if (fixturesSnapshot.empty) {
            content.innerHTML = `<div style="padding:40px; color:#888;">ပွဲစဉ်များ မရှိသေးပါ။</div>`;
            return;
        }

        // Rankings (Live Score) များကို တစ်ခါတည်း ဖတ်ခြင်း
        db.collection("tw_mm_tournament").onSnapshot((rankSnapshot) => {
            let scores = {};
            rankSnapshot.forEach(doc => {
                scores[doc.id] = doc.data().gw_points; // FPL ID အလိုက် GW အမှတ် သိမ်းမည်
            });

            let html = `<h2 style="color:#fff; font-size:1.1rem; margin-bottom:20px;">
                            ${type === 'league' ? 'H2H LEAGUE MATCHES' : 'TW FA CUP PLAYOFF'}
                        </h2>`;

            fixturesSnapshot.forEach(doc => {
                const f = doc.data();
                const homePts = scores[f.home.id] || 0;
                const awayPts = scores[f.away.id] || 0;

                // ဘယ်သူနိုင်နေလဲ အရောင်သတ်မှတ်ခြင်း
                const homeStyle = homePts > awayPts ? "color:#00ff88; font-weight:bold;" : "color:#fff;";
                const awayStyle = awayPts > homePts ? "color:#00ff88; font-weight:bold;" : "color:#fff;";

                html += `
                    <div style="background:#1a1a1a; border-radius:15px; padding:15px; margin-bottom:15px; border-left: 4px solid ${type === 'league' ? '#D4AF37' : '#00ff88'};">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <div style="flex:1; text-align:right; padding-right:10px;">
                                <div style="font-size:0.9rem; ${homeStyle}">${f.home.name}</div>
                                <div style="font-size:0.7rem; color:#888;">${f.home.manager}</div>
                            </div>

                            <div style="background:#333; padding:5px 15px; border-radius:8px; min-width:80px; text-align:center;">
                                <span style="font-size:1.2rem; font-weight:bold; ${homeStyle}">${homePts}</span>
                                <span style="color:#888; margin:0 5px;">-</span>
                                <span style="font-size:1.2rem; font-weight:bold; ${awayStyle}">${awayPts}</span>
                            </div>

                            <div style="flex:1; text-align:left; padding-left:10px;">
                                <div style="font-size:0.9rem; ${awayStyle}">${f.away.name}</div>
                                <div style="font-size:0.7rem; color:#888;">${f.away.manager}</div>
                            </div>
                        </div>
                        <div style="font-size:0.6rem; color:#555; margin-top:10px; text-transform:uppercase;">
                            GW ${f.gameweek} | Division: ${f.division}
                        </div>
                    </div>
                `;
            });

            content.innerHTML = html;
        });
    });
};
