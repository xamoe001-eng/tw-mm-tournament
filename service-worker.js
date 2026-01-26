const CACHE_NAME = 'tw-mm-tournament-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/index.html',
  '/css/style.css',
  '/js/config.js',
  '/js/app.js',
  '/js/tournament.js',
  '/js/auth.js',
  '/js/community.js',
  '/manifest.json',
  '/icons/icon-192.png',
  '/icons/icon-512.png'
];

// Service Worker ကို Install လုပ်ပြီး Assets များကို Cache ထဲထည့်ခြင်း
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('Caching shell assets');
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
});

// အဟောင်းဖြစ်နေသော Cache များကို ရှင်းထုတ်ခြင်း
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
});

// Network မရှိလျှင် Cache ထဲမှ ထုတ်ပြပေးခြင်း (Offline Support)
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
}
                     );
