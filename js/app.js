// js/app.js
function showTab(tabId) {
    // Nav Buttons အရောင်ပြောင်းရန်
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`btn-${tabId}`).classList.add('active');

    // Content ပြောင်းရန်
    if (tabId === 'community') {
        renderCommunity(); // community.js ထဲက function
    } else if (tabId === 'leagues') {
        renderLeagues();   // tournament.js ထဲက function
    } else if (tabId === 'live') {
        document.getElementById('main-root').innerHTML = "<div class='loading'>Live Hub Coming Soon...</div>";
    }
}

// Website စဖွင့်တာနဲ့ Community ကို အရင်ပြမယ်
window.onload = () => {
    showTab('community');
};
