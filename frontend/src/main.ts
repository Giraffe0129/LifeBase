import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/global.css'

// ===== 注册 Service Worker（离线缓存）=====
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').then(
      (reg) => console.log('[SW] 注册成功'),
      (err) => console.warn('[SW] 注册失败:', err),
    )
  })
}

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
