const CACHE_NAME = 'nextgen-books-v1';
const APP_SHELL = [
  '/ebook/',
  '/ebook/manifest.webmanifest',
  '/static/ebook/app.css',
  '/static/ebook/app.js',
  '/static/ebook/icon.svg',
  '/static/ebook/apple-touch-icon.png',
  '/static/ebook/icon-192.png',
  '/static/ebook/icon-512.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys.filter((key) => key.startsWith('nextgen-books-') && key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== 'GET' || url.origin !== self.location.origin) return;

  if (url.pathname === '/api/ebook/catalog') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.ok) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
          }
          return response;
        })
        .catch(async () => (await caches.match(request)) || Response.error())
    );
    return;
  }

  if (request.mode === 'navigate' && url.pathname.startsWith('/ebook')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.ok) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put('/ebook/', copy));
          }
          return response;
        })
        .catch(async () => (await caches.match('/ebook/')) || Response.error())
    );
    return;
  }

  if (url.pathname.startsWith('/static/ebook/')) {
    event.respondWith(
      caches.match(request).then((cached) => cached || fetch(request).then((response) => {
        if (response.ok) {
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
        }
        return response;
      }))
    );
  }
});
