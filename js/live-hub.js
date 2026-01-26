window.renderLiveHub = function() {
    const mainRoot = document.getElementById('main-root');
    if (!mainRoot) return;

    mainRoot.innerHTML = `
        <div style="padding: 20px; animation: fadeIn 0.5s;">
            <h2 style="color: #D4AF37; text-align: center;">LIVE HUB 🏆</h2>
            
            <div style="background: linear-gradient(145deg, #1a1a1a, #222); border: 1px solid #D4AF37; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(212,175,55,0.1);">
                <p style="color: #888; margin-bottom: 10px; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px;">Next FPL Deadline</p>
                <div id="countdown" style="font-size: 1.8rem; color: #D4AF37; font-weight: bold; font-family: monospace;">
                    -- : -- : -- : --
                </div>
            </div>

            <div style="display: grid; gap: 15px;">
                <div style="background: #222; padding: 15px; border-radius: 10px; border-left: 4px solid #D4AF37;">
                    <h4 style="color: #D4AF37; margin: 0 0 5px 0;">Tournament Status</h4>
                    <p style="color: #ccc; margin: 0; font-size: 0.85rem;">Division 1 & 2 Rankings are now live. Playoff seeds will be calculated soon.</p>
                </div>

                <div style="background: #222; padding: 15px; border-radius: 10px; border-left: 4px solid #444;">
                    <h4 style="color: #888; margin: 0 0 5px 0;">Live Matchups</h4>
                    <p style="color: #666; margin: 0; font-size: 0.85rem;">Real-time head-to-head scores will be available once the Gameweek starts.</p>
                </div>
            </div>
        </div>
    `;

    // Countdown Logic ကို စတင်ပါမယ် (ဥပမာ အချိန် - နောက် ၃ ရက်)
    startCountdown();
};

function startCountdown() {
    // မှတ်ချက် - ဒီနေရာမှာ တကယ့် FPL API က Deadline ကို ထည့်လို့ရပါတယ်
    // အခုလောလောဆယ် နမူနာအဖြစ် နောက် ၃ ရက်ကို ပြထားပါမယ်
    const deadline = new Date().getTime() + (3 * 24 * 60 * 60 * 1000);

    const timer = setInterval(() => {
        const now = new Date().getTime();
        const distance = deadline - now;

        const days = Math.floor(distance / (1000 * 60 * 60 * 24));
        const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);

        const countdownEl = document.getElementById('countdown');
        if (countdownEl) {
            countdownEl.innerHTML = `${days}d ${hours}h ${minutes}m ${seconds}s`;
        }

        if (distance < 0) {
            clearInterval(timer);
            if (countdownEl) countdownEl.innerHTML = "GAMEWEEK STARTED!";
        }
    }, 
                              1000);
}
