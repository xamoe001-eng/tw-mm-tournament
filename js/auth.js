/**
 * ၁။ Initialization
 */
const provider = new firebase.auth.GoogleAuthProvider();
const authRoot = document.getElementById('auth-root');

/**
 * ၂။ Auth State Observer (အကောင့်အခြေအနေ စောင့်ကြည့်ခြင်း)
 */
firebase.auth().onAuthStateChanged(async (user) => {
    if (user) {
        // --- LOGIN ဝင်ထားချိန် ---
        try {
            const userDoc = await db.collection("users").doc(user.uid).get();
            let managerName = user.displayName ? user.displayName.split(' ')[0] : "Manager";
            
            if (userDoc.exists) {
                const userData = userDoc.data();
                managerName = userData.manager_name;
                updateProfileModal(userData); // Profile Card ထဲ ဒေတာထည့်မယ်
            }

            // Header မှာ နာမည်ပြမယ်
            authRoot.innerHTML = `
                <div onclick="window.openProfile()" style="display: flex; align-items: center; gap: 8px; cursor: pointer; background: #1a1a1a; padding: 5px 12px; border-radius: 20px; border: 1px solid #333;">
                    <div style="font-size: 1rem;">⚽</div>
                    <span style="color: #D4AF37; font-size: 0.85rem; font-weight: 800;">${managerName}</span>
                </div>
            `;
        } catch (error) {
            console.error("Profile error:", error);
        }
    } else {
        // --- LOGIN ထွက်ထားချိန် ---
        authRoot.innerHTML = `
            <button onclick="window.renderAuthUI()" 
                style="background: transparent; border: 1px solid #D4AF37; color: #D4AF37; padding: 6px 15px; border-radius: 20px; font-weight: 800; font-size: 0.75rem; cursor: pointer;">
                LOGIN
            </button>
        `;
        // အကောင့်မရှိရင် Login Form တန်းပြချင်ရင် (Optional)
        // window.renderAuthUI(); 
    }
});

/**
 * ၃။ UI Rendering Functions
 */
window.renderAuthUI = function() {
    const mainRoot = document.getElementById('main-root');
    mainRoot.innerHTML = `
        <div class="auth-form-container" style="max-width: 400px; margin: 40px auto; padding: 20px; animation: fadeIn 0.3s ease;">
            <div style="display: flex; background: #111; padding: 5px; border-radius: 50px; margin-bottom: 25px; border: 1px solid #222;">
                <button id="tab-login" onclick="window.toggleAuthTab('login')" style="flex: 1; padding: 10px; border-radius: 40px; border: none; background: #D4AF37; color: #000; font-weight: 800; cursor: pointer; transition: 0.3s;">LOGIN</button>
                <button id="tab-signup" onclick="window.toggleAuthTab('signup')" style="flex: 1; padding: 10px; border-radius: 40px; border: none; background: transparent; color: #666; font-weight: 800; cursor: pointer; transition: 0.3s;">SIGN UP</button>
            </div>

            <div id="form-login">
                <input type="email" id="email" class="auth-input" placeholder="Gmail Address">
                <input type="password" id="pass" class="auth-input" placeholder="Password">
                <button onclick="window.handleLogin()" class="primary-btn" style="background: #00ff88; margin-top: 10px;">LOG IN</button>
                <div style="margin: 20px 0; color: #444; font-size: 0.8rem; text-align: center;">OR</div>
                <button onclick="window.loginWithGoogle()" class="primary-btn" style="background: #fff; color: #000; display: flex; align-items: center; justify-content: center; gap: 10px;">
                    GOOGLE LOGIN
                </button>
            </div>

            <div id="form-signup" style="display: none;">
                <input type="text" id="reg-manager" class="auth-input" placeholder="Manager Name">
                <input type="text" id="reg-team" class="auth-input" placeholder="FPL Team Name">
                <input type="text" id="reg-fb" class="auth-input" placeholder="Facebook Link">
                <input type="email" id="reg-email" class="auth-input" placeholder="Email Address">
                <input type="password" id="reg-pass" class="auth-input" placeholder="Password (Min 6 chars)">
                <button onclick="window.handleSignUp()" class="primary-btn" style="margin-top: 10px;">CREATE ACCOUNT</button>
            </div>
        </div>
    `;
};

window.toggleAuthTab = (type) => {
    const isLogin = type === 'login';
    document.getElementById('form-login').style.display = isLogin ? 'block' : 'none';
    document.getElementById('form-signup').style.display = isLogin ? 'none' : 'block';
    document.getElementById('tab-login').style.cssText = isLogin ? 'flex: 1; padding: 10px; border-radius: 40px; background: #D4AF37; color: #000; font-weight: 800;' : 'flex: 1; padding: 10px; border-radius: 40px; background: transparent; color: #666; font-weight: 800;';
    document.getElementById('tab-signup').style.cssText = isLogin ? 'flex: 1; padding: 10px; border-radius: 40px; background: transparent; color: #666; font-weight: 800;' : 'flex: 1; padding: 10px; border-radius: 40px; background: #D4AF37; color: #000; font-weight: 800;';
};

/**
 * ၄။ Auth Logic Functions
 */
window.handleSignUp = async () => {
    const manager = document.getElementById('reg-manager').value;
    const team = document.getElementById('reg-team').value;
    const fb = document.getElementById('reg-fb').value;
    const email = document.getElementById('reg-email').value;
    const pass = document.getElementById('reg-pass').value;

    if (!manager || !email || pass.length < 6) return alert("အချက်အလက်များကို မှန်ကန်အောင် ဖြည့်ပါ");

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
        alert("Account Created!");
        location.reload(); 
    } catch (e) { alert(e.message); }
};

window.handleLogin = () => {
    const email = document.getElementById('email').value;
    const pass = document.getElementById('pass').value;
    if(!email || !pass) return alert("Email နှင့် Password ရိုက်ထည့်ပါ");

    firebase.auth().signInWithEmailAndPassword(email, pass)
        .then(() => { location.reload(); })
        .catch(e => alert("Login မှားယွင်းနေပါသည်။"));
};

window.loginWithGoogle = () => {
    firebase.auth().signInWithPopup(provider).then(() => location.reload()).catch(e => console.error(e));
};

window.handleLogout = () => {
    if(confirm("Logout ထွက်မှာ သေချာပါသလား?")) {
        firebase.auth().signOut().then(() => {
            window.closeProfile();
            location.reload(); // အကောင့်ထွက်ပြီးတာနဲ့ page refresh လုပ်မယ်
        });
    }
};

/**
 * ၅။ Modal & Profile Management
 */
function updateProfileModal(data) {
    if(document.getElementById('prof-manager')) document.getElementById('prof-manager').innerText = data.manager_name;
    if(document.getElementById('prof-team')) document.getElementById('prof-team').innerText = data.team_name;
    if(document.getElementById('prof-fb')) document.getElementById('prof-fb').innerText = data.facebook_name || "-";
    const logoutBtn = document.getElementById('logout-section');
    if(logoutBtn) logoutBtn.style.display = 'block';
}

window.openProfile = () => {
    const modal = document.getElementById('profile-modal');
    if(modal) modal.style.display = 'flex';
};

window.closeProfile = () => {
    const modal = document.getElementById('profile-modal');
    if(modal) modal.style.display = 'none';
};
