// js/app.js (အချောသတ်ပြင်ဆင်မှု)
function showTab(tabId) {
    console.log("Attempting to show tab:", tabId);

    const buttons = document.querySelectorAll('.nav-btn');
    buttons.forEach(btn => btn.classList.remove('active'));

    const targetBtn = document.getElementById(`btn-${tabId}`);
    if (targetBtn) {
        targetBtn.classList.add('active');
    }

    const mainRoot = document.getElementById('main-root');
    
    if (tabId === 'community') {
        if (typeof renderCommunity === "function") {
            renderCommunity();
        } else {
            mainRoot.innerHTML = "<div class='loading'>Community Hub...</div>";
        }
    } 
    else if (tabId === 'leagues') {
        // window object ထဲမှာ function ရှိမရှိ စစ်တာက ပိုသေချာပါတယ်
        if (typeof window.renderLeagues === "function") {
            window.renderLeagues(); 
        } else {
            mainRoot.innerHTML = "<div class='loading'>System loading... Please refresh.</div>";
            console.error("renderLeagues function is not defined in tournament.js");
        }
    } 
    else if (tabId === 'live') {
        mainRoot.innerHTML = "<div style='text-align:center; padding:50px; color:#D4AF37;'>Coming Soon...</div>";
    }
}

// ဖြည့်စွက်ချက်: window.onload ကို သုံးခြင်းဖြင့် ဖိုင်အားလုံး load ဖြစ်ပြီးမှ စတင်စေပါမယ်
window.onload = () => {
    console.log("All files loaded. Initializing app...");
    showTab('community');
    
};
