// js/app.js
function showTab(tabId) {
    console.log("Attempting to show tab:", tabId);

    // ၁။ Nav Buttons အားလုံးကို Active ဖြုတ်မယ်
    const buttons = document.querySelectorAll('.nav-btn');
    buttons.forEach(btn => btn.classList.remove('active'));

    // ၂။ နှိပ်လိုက်တဲ့ Button ကို Active လုပ်မယ်
    const targetBtn = document.getElementById(`btn-${tabId}`);
    if (targetBtn) {
        targetBtn.classList.add('active');
    }

    // ၃။ Content ပြောင်းလဲခြင်း logic
    const mainRoot = document.getElementById('main-root');
    if (!mainRoot) return;
    
    if (tabId === 'community') {
        if (typeof window.renderCommunity === "function") {
            window.renderCommunity();
        } else {
            mainRoot.innerHTML = "<div class='loading'>Welcome to Community Hub...</div>";
        }
    } 
    else if (tabId === 'leagues') {
        // Tournament Function ကို သေချာစစ်ပြီး ခေါ်မယ်
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

// Website ဖိုင်အားလုံး load ဖြစ်ပြီးမှ စတင်အလုပ်လုပ်ဖို့
window.onload = () => {
    console.log("App Initialized");
    showTab('community');
    
};
