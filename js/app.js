/**
 * Tab ပြောင်းလဲခြင်းနှင့် သက်ဆိုင်ရာ Function များကို ခေါ်ယူခြင်း
 */
function showTab(tabId) {
    console.log("Switching to tab:", tabId);

    // ၁။ Navigation Items အားလုံးကို Active Class ဖြုတ်မယ်
    // index.html အသစ်မှာ .nav-btn အစား .nav-item ကို သုံးထားလို့ ပြန်ညှိပေးထားပါတယ်
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

    // Tab ပြောင်းတိုင်း အပေါ်ဆုံးကို ပြန်ပို့ပေးမယ် (Mobile User Experience အတွက်)
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    // ၄။ ရွေးချယ်လိုက်သော Tab အလိုက် Logic များ
    switch(tabId) {
        case 'community':
            if (typeof window.renderCommunity === "function") {
                window.renderCommunity();
            } else {
                mainRoot.innerHTML = `
                    <div style="text-align:center; padding:100px 20px;">
                        <h2 style="color:#D4AF37;">COMMUNITY</h2>
                        <p style="color:#888;">Coming Soon...</p>
                    </div>`;
            }
            break;

        case 'leagues':
            if (typeof window.renderLeagues === "function") {
                window.renderLeagues(); 
            } else {
                mainRoot.innerHTML = "<div class='loading'>🏆 Standings Loading...</div>";
                console.error("renderLeagues function not found in tournament.js");
            }
            break;

        case 'scout':
            if (typeof window.renderScoutHub === "function") {
                window.renderScoutHub();
            } else {
                mainRoot.innerHTML = "<div class='loading'>🔭 Scout Hub Loading...</div>";
                console.error("renderScoutHub function not found in scout.js");
            }
            break;

        case 'live':
            if (typeof window.renderLiveHub === "function") {
                window.renderLiveHub();
            } else {
                mainRoot.innerHTML = `
                    <div style="text-align:center; padding:100px 20px;">
                        <h2 style="color:#00ff88;">LIVE HUB</h2>
                        <p style="color:#888;">Match Day Data Coming Soon...</p>
                    </div>`;
            }
            break;

        default:
            mainRoot.innerHTML = "<div class='loading'>Error: Page Not Found</div>";
    }
}

/**
 * Firebase Auth အခြေအနေကို စောင့်ကြည့်ပြီး App ကို စတင်ခြင်း
 */
firebase.auth().onAuthStateChanged((user) => {
    console.log("Auth State Changed. User:", user ? user.displayName : "Logged Out");
    
    // Auth ကနေ User ရှိ/မရှိ စစ်ဆေးပြီးမှ Tab စပြမယ်
    // စဖွင့်ဖွင့်ချင်း Live Hub ကို ပြချင်ရင် 'live' လို့ ပြောင်းနိုင်ပါတယ်
    if (user) {
        showTab('live');
    } else {
        showTab('community');
    }
});

/**
 * ၅။ Website အဆင်သင့်ဖြစ်ချိန်တွင် Initialize လုပ်ရန်
 */
window.onload = () => {
    console.log("TW MM Tournament App Initiali
                zed");
};
