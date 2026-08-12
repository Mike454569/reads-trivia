// Service worker: makes the app a real installable PWA and lets it load when
// offline. Deliberately network-first (not cache-first) — this app's content
// files (data/*.js) get updated fairly often, and a cache-first strategy would
// leave installed users stuck on stale trivia/rosters/grid data indefinitely
// with no way to know a refresh happened. Network-first means anyone online
// always gets the latest files; the cache only kicks in when there's no
// connection, which is exactly the scenario the README already documents
// (solo play keeps working offline, only the shared leaderboard needs a
// connection). Bump CACHE_VERSION when shipping a change worth force-clearing
// old installs' caches for.
var CACHE_VERSION = 'reads-v27';
var CORE_ASSETS = [
  './', './index.html', './styles.css', './app.js', './reads-config.js', './engine-game-ui.js', './six-degrees-ui.js', './creator-ui.js', './sound.js', './firebase-sync.js', './manifest.json',
  './data/quiz.js', './data/quiz-engine-draft-production.js',
  './data/quiz-engine-game-result-production.js', './data/quiz-engine-cfb-game-result-production.js',
  './data/grid.js', './data/blitz.js', './data/silhouette.js',
  './data/legends.js', './data/legends-meta.js', './data/cfb.js', './data/cfb-speed.js',
  './data/cfb-blitz.js', './data/cfb-grid.js', './data/cfb-legends.js', './data/cfb-legends-meta.js',
  './data/higher-lower-extra.js', './data/xso.js',
  './assets/brand/reads-logo.jpg', './assets/brand/reads-logo-square.jpg',
  './assets/brand/icon-192.png', './assets/brand/icon-512.png',
  './assets/brand/icon-192-maskable.png', './assets/brand/icon-512-maskable.png',
  './assets/brand/apple-touch-icon.png', './assets/brand/favicon-32.png'
];

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(CACHE_VERSION).then(function (cache) {
      // addAll() is all-or-nothing — one bad/missing URL fails the whole
      // install and the SW never activates. Each asset is added separately
      // instead so one hiccup (e.g. a file renamed but this list not yet
      // updated) doesn't take the entire offline shell down with it.
      return Promise.all(CORE_ASSETS.map(function (url) {
        return cache.add(url).catch(function (err) { console.warn('SW: failed to cache', url, err); });
      }));
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.filter(function (k) { return k !== CACHE_VERSION; }).map(function (k) { return caches.delete(k); }));
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', function (event) {
  if (event.request.method !== 'GET') return;
  // Firebase/Firestore traffic (leaderboard sync) — never intercept, always hit the network.
  if (event.request.url.indexOf('firestore.googleapis.com') !== -1 || event.request.url.indexOf('gstatic.com') !== -1) return;
  // v1.2 Reads Engine Gateway public gameplay pilot (app.js's
  // ENGINE_GATEWAY_BASE_URL + /v1/public/*) — real bug found by actually
  // testing the Gateway-unavailable fallback path in a browser, not
  // assumed: without this exclusion, a failed GET /v1/public/game request
  // fell into the catch() below and silently resolved with the cached
  // ./index.html HTML page instead of a real network error, so
  // enginePilotFetchJson()'s res.json() call failed on the HTML with a
  // confusing "Unexpected token '<'" instead of a clean, real "can't
  // reach the engine" error. A live game/answer response must also never
  // be served from a stale cache on a LATER request — every reason
  // Part 21 warned about applies here. Excluded by path, not origin, so
  // this doesn't accidentally widen to unrelated cross-origin requests.
  if (event.request.url.indexOf('/v1/public/') !== -1) return;

  event.respondWith(
    fetch(event.request)
      .then(function (response) {
        var copy = response.clone();
        caches.open(CACHE_VERSION).then(function (cache) { cache.put(event.request, copy); });
        return response;
      })
      .catch(function () {
        return caches.match(event.request).then(function (cached) { return cached || caches.match('./index.html'); });
      })
  );
});

// Push notifications — the actual send happens server-side (see
// netlify/functions/send-daily-push.js), this is just the client half that
// turns an incoming push message into a real system notification. Fires
// even if the app isn't open, which is the entire point of push over a
// locally-scheduled notification.
self.addEventListener('push', function (event) {
  var data = {};
  try { data = event.data ? event.data.json() : {}; } catch (e) {}
  var title = data.title || 'Reads';
  var options = {
    body: data.body || '',
    icon: './assets/brand/icon-192.png',
    badge: './assets/brand/icon-192.png',
    data: { url: data.url || './' }
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

// Tapping the notification focuses an already-open Reads tab if one exists,
// instead of always opening a new one — same "don't spawn duplicate tabs"
// courtesy most real apps' notifications give you.
self.addEventListener('notificationclick', function (event) {
  event.notification.close();
  var url = (event.notification.data && event.notification.data.url) || './';
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (windowClients) {
      for (var i = 0; i < windowClients.length; i++) {
        if ('focus' in windowClients[i]) return windowClients[i].focus();
      }
      if (self.clients.openWindow) return self.clients.openWindow(url);
    })
  );
});
