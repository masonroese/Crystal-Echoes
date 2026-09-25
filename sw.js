// Keeps Crystal Echoes playable offline once it has been opened.
const CACHE='crystal-echoes-9d757a460e';
const FILES=["./", "index.html", "manifest.json", "fonts/Barlow-Medium.ttf", "fonts/Barlow-Regular.ttf", "fonts/Barlow-SemiBold.ttf", "fonts/ChakraPetch-Bold.ttf", "fonts/ChakraPetch-Medium.ttf", "fonts/ChakraPetch-SemiBold.ttf", "icons/apple-touch-icon.png", "icons/icon-192.png", "icons/icon-512.png", "icons/maskable-512.png"];
self.addEventListener('install',e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(FILES)));self.skipWaiting();});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))));self.clients.claim();});
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET')return;
  // network first for the page itself (so updates arrive), cache first for everything else
  if(e.request.mode==='navigate'){e.respondWith(fetch(e.request).then(r=>{const cp=r.clone();caches.open(CACHE).then(c=>c.put(e.request,cp));return r;}).catch(()=>caches.match(e.request).then(r=>r||caches.match('index.html'))));return;}
  e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request)));
});
