const CACHE_NAME = 'empire-sprites-v1';

// Minimal precache on install — just the most critical battle assets.
// Everything else is cached on first request via cache-first fetch handler.
const PRECACHE = [
  '/assets/sprites/bases/path.webp',
  '/assets/sprites/bases/spawnpoint.webp',
  '/assets/sprites/images/texture.webp',
  '/assets/sprites/images/tctd.webp',
  '/assets/sprites/maps/map.webp',
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(PRECACHE))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('push', event => {
  const data = event.data ? event.data.json() : {};
  const title = data.title || 'Empire';
  const body = data.body || '';
  event.waitUntil(
    self.registration.showNotification(title, {
      body,
      icon: '/assets/sprites/ui/icon-192.png',
      tag: 'under-siege',
      renotify: true,
    })
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(clients.openWindow('/'));
});

self.addEventListener('fetch', event => {
  const url = event.request.url;
  if (!url.includes('/assets/sprites/')) return;

  event.respondWith(
    caches.open(CACHE_NAME).then(cache =>
      cache.match(event.request).then(cached => {
        if (cached) return cached;
        return fetch(event.request).then(response => {
          if (response.ok) cache.put(event.request, response.clone());
          return response;
        });
      })
    )
  );
});
