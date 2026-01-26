/**
 * Tab ပြောင်းလဲခြင်းနှင့် သက်ဆိုင်ရာ Function များကို ခေါ်ယူခြင်း
 */
function showTab(tabId) {
    console.log("Switching to tab:", tabId);

    // ၁။ Navigation Items အားလုံးကို Active Class ဖြုတ်မယ်
    // Query selector ကို .nav-item (index.html မှာ သုံးထားတဲ့ class) အဖြစ် သတ်မှတ်ပါ
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => item.classList.remove('active'));

    // ၂။ လက်ရှိနှိပ်လိုက်တဲ့ Item ကို Active လုပ်မယ်
    const targetItem = document.getElementById(`btn-${tabId}`);
    if (targetItem) {
        targetItem.classList.add('active');
    }

    // ၃။ Content ပြသရမည့် နေရာကို သတ်မှတ်မယ်
    const mainRoot = document.getElementById('main-root');
    if (!mainRoot) return;

    // Tab ပြောင်းတိုင်း အပေါ်ဆုံးကို ပြန်ပို့ပေးမယ် (Mobile UX အတွက်)
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    // ၄။ ရွေးချယ်လိုက်သော Tab အလိုက် Logic များ
    switch(tabId) {
        case 'community':
            if (typeof window.renderCommunity === "function") {
                window.renderCommunity();
            } else {
                mainRoot.innerHTML = `<div class="loading">🏠 Community Hub loading...</div>`;
            }
            break;

        case 'leagues':
            if (typeof window.renderLeagues === "function") {
                window.renderLeagues(); 
            } else {
                mainRoot.innerHTML = `<div class="loading">🏆 Standings loading...</div>`;
            }
            break;

        case 'scout':
            // renderScoutHub သို့မဟုတ် renderScout စစ်ဆေးပါ
            if (typeof window.renderScoutHub === "function") {
                window.renderScoutHub();
            } else if (typeof window.renderScout === "function") {
                window.renderScout();
            } else {
                mainRoot.innerHTML = `<div class="loading">🔭 Scout Hub loading...</div>`;
            }
            break;

        case 'live':
            if (typeof window.renderLiveHub === "function") {
                window.renderLiveHub();
            } else {
                mainRoot.innerHTML = `<div class="loading">⚡ Live Hub loading...</div>`;
            }
            break;

        default:
            console.warn("Unknown tabId:", tabId);
    }
}

/**
 * Firebase Auth အခြေအနေကို စောင့်ကြည့်ပြီး App ကို စတင်ခြင်း
 */
firebase.auth().onAuthStateChanged((user) => {
    // ပထမဆုံးဝင်ဝင်ချင်းမှာ အလုပ်လုပ်စေရန်
    if (user) {
        showTab('live'); // Login ဝင်ထားရင် Live Hub ကို အရင်ပြမယ်
    } else {
        showTab('community'); // Login မရှိရင် Home ကို ပြမယ်
    }
});

/**
 * ၅။ Website အဆင်သင့်ဖြစ်ချိန်တွင် Initialize လုပ်ရန်
 */
window.onload = () => {
    console.log("TW MM Tournament App Re
                ady");
};
