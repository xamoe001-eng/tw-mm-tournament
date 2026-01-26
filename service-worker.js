const CACHE_NAME = 'twmm-v3'; // Version ပြောင်းပေးမှ ဖုန်းထဲမှာ Update ဖြစ်မှာပါ
const ASSETS = [
  './',
  'index.html',
  'css/style.css',
  'js/config.js',
  'js/app.js',
  'js/tournament.js',
  'js/auth.js',
  'js/community.js',
  'js/scout.js',
  'js/live-hub.js',
  'manifest.json',
  'icon-192.png',
  'icon-512.png',
  'scout_data.json' // <--- ဒီဖိုင်ကို ထည့်ဖို့ လိုအပ်ပါတယ်
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      console.log('Caching assets...');
      return cache.addAll(ASSETS);
    })
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
      );
    })
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      // ဒေတာအသစ်ရှိရင် Network ကယူမယ်၊ မရှိရင် Cache ကပြမယ်
      return response || fetch(event.request);
    })
  );
}
                     );
