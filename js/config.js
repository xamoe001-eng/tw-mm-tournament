// Firebase Configuration (မိတ်ဆွေရဲ့ Project Keys များ)
const firebaseConfig = {
  apiKey: "AIzaSyDE11cAUZfJoZMMCF-eyqGDUioYDQSCWrs",
  authDomain: "tw-fpl-tour.firebaseapp.com",
  projectId: "tw-fpl-tour",
  storageBucket: "tw-fpl-tour.firebasestorage.app",
  messagingSenderId: "1023019839565",
  appId: "1:1023019839565:web:e91650d5c475c54a63ec04",
  measurementId: "G-48KP6S02RK"
};

// Firebase ကို စတင်ချိတ်ဆက်ခြင်း (Compatibility Version)
firebase.initializeApp(firebaseConfig);

// Database နှင့် Login အတွက် Variable များ သတ်မှတ်ခြင်း
const db = firebase.firestore();
const auth = firebase.auth();

// Analytics (Optional - ထည့်ထားချင်ရင်)
const analytics = firebase.analytics();

console.log("TW MM Tournament - Firebase Connected! 🏆");
