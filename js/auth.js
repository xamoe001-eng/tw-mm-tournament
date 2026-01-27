/**
 * ၁။ Initialization & Providers
 */
const provider = new firebase.auth.GoogleAuthProvider();
const authRoot = document.getElementById('auth-root');

/**
 * ၂။ Login အခြေအနေကို စောင့်ကြည့်ခြင်း (Auth State Observer)
 */
firebase.auth().onAuthStateChanged(async (user) => {
    if (user) {
        // User ရှိလျှင် Firestore မှ Profile Data ကိုယူမည်
        try {
            const userDoc = await db.collection("users").doc(user.uid).get();
            let managerName = user.displayName ? user.displayName.split(' ')[0] : "Manager";
            
            if (userDoc.exists) {
                managerName = userDoc.data().manager_name;
                // Profile Modal ထဲသို့ Data များ ထည့်သွင်းခြင်း
                updateProfileModal(userDoc.data());
            }

            // Header UI ကို Profile ပြောင်းလဲခြင်း
            authRoot.innerHTML = `
                <div onclick="window.openProfile()" style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                    <div style="width: 32px; height: 32px; background: #222; border: 1.5px solid #D4AF37; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.8rem;">
                        ⚽
                    </div>
                    <span style="color: #D4AF37; font-size: 0.85rem; font-weight: 800;">${managerName}</span>
                </div>
            `;
        } catch (error) {
            console.error("Error fetching user profile:", error);
        }
        
    } else {
        // Login မဝင်ထားလျှင် Login ခလုတ်ပြမည်
        authRoot.innerHTML = `
            <button onclick="window.renderAuthUI()" 
                style="background: transparent; border: 1px solid #D4AF37; color: #D4AF37; padding: 6px 15px; border-radius: 20px; font-weight: 800; font-size: 0.75rem; cursor: pointer;">
                LOGIN
            </button>
        `;
    }

    // Tab များကို Refresh လုပ်ရန်
    if (window.currentTab === 'community') window.renderCommunity();
});

/**
 * ၃။ Auth UI Render လုပ်ခြင်း (Login/Sign Up Form)
 */
window.renderAuthUI = function() {
    const mainRoot = document.getElementById('main-root');
    mainRoot.innerHTML = `
        <div class="auth-form-container" style="max-width: 400px; margin: 40px auto; padding: 20px;">
            <div style="display: flex; background: #111; padding: 5px; border-radius: 50px; margin-bottom: 25px; border: 1px solid #222;">
                <button id="tab-login" onclick="window.toggleAuthTab('login')" style="flex: 1; padding: 10px; border-radius: 40px; border: none; background: #D4AF37; color: #000; font-weight: 800; cursor: pointer;">LOGIN</button>
                <button id="tab-signup" onclick="window.toggleAuthTab('signup')" style="flex: 1; padding: 10px; border-radius: 40px; border: none; background: transparent; color: #666; font-weight: 800; cursor: pointer;">SIGN UP</button>
            </div>

            <div id="form-login">
                <input type="email" id="email" class="auth-input" placeholder="Gmail Address">
                <input type="password" id="pass" class="auth-input" placeholder="Password">
                <button onclick="window.handleLogin()" class="primary-btn" style="background: #00ff88;">LOG IN</button>
                <div style="margin: 20px 0; color: #444; font-size: 0.8rem;">OR</div>
                <button onclick="window.loginWithGoogle()" class="primary-btn" style="background: #fff; color: #000; display: flex; align-items: center; justify-content: center; gap: 10px;">
                    <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/pwa_loader.gif" style="width:20px; display:none;"> GOOGLE LOGIN
                </button>
            </div>

            <div id="form-signup" style="display: none;">
                <input type="text" id="reg-manager" class="auth-input" placeholder="Manager Name">
                <input type="text" id="reg-team" class="auth-input" placeholder="FPL Team Name">
                <input type="text" id="reg-fb" class="auth-input" placeholder="Facebook Name/Link">
                <input type="email" id="reg-email" class="auth-input" placeholder="Email Address">
                <input type="password" id="reg-pass" class="auth-input" placeholder="Password (Min 6 chars)">
                <button onclick="window.handleSignUp()" class="primary-btn">CREATE ACCOUNT</button>
            </div>
        </div>
    `;
};

/**
 * ၄။ Logic Functions
 */
window.toggleAuthTab = (type) => {
    const isLogin = type === 'login';
    document.getElementById('form-login').style.display = isLogin ? 'block' : 'none';
    document.getElementById('form-signup').style.display = isLogin ? 'none' : 'block';
    document.getElementById('tab-login').style.background = isLogin ? '#D4AF37' : 'transparent';
    document.getElementById('tab-login').style.color = isLogin ? '#000' : '#666';
    document.getElementById('tab-signup').style.background = isLogin ? 'transparent' : '#D4AF37';
    document.getElementById('tab-signup').style.color = isLogin ? '#666' : '#000';
};

window.handleSignUp = async () => {
    const manager = document.getElementById('reg-manager').value;
    const team = document.getElementById('reg-team').value;
    const fb = document.getElementById('reg-fb').value;
    const email = document.getElementById('reg-email').value;
    const pass = document.getElementById('reg-pass').value;

    if (!manager || !email || pass.length < 6) return alert("အချက်အလက်များကို မှန်ကန်အောင် ဖြည့်ပါ (Password အနည်းဆုံး ၆ လုံး)");

    try {
        const res = await firebase.auth().createUserWithEmailAndPassword(email, pass);
        await db.collection("users").doc(res.user.uid).set({
            uid: res.user.uid,
            manager_name: manager,
            team_name: team,
            facebook_name: fb,
            email: email,
            role: 'member',
            joined_at: firebase.firestore.FieldValue.serverTimestamp()
        });
        alert("အကောင့်ဖွင့်ခြင်း အောင်မြင်ပါသည်။");
        window.showTab('leagues'); // Login ဝင်ပြီးနောက် Standings သို့ သွားမည်
    } catch (e) { alert(e.message); }
};

window.handleLogin = () => {
    const email = document.getElementById('email').value;
    const pass = document.getElementById('pass').value;
    firebase.auth().signInWithEmailAndPassword(email, pass)
        .then(() => { alert("Welcome Back!"); window.showTab('leagues'); })
        .catch(e => alert("အီးမေးလ် သို့မဟုတ် Password မှားနေပါသည်"));
};

window.loginWithGoogle = () => {
    firebase.auth().signInWithPopup(provider).catch(e => console.error(e));
};

window.handleLogout = () => {
    firebase.auth().signOut().then(() => {
        window.closeProfile();
        location.reload();
    });
};

/**
 * ၅။ Profile Modal Functions
 */
function updateProfileModal(data) {
    document.getElementById('prof-manager').innerText = data.manager_name || "Manager";
    document.getElementById('prof-team').innerText = data.team_name || "Team Name";
    document.getElementById('prof-fb').innerText = data.facebook_name || "-";
    document.getElementById('logout-section').style.display = 'block';
}

window.openProfile = () => {
    document.getElementById('profile-modal').style.display = 'flex';
};

window.closeProfile = () => {
    document.getElementById('profile-modal').style.display = 'none';
};
