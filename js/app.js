// js/app.js
function showTab(tabId) {
    console.log("Attempting to show tab:", tabId); // Console မှာ စစ်ဖို့

    // ၁။ Nav Buttons အားလုံးကို Active ဖြုတ်မယ်
    const buttons = document.querySelectorAll('.nav-btn');
    buttons.forEach(btn => btn.classList.remove('active'));

    // ၂။ နှိပ်လိုက်တဲ့ Button ကို Active လုပ်မယ်
    const targetBtn = document.getElementById(`btn-${tabId}`);
    if (targetBtn) {
        targetBtn.classList.add('active');
    } else {
        console.error(`Button with ID btn-${tabId} not found!`);
    }

    // ၃။ Content ပြောင်းမယ်
    const mainRoot = document.getElementById('main-root');
    
    if (tabId === 'community') {
        if (typeof renderCommunity === "function") {
            renderCommunity();
        } else {
            console.error("renderCommunity function is not defined in community.js");
        }
    } 
    else if (tabId === 'leagues') {
        if (typeof renderLeagues === "function") {
            renderLeagues();
        } else {
            // ဒီနေရာမှာ function မရှိသေးရင် အောက်ကစာသားပေါ်လာမယ်
            mainRoot.innerHTML = "<div class='loading'>League loading function not found...</div>";
            console.error("renderLeagues function is not defined in tournament.js");
        }
    } 
    else if (tabId === 'live') {
        mainRoot.innerHTML = "<div style='text-align:center; padding:50px; color:#D4AF37;'>Coming Soon...</div>";
    }
}

// Website စဖွင့်တာနဲ့ စတင်အလုပ်လုပ်ဖို့
document.addEventListener('DOMContentLoaded', () => {
    console.log("App Initialized");
    showTab('community');

});
