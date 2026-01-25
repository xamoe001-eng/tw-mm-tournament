// Google Login ပြုလုပ်ရန် Provider သတ်မှတ်ခြင်း
const provider = new firebase.auth.GoogleAuthProvider();

// UI ရဲ့ နေရာကို သတ်မှတ်ခြင်း
const authRoot = document.getElementById('auth-root');

// Login အခြေအနေကို စောင့်ကြည့်စစ်ဆေးခြင်း
auth.onAuthStateChanged((user) => {
    if (user) {
        // User Login ဝင်ထားလျှင်: Profile ပုံနှင့် Logout ခလုတ်ပြမည်
        authRoot.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <img src="${user.photoURL}" alt="User" 
                     style="width: 35px; height: 35px; border-radius: 50%; border: 1px solid #D4AF37;">
                <span style="color: #D4AF37; font-size: 0.9rem; font-weight: bold;">
                    ${user.displayName.split(' ')[0]}
                </span>
                <button onclick="logout()" 
                        style="background: none; border: 1px solid #444; color: #a0a0a0; 
                               padding: 5px 10px; cursor: pointer; border-radius: 4px; font-size: 0.8rem;">
                    Logout
                </button>
            </div>
        `;
        
        // Login ဝင်ပြီးသွားလျှင် Community Feed ကို Refresh လုပ်ပေးရန် (လိုအပ်ပါက)
        if (typeof renderCommunity === "function") {
            renderCommunity();
        }
    } else {
        // User Login မဝင်ထားလျှင်: Login ခလုတ်ပြမည်
        authRoot.innerHTML = `
            <button onclick="login()" class="tw-btn-gold">
                GOOGLE LOGIN
            </button>
        `;
        
        // Login ထွက်သွားလျှင် Community ကို Guest View အဖြစ် ပြန်ပြရန်
        if (typeof renderCommunity === "function") {
            renderCommunity();
        }
    }
});

// Login လုပ်ဆောင်ချက်
function login() {
    auth.signInWithPopup(provider)
        .then((result) => {
            console.log("Login Successful:", result.user.displayName);
        })
        .catch((error) => {
            console.error("Login Error:", error.message);
            alert("Login လုပ်လို့မရပါဘူး: " + error.message);
        });
}

// Logout လုပ်ဆောင်ချက်
function logout() {
    auth.signOut().then(() => {
        console.log("Logged Out");
    }).catch((error) => {
        console.error("Logout Error:", error.message);
    })
      ;
}
