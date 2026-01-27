// --- 🎨 UI Styles Injection ---
const style = document.createElement('style');
style.innerHTML = `
    .comm-container { max-width: 600px; margin: auto; padding: 20px; font-family: sans-serif; color: white; }
    .post-card { background: #1a1a1a; border: 1px solid #333; padding: 15px; margin-bottom: 15px; border-radius: 12px; }
    .initial-box { 
        width: 40px; height: 40px; background: linear-gradient(45deg, #D4AF37, #aa8c2c); 
        color: black; border-radius: 50%; display: flex; align-items: center; 
        justify-content: center; font-weight: bold; cursor: pointer; font-size: 18px;
    }
    .post-btn { 
        background: #D4AF37; color: black; font-weight: bold; border: none; 
        padding: 10px; border-radius: 8px; cursor: pointer; width: 100%; margin-top: 10px;
    }
    .chat-modal {
        position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
        background: #111; border: 1px solid #D4AF37; padding: 20px; border-radius: 15px;
        z-index: 1000; width: 90%; max-width: 400px; box-shadow: 0 0 20px rgba(0,0,0,0.8);
    }
    .overlay { position: fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.7); z-index:999; }
    .status-online { color: #4caf50; font-size: 11px; }
`;
document.head.appendChild(style);

// --- 🛠️ Core Functions ---

function renderCommunity() {
    const main = document.getElementById('main-root');
    const user = auth.currentUser;

    main.innerHTML = `
        <div class="comm-container">
            <h2 style="color: #D4AF37; text-align: center;">🤝 Community Hub ✨</h2>
            ${user ? `
                <div style="background: #1a1a1a; padding: 15px; border-radius: 15px; border: 1px solid #333; margin-bottom: 25px;">
                    <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 10px;">
                        <div class="initial-box">${user.displayName.charAt(0)}</div>
                        <strong>${user.displayName} <br><small class="status-online">● Online</small></strong>
                    </div>
                    <textarea id="postInput" style="width:100%; background:#000; color:white; border:1px solid #444; padding:10px; border-radius:8px; height:80px; resize:none;" placeholder="ဘာတွေပြောချင်လဲ..."></textarea>
                    <button onclick="savePost()" class="post-btn">🚀 POST တင်မယ်</button>
                </div>
            ` : `<div style="text-align:center; padding:20px;">Login ဝင်ပြီးမှ Post တင်လို့ရပါမယ်ဗျ။</div>`}
            <div id="posts-list"></div>
        </div>
        <div id="modal-container"></div>
    `;
    loadPosts();
}

function savePost() {
    const text = document.getElementById('postInput').value;
    const user = auth.currentUser;
    if (!text.trim()) return alert("စာအရင်ရေးပါ!");

    db.collection("tw_posts").add({
        name: user.displayName,
        uid: user.uid, // UID သေချာထည့်လိုက်ပြီ
        message: text,
        timestamp: firebase.firestore.FieldValue.serverTimestamp()
    }).then(() => { document.getElementById('postInput').value = ""; });
}

function loadPosts() {
    db.collection("tw_posts").orderBy("timestamp", "desc").onSnapshot(snapshot => {
        const list = document.getElementById('posts-list');
        if (!list) return;
        list.innerHTML = snapshot.docs.map(doc => {
            const p = doc.data();
            const time = p.timestamp ? new Date(p.timestamp.seconds * 1000).toLocaleTimeString() : 'Just now';
            return `
                <div class="post-card">
                    <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px;">
                        <div class="initial-box" onclick="openProfile('${p.uid}', '${p.name}')">${p.name ? p.name.charAt(0) : '?'}</div>
                        <div>
                            <strong style="color:#D4AF37; cursor:pointer;" onclick="openProfile('${p.uid}', '${p.name}')">${p.name}</strong>
                            <div style="color:#666; font-size:10px;">${time}</div>
                        </div>
                    </div>
                    <div style="font-size:15px; line-height:1.5;">${p.message}</div>
                    <div style="margin-top:10px; display:flex; gap:15px; color:#777; font-size:13px;">
                        <span style="cursor:pointer;">❤️ Like</span>
                        <span style="cursor:pointer;" onclick="openProfile('${p.uid}', '${p.name}')">💬 Message / Chat</span>
                    </div>
                </div>
            `;
        }).join('');
    });
}

// --- 💬 Chat & Profile System ---

function openProfile(targetUid, targetName) {
    const currentUser = auth.currentUser;
    if (!currentUser) return alert("Login အရင်ဝင်ပါ!");
    if (currentUser.uid === targetUid) return alert("ဒါက သင့်ကိုယ်ပိုင် Profile ပါ!");

    const modalContainer = document.getElementById('modal-container');
    modalContainer.innerHTML = `
        <div class="overlay" onclick="closeModal()"></div>
        <div class="chat-modal">
            <h3 style="color:#D4AF37; margin-top:0;">👤 ${targetName}</h3>
            <p style="font-size:12px; color:#888;">User ID: ${targetUid}</p>
            <hr border="1" style="border-color:#333;">
            <div id="chat-box" style="height:150px; overflow-y:auto; margin-bottom:10px; padding:5px; background:#000; border-radius:5px; font-size:13px;">
                <p style="color:#555; text-align:center;">စာတိုလေး ပို့နှုတ်ဆက်လိုက်ပါ 💌</p>
            </div>
            <div style="display:flex; gap:5px;">
                <input type="text" id="chatInput" style="flex:1; background:#222; color:white; border:1px solid #444; padding:8px; border-radius:5px;" placeholder="စာရေးရန်...">
                <button onclick="sendPrivateMsg('${targetUid}')" style="background:#D4AF37; border:none; border-radius:5px; padding:0 15px; font-weight:bold; cursor:pointer;">Send</button>
            </div>
            <button onclick="closeModal()" style="width:100%; background:none; border:none; color:#666; margin-top:15px; cursor:pointer;">ပိတ်မည်</button>
        </div>
    `;
    listenToMessages(targetUid);
}

function sendPrivateMsg(targetUid) {
    const text = document.getElementById('chatInput').value;
    if (!text.trim()) return;

    db.collection("tw_messages").add({
        senderId: auth.currentUser.uid,
        receiverId: targetUid,
        senderName: auth.currentUser.displayName,
        text: text,
        timestamp: firebase.firestore.FieldValue.serverTimestamp()
    }).then(() => {
        document.getElementById('chatInput').value = "";
    });
}

function listenToMessages(targetUid) {
    const myUid = auth.currentUser.uid;
    const chatBox = document.getElementById('chat-box');

    // နှစ်ယောက်ကြားက စာတွေကို ယူမယ်
    db.collection("tw_messages")
        .orderBy("timestamp", "asc")
        .onSnapshot(snapshot => {
            const msgs = snapshot.docs.filter(doc => {
                const d = doc.data();
                return (d.senderId === myUid && d.receiverId === targetUid) || 
                       (d.senderId === targetUid && d.receiverId === myUid);
            });

            chatBox.innerHTML = msgs.map(doc => {
                const m = doc.data();
                const isMe = m.senderId === myUid;
                return `<div style="text-align: ${isMe ? 'right' : 'left'}; margin-bottom:8px;">
                            <span style="background:${isMe ? '#D4AF37' : '#333'}; color:${isMe ? 'black' : 'white'}; padding:5px 10px; border-radius:10px; display:inline-block;">
                                ${m.text}
                            </span>
                        </div>`;
            }).join('');
            chatBox.scrollTop = chatBox.scrollHeight;
        });
}

function closeModal() {
    document.getElementById('modal-container').innerHTML = "";
}
