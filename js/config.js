// js/config.js
const firebaseConfig = {
    apiKey: "AIzaSyDE11cAUZfJoZMMCF-eyqGDUioYDQSCWrs", 
    authDomain: "your-project-id.firebaseapp.com",
    projectId: "your-project-id",
    storageBucket: "your-project-id.appspot.com",
    messagingSenderId: "1234567890",
    appId: "1:1234567890:web:abcdefg"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const db = firebase.firestore();
const auth = firebase.auth();
