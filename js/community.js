function renderCommunity() {
    const main = document.getElementById('main-root');
    const user = auth.currentUser;

    main.innerHTML = `
        <div style="padding: 20px;">
            ${user ? `
                <div style="background: #1a1a1a; padding: 15px; border-radius: 8px; border: 1px solid #333; margin-bottom: 20px;">
                    <textarea id="postInput" placeholder="ဘာပြောချင်လဲဗျာ..." 
                        style="width: 100%; background: #000; color: white; border: 1px solid #444; padding: 10px; border-radius: 5px; height: 80px; box-sizing: border-box;"></textarea>
                    <button onclick="savePost()" class="tw-btn-gold" style="margin-top: 10px; width: 100%;">POST တင်မယ်</button>
                </div>
            ` : `
                <div style="text-align: center; color: #a0a0a0; padding: 20px;">
                    Post တင်ရန် အပေါ်က Google Login ကို အရင်နှိပ်ပါဗျ။
                </div>
            `}
            <div id="posts-list"></div>
        </div>
    `;
    loadPosts();
}

function savePost() {
    const text = document.getElementById('postInput').value;
    if (!text.trim()) return alert("စာအရင်ရေးပါဦး!");

    db.collection("tw_posts").add({
        name: auth.currentUser.displayName,
        photo: auth.currentUser.photoURL,
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
        list.innerHTML = snapshot.docs.map(doc => {
            const p = doc.data();
            return `
                <div style="background: #1a1a1a; border-left: 4px solid #D4AF37; padding: 15px; margin-bottom: 10px; border-radius: 4px;">
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                        <img src="${p.photo}" style="width: 30px; height: 30px; border-radius: 50%;">
                        <strong style="color: #D4AF37;">${p.name}</strong>
                    </div>
                    <div style="color: white; line-height: 1.5;">${p.message}</div>
                </div>
            `;
        }).join('');
    })
      ;
}
