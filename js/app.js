/**
 * Tab ပြောင်းလဲခြင်းနှင့် သက်ဆိုင်ရာ Function များကို ခေါ်ယူခြင်း
 */
function showTab(tabId) {
    console.log("Attempting to show tab:", tabId);

    // ၁။ Nav Buttons အားလုံးကို Active Class ဖြုတ်မယ်
    const buttons = document.querySelectorAll('.nav-btn');
    buttons.forEach(btn => btn.classList.remove('active'));

    // ၂။ လက်ရှိနှိပ်လိုက်တဲ့ Button ကို Active လုပ်မယ်
    const targetBtn = document.getElementById(`btn-${tabId}`);
    if (targetBtn) {
        targetBtn.classList.add('active');
    }

    // ၃။ Content ပြသရမည့် နေရာကို သတ်မှတ်မယ်
    const mainRoot = document.getElementById('main-root');
    if (!mainRoot) return;
    
    // ၄။ ရွေးချယ်လိုက်သော Tab အလိုက် Logic များ
    if (tabId === 'community') {
        if (typeof window.renderCommunity === "function") {
            window.renderCommunity();
        } else {
            mainRoot.innerHTML = "<div class='loading'>Welcome to Community Hub...</div>";
        }
    } 
    else if (tabId === 'leagues') {
        // Tournament Rankings ပြရန်
        if (typeof window.renderLeagues === "function") {
            window.renderLeagues(); 
        } else {
            mainRoot.innerHTML = "<div class='loading'>Rankings Loading...</div>";
            console.error("renderLeagues function is not defined in tournament.js");
        }
    } 
    else if (tabId === 'scout') {
        // Official Scouts & Private League ပြရန်
        if (typeof window.renderScoutHub === "function") {
            window.renderScoutHub();
        } else {
            mainRoot.innerHTML = "<div class='loading'>Scout Hub Loading...</div>";
            console.error("renderScoutHub function is not defined in scout.js");
        }
    }
    else if (tabId === 'live') {
        // Live Hub ပိုင်း (Countdown Timer စသည်)
        if (typeof window.renderLiveHub === "function") {
            window.renderLiveHub();
        } else {
            mainRoot.innerHTML = "<div style='text-align:center; padding:50px; color:#D4AF37;'>Live Hub Coming Soon...</div>";
        }
    }
}

// ၅။ Website ဖိုင်အားလုံး (Scripts/Images) Load ဖြစ်ပြီးမှ App ကို စတင်မည်
window.onload = () => {
    console.log("App Initialized Successfully");
    // စဖွင့်ဖွင့်ချင်း Community ကို အရင်ပြထားမယ်
    showTab('community');
    
};
