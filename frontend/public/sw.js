/**
 * Service Worker - 离线缓存
 * 使用 Cache First 策略：优先从缓存加载，同时后台更新。
 * 离线时保证静态资源和 API 数据的可用性。
 */
const CACHE_NAME = 'my-awesome-app-v2'

// 安装时预缓存的静态资源
const PRECACHE_URLS = [
  '/',
  '/index.html',
  '/manifest.webmanifest',
]

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRECACHE_URLS)
    })
  )
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((names) => {
      return Promise.all(
        names
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      )
    })
  )
  self.clients.claim()
})

// 网络优先，回退到缓存
self.addEventListener('fetch', (event) => {
  // API 请求使用 Network First 策略
  if (event.request.url.includes('/api/') || event.request.url.includes('/ws')) {
    event.respondWith(networkFirst(event.request))
    return
  }

  // 静态资源使用 Cache First 策略
  event.respondWith(cacheFirst(event.request))
})

async function cacheFirst(request) {
  const cached = await caches.match(request)
  if (cached) return cached

  try {
    const response = await fetch(request)
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME)
      cache.put(request, response.clone())
    }
    return response
  } catch (e) {
    return new Response('离线模式', { status: 503 })
  }
}

async function networkFirst(request) {
  try {
    const response = await fetch(request)
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME)
      cache.put(request, response.clone())
    }
    return response
  } catch (e) {
    const cached = await caches.match(request)
    if (cached) return cached
    return new Response(JSON.stringify({ error: '离线模式' }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' },
    })
  }
}
