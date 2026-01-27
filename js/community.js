// --- CSS Styles (Auto-inject into head) ---
const style = document.createElement('style');
style.innerHTML = `
    .comm-container { max-width: 600px; margin: auto; padding: 20px; font-family: 'Pyidaungsu', sans-serif; }
    .post-box { background: #1a1a1a; padding: 20px; border-radius: 15px; border: 1px solid #333; margin-bottom: 30px; }
    
    /* Profile Image အစား သုံးမည့် စာလုံးဝိုင်း */
    .initial-box { 
        width: 40px; height: 40px; background: linear-gradient(45deg, #222, #444); 
        color: #D4AF37; border-radius: 50%; display: flex; align-items: center; 
        justify-content: center; font-weight: bold; border: 1px solid #444; 
        cursor: pointer; text-transform: uppercase; font-size: 18px;
    }

    .post-card { 
        background: #1a1a1a; border: 1px solid #333; padding: 18px; 
        margin-bottom: 15px; border-radius: 12px; transition: 0.3s; 
    }
    .post-card:hover { border-color: #D4AF37; }
    
    .post-btn { 
        background: #D4AF37; color: black; font-weight: bold; border: none; 
        padding: 12px; border-radius: 8px; cursor: pointer; width: 100%; margin-top: 10px;
    }
    .post-btn:hover { background: #f2d06b; }
    
    .post-input { 
        width: 100%; background: #0b0b0b; color: white; border: 1px solid #444; 
        padding: 12px; border-radius: 10px; height: 100px; box-sizing: border-box; 
        outline: none; resize: none; margin-top: 10px;
    }
    .status-online { color: #4caf50; font-size: 11px; }
`;
document.head.appendChild(style);

// --- Main Functions ---

function renderCommunity() {
    const main = document.getElementById('main-root');
    const user = auth.currentUser;

    main.innerHTML = `
        <div class="comm-container">
            <h2 style="color: #D4AF37; text-align: center;">🤝 Community Hub ✨</h2>
            
            ${user ? `
                <div class="post-box">
                    <div style="display: flex; gap: 12px; align-items: center;">
                        <div class="initial-box">${user.displayName.charAt(0)}</div>
                        <div>
                            <span style="color: white; font-weight: bold;">${user.displayName}</span><br>
                            <small class="status-online">● Online</small>
                        </div>
                    </div>
                    <textarea id="postInput" class="post-input" placeholder="ဒီနေ့ ဘာထူးသလဲဗျာ... ✍️"></textarea>
                    <button onclick="savePost()" class="post-btn">🚀 POST တင်မယ်</button>
                </div>
            ` : `
                <div style="text-align: center; background: #1a1a1a; color: #a0a0a0; padding: 30px; border-radius: 15px; border: 1px dashed #444;">
                    👋 Post တင်ဖို့ Google Login အရင်ဝင်ပေးပါဦးဗျ။
                </div>
            `}

            <div id="posts-list">
                <p style="color: gray; text-align: center;">စာလေးတွေ ရှာနေတယ် ခနစောင့်နော်... ⌛</p>
            </div>
        </div>
    `;
    loadPosts();
}

function savePost() {
    const text = document.getElementById('postInput').value;
    if (!text.trim()) return alert("စာလေး တစ်ခုခု အရင်ရေးပါဦး! 😅");

    db.collection("tw_posts").add({
        name: auth.currentUser.displayName,
        uid: auth.currentUser.uid,
        message: text,
        timestamp: firebase.firestore.FieldValue.serverTimestamp()
    }).then(() => {
        document.getElementById('postInput').value = "";
    });
}

function loadPosts() {
    db.collection("tw_posts").orderBy("timestamp", "desc").onSnapshot(snapshot => {
        const list = document.getElementById('posts-list');
        if (!list) return;

        if (snapshot.empty) {
            list.innerHTML = "<p style='color: gray; text-align: center;'>ဘာမှမရှိသေးဘူး ပထမဆုံး Post တင်လိုက်ပါ! 📣</p>";
            return;
        }

        list.innerHTML = snapshot.docs.map(doc => {
            const p = doc.data();
            const time = p.timestamp ? new Date(p.timestamp.seconds * 1000).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : 'ခုနလေးတင်';
            const initial = p.name ? p.name.charAt(0).toUpperCase() : '?';

            return `
                <div class="post-card">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                        <div class="initial-box" onclick="viewProfile('${p.uid}', '${p.name}')">${initial}</div>
                        <div>
                            <strong style="color: #D4AF37; cursor: pointer;" onclick="viewProfile('${p.uid}', '${p.name}')">${p.name} 👤</strong>
                            <div style="color: #666; font-size: 11px;">${time}</div>
                        </div>
                    </div>
                    <div style="color: #e0e0e0; line-height: 1.6; font-size: 15px; white-space: pre-wrap;">${p.message}</div>
                    
                    <div style="margin-top: 15px; border-top: 1px solid #222; padding-top: 10px; display: flex; gap: 20px;">
                        <span style="color: #888; cursor: pointer; font-size: 13px;">❤️ Like</span>
                        <span style="color: #888; cursor: pointer; font-size: 13px;" onclick="alert('Comment feature မကြာခင် လာပါတော့မယ်! 🔜')">💬 Comment</span>
                    </div>
                </div>
            `;
        }).join('');
    });
}

function viewProfile(uid, name) {
    alert(`👤 User Details\n----------\nအမည်: ${name}\nID: ${uid}\n\nအချင်းချင်း စာပို့နိုင်တဲ့ Private Message feature ကို မကြာခင် ထပ်ထည့်ပေးပါမယ်! 💌`);
}
