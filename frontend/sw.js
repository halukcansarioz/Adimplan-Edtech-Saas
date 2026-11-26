const CACHE_NAME = 'adimplan-pwa-v13';
const PRECACHE_URLS = [
  './index.html',
  './login.html',
  './app.html',
  './admin.html',
  './manifest.json',
  './super-admin.html',
  './404.html',
  './coach-modules.js?v=1',
  './favicon.svg'
];

// "cleanUrls" yayında /app.html -> /app yönlendirir. Yönlendirilmiş bir yanıt
// sayfa gezinmesine servis edilemediği için önbelleğe temiz bir kopyası yazılır.
async function toCacheable(response) {
  if (!response.redirected) return response;
  return new Response(await response.blob(), {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers
  });
}

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) =>
      Promise.all(
        PRECACHE_URLS.map(async (path) => {
          const response = await fetch(path, { cache: 'reload' });
          if (!response.ok) throw new Error(`Precache failed: ${path}`);
          await cache.put(path, await toCacheable(response));
        })
      )
    )
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

async function offlineFallback(request) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request, { ignoreSearch: true });
  if (cached) return cached;
  // HTML yedeği yalnızca sayfa gezinmelerine döner; script/görsel isteklerine değil.
  if (request.mode !== 'navigate') return Response.error();
  const path = new URL(request.url).pathname.replace(/\/$/, '');
  const page = path.split('/').pop();
  if (page && !page.includes('.')) {
    const clean = await cache.match(`./${page}.html`);
    if (clean) return clean;
  }
  return (await cache.match('./index.html')) || Response.error();
}

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;
  if (url.pathname.startsWith('/api/')) return;

  event.respondWith(
    fetch(event.request)
      .then(async (networkResponse) => {
        if (networkResponse && networkResponse.status === 200) {
          const copy = await toCacheable(networkResponse.clone());
          const cache = await caches.open(CACHE_NAME);
          await cache.put(event.request, copy);
        }
        return networkResponse;
      })
      .catch(() => offlineFallback(event.request))
  );
});
