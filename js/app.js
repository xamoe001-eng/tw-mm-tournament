/**
 * Tab Switching Logic - Page တစ်ခုချင်းစီကို ချိတ်ဆက်ပေးခြင်း
 */
window.showTab = function(tabId) {
    console.log("Navigating to:", tabId);

    // ၁။ Navigation UI Update: အရင် Active ဖြစ်နေတာတွေကို ဖြုတ်ပြီး အသစ်ကို Active လုပ်မယ်
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => item.classList.remove('active'));

    const targetItem = document.getElementById(`btn-${tabId}`);
    if (targetItem) {
        targetItem.classList.add('active');
    }

    // ၂။ Content Area ကို ရှာဖွေခြင်း
    const mainRoot = document.getElementById('main-root');
    if (!mainRoot) return;

    // Mobile UX အတွက် Tab ပြောင်းတိုင်း အပေါ်ဆုံးကို Smooth ဖြစ်အောင် ပို့ပေးမည်
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // ၃။ သက်ဆိုင်ရာ JS ဖိုင်များထဲက Rendering Function များကို ခေါ်ယူခြင်း
    switch(tabId) {
        case 'community':
            if (typeof window.renderCommunity === "function") {
                window.renderCommunity();
            } else {
                mainRoot.innerHTML = `<div class="loading">🏠 Community Page Loading...</div>`;
            }
            break;

        case 'leagues':
            if (typeof window.renderLeagues === "function") {
                window.renderLeagues();
            } else {
                mainRoot.innerHTML = `<div class="loading">🏆 Standings Data Loading...</div>`;
            }
            break;

        case 'scout':
            // scout.js ထဲမှာ renderScoutHub ဒါမှမဟုတ် renderScout လို့ ပေးထားတာကို စစ်ဆေးခေါ်ယူမည်
            if (typeof window.renderScoutHub === "function") {
                window.renderScoutHub();
            } else if (typeof window.renderScout === "function") {
                window.renderScout();
            } else {
                mainRoot.innerHTML = `<div class="loading">🔭 Scout Hub Loading...</div>`;
            }
            break;

        case 'live':
            if (typeof window.renderLiveHub === "function") {
                window.renderLiveHub();
            } else {
                mainRoot.innerHTML = `<div class="loading">⚡ Live Match Hub Loading...</div>`;
            }
            break;

        default:
            console.warn("Unknown tabId encountered:", tabId);
    }
};

/**
 * Firebase Auth အခြေအနေကို စောင့်ကြည့်ပြီး App ကို စတင်ခြင်း
 */
firebase.auth().onAuthStateChanged((user) => {
    // Login ဝင်ထားလျှင် Live Hub ကို အရင်ပြမည်၊ မဟုတ်လျှင် Community ပြမည်
    if (user) {
        showTab('live');
    } else {
        showTab('community');
    }
});

// App ready status log
window.onload = () => {
    console.log("TW MM App: Global scripts loaded and re
                ady.");
};
