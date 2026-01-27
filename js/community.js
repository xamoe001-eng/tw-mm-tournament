// --- CSS Styles (ဒါကို HTML ရဲ့ <style> tag ထဲ ထည့်ထားပေးပါ) ---
const style = document.createElement('style');
style.innerHTML = `
    .post-card {
        background: #1e1e1e;
        border: 1px solid #333;
        padding: 15px;
        margin-bottom: 15px;
        border-radius: 12px;
        transition: 0.3s;
    }
    .post-card:hover { border-color: #D4AF37; transform: translateY(-2px); }
    .user-avatar { width: 40px; height: 40px; border-radius: 50%; border: 2px solid #D4AF37; cursor: pointer; }
    .post-btn { 
        background: linear-gradient(45deg, #D4AF37, #f2d06b);
        color: black; font-weight: bold; border: none; padding: 10px;
        border-radius: 8px; cursor: pointer; transition: 0.3s;
    }
    .post-btn:hover { opacity: 0.8; box-shadow: 0 0 10px rgba(212, 175, 55, 0.4); }
    .status-online { color: #4caf50; font-size: 12px; }
`;
document.head.appendChild(style);

// --- Main Functions ---

function renderCommunity() {
    const main = document.getElementById('main-root');
    const user = auth.currentUser;

    main.innerHTML = `
        <div style="max-width: 600px; margin: auto; padding: 20px;">
            <h2 style="color: #D4AF37; text-align: center;">🤝 Community Hub ✨</h2>
            
            ${user ? `
                <div style="background: #1a1a1a; padding: 20px; border-radius: 15px; border: 1px solid #333; margin-bottom: 30px;">
                    <div style="display: flex; gap: 10px; margin-bottom: 10px;">
                        <img src="${user.photoURL}" class="user-avatar" title="ဒါ မင်းရဲ့ Profile ပါ">
                        <span style="color: white; font-weight: bold;">${user.displayName} <br> <small class="status-online">● Online</small></span>
                    </div>
                    <textarea id="postInput" placeholder="ဒီနေ့ ဘာထူးသလဲဗျာ... ✍️" 
                        style="width: 100%; background: #0b0b0b; color: white; border: 1px solid #444; padding: 12px; border-radius: 10px; height: 100px; box-sizing: border-box; outline: none;"></textarea>
                    <button onclick="savePost()" class="post-btn" style="margin-top: 10px; width: 100%;">🚀 POST တင်မယ်</button>
                </div>
            ` : `
                <div style="text-align: center; background: #1a1a1a; color: #a0a0a0; padding: 30px; border-radius: 15px; border: 1px dashed #444;">
                    👋 အရင်ဆုံး Login ဝင်ပေးပါဦးဗျ။ <br><br>
                    နွေးထွေးတဲ့ Community ထဲမှာ စကားပြောဖို့ စောင့်နေပါတယ်။ 😊
                </div>
            `}

            <div id="posts-list" style="margin-top: 20px;">
                <p style="color: gray; text-align: center;">စာလေးတွေ ရှာနေတယ် ခနစောင့်နော်... ⌛</p>
            </div>
        </div>
    `;
    loadPosts();
}

function savePost() {
    const text = document.getElementById('postInput').value;
    if (!text.trim()) return alert("စာအရင်ရေးပါဦး! 😅");

    db.collection("tw_posts").add({
        name: auth.currentUser.displayName,
        photo: auth.currentUser.photoURL,
        uid: auth.currentUser.uid, // User ID သိမ်းထားမှ Profile နှိပ်ရင် ဘယ်သူလဲ သိမှာ
        message: text,
        timestamp: firebase.firestore.FieldValue.serverTimestamp()
    }).then(() => {
        document.getElementById('postInput').value = "";
        console.log("Post success! 🎉");
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
            const time = p.timestamp ? new Date(p.timestamp.seconds * 1000).toLocaleString() : 'ခုနလေးတင်';

            return `
                <div class="post-card">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                        <img src="${p.photo}" class="user-avatar" onclick="viewProfile('${p.uid}', '${p.name}')">
                        <div>
                            <strong style="color: #D4AF37; cursor: pointer;" onclick="viewProfile('${p.uid}', '${p.name}')">${p.name} 👤</strong>
                            <div style="color: #666; font-size: 11px;">${time}</div>
                        </div>
                    </div>
                    <div style="color: #e0e0e0; line-height: 1.6; font-size: 15px; white-space: pre-wrap;">${p.message}</div>
                    
                    <div style="margin-top: 15px; border-top: 1px solid #333; padding-top: 10px; display: flex; gap: 15px;">
                        <span style="color: #888; cursor: pointer; font-size: 13px;">❤️ Like</span>
                        <span style="color: #888; cursor: pointer; font-size: 13px;" onclick="alert('Comment feature Coming Soon! 🔜')">💬 Comment</span>
                    </div>
                </div>
            `;
        }).join('');
    });
}

function viewProfile(uid, name) {
    alert(`ဒါကတော့ "${name}" ရဲ့ Profile ဖြစ်ပါတယ်ခင်ဗျာ။ \nUser ID: ${uid} \n\nMessage ပို့တဲ့ Feature လေး မကြာခင် လာပါမယ်! 💌`);
}
