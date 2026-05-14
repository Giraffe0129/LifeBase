<script setup lang="ts">
import { onMounted, onUnmounted, ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { connectWebSocket } from './api'
import { useAppStore } from './stores/useAppStore'
import { useAuthStore } from './stores/useAuthStore'
import { taskApi, travelPlanApi, noteApi, settingsApi } from './api'
import { isOnline } from './db/localDB'
import { onNetworkChange, loadFromLocalCache, flushSyncQueue, fullSync } from './db/sync'
import { icons } from './utils/icons'

const route = useRoute()
const router = useRouter()
const store = useAppStore()
const auth = useAuthStore()
const wsRef = ref<WebSocket | null>(null)

// Theme
const isDark = ref(false)
const autoTheme = ref(true)

function getMinutesSinceMidnight(): number {
  const now = new Date()
  return now.getHours() * 60 + now.getMinutes()
}
function computeIsDark(): boolean {
  const now = getMinutesSinceMidnight()
  return now < 360 || now >= 1080
}

function applyTheme(dark: boolean) {
  isDark.value = dark
  if (dark) document.documentElement.classList.add('dark-mode')
  else document.documentElement.classList.remove('dark-mode')
}

function toggleTheme() {
  autoTheme.value = false
  applyTheme(!isDark.value)
  localStorage.setItem('theme_manual', isDark.value ? 'dark' : 'light')
}

let themeTimer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  const manual = localStorage.getItem('theme_manual')
  if (manual) {
    autoTheme.value = false
    applyTheme(manual === 'dark')
  } else {
    autoTheme.value = true
    applyTheme(computeIsDark())
    themeTimer = setInterval(() => { if (autoTheme.value) applyTheme(computeIsDark()) }, 60000)
  }
})

onUnmounted(() => { if (themeTimer) clearInterval(themeTimer) })

/** 从后端加载数据（登录成功后也会调用） */
async function loadAppData() {
  if (!auth.isLoggedIn) return
  store.loading = true
  try {
    if (isOnline()) {
      const [tasks, plans, notes, categories, settings] = await Promise.all([
        taskApi.list(), travelPlanApi.list(), noteApi.list(),
        store.fetchCategories(), settingsApi.get(),
      ])
      store.tasks = tasks; store.travelPlans = plans; store.notes = notes; store.settings = settings
    } else { await loadFromLocalCache() }
  } catch { await loadFromLocalCache() }
  finally { store.loading = false }

  if (isOnline()) {
    wsRef.value?.close()
    wsRef.value = connectWebSocket((type, data) => store.handleWSMessage(type, data))
  }
}

// 初始加载：恢复 session 后加载数据
onMounted(async () => {
  const restored = await auth.restoreSession()
  if (restored) {
    await loadAppData()
  }

  // 监听登录/退出事件
  watch(() => auth.token, async (newToken, oldToken) => {
    if (newToken && !oldToken) {
      // 刚刚登录 → 加载数据
      await loadAppData()
    } else if (!newToken) {
      // 退出登录 → 清空数据
      store.tasks = []
      store.travelPlans = []
      store.notes = []
      store.settings = { weather_enabled: true, extras: {} }
      wsRef.value?.close()
      wsRef.value = null
    }
  })

  onNetworkChange(() => {
    if (isOnline()) {
      flushSyncQueue().then(() => fullSync())
      wsRef.value?.close()
      wsRef.value = connectWebSocket((type, data) => store.handleWSMessage(type, data))
    }
  })
})

// Navigation
const pageTitle = computed(() => {
  const titles: Record<string, string> = { '/tasks': '当前任务', '/travel': '出行计划', '/notes': '值得记录', '/settings': '设置' }
  return titles[route.path] || 'My App'
})

const sidebarItems = [
  { path: '/tasks', label: '当前任务', icon: icons.tasks },
  { path: '/travel', label: '出行计划', icon: icons.travel },
  { path: '/notes', label: '值得记录', icon: icons.notes },
  { path: '/settings', label: '设置', icon: icons.settings },
]

function isActive(path: string) { return route.path === path }
function navigateTo(path: string) { router.push(path) }

// Swipe
const swipeContainer = ref<HTMLElement | null>(null)
let touchStartX = 0, touchStartY = 0, swiping = false

function onTouchStart(e: TouchEvent) { touchStartX = e.touches[0].clientX; touchStartY = e.touches[0].clientY; swiping = true }
function onTouchEnd(e: TouchEvent) {
  if (!swiping) return; swiping = false
  const dx = e.changedTouches[0].clientX - touchStartX
  const dy = e.changedTouches[0].clientY - touchStartY
  if (Math.abs(dx) < 50 || Math.abs(dx) < Math.abs(dy) * 1.5) return
  const paths = ['/tasks', '/travel', '/notes']
  const idx = paths.indexOf(route.path)
  if (idx === -1) return
  if (dx < 0 && idx < paths.length - 1) router.push(paths[idx + 1])
  else if (dx > 0 && idx > 0) router.push(paths[idx - 1])
}

const timeStr = computed(() => new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }))
const timeGreeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 9) return '早上好'
  if (h < 12) return '上午好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})
const pendingCount = computed(() => store.pendingTasks.length)
</script>

<template>
  <template v-if="route.path === '/login' || route.path === '/sticky'">
    <router-view />
  </template>
  <template v-else>
    <div class="claude-layout">
      <!-- Sidebar Desktop -->
      <aside class="claude-sidebar">
        <div class="sidebar-header">
          <div class="sidebar-logo" v-html="icons.notes"></div>
          <span class="sidebar-title">My App</span>
        </div>
        <nav class="sidebar-nav">
          <button v-for="item in sidebarItems" :key="item.path"
            class="sidebar-nav-item" :class="{ active: isActive(item.path) }"
            @click="navigateTo(item.path)">
            <span class="nav-icon" v-html="item.icon"></span>
            <span style="flex:1">{{ item.label }}</span>
            <span v-if="item.path === '/tasks' && pendingCount > 0"
              class="tag" style="background: rgba(255,255,255,0.2); color: var(--primary-foreground); font-size: 10px; padding: 1px 8px;">
              {{ pendingCount > 99 ? '99+' : pendingCount }}
            </span>
          </button>
        </nav>
        <div class="sidebar-footer">
          <span v-html="icons.dot" style="color: var(--success); width:8px;height:8px;"></span>
          <span class="text-sm" style="color: var(--muted-foreground); font-weight: 600;">
            {{ isOnline() ? '在线' : '离线' }}
          </span>
          <span v-if="auth.user" style="margin-left: auto; font-size: 12px; color: var(--muted-foreground); max-width: 100px; overflow: hidden; text-overflow: ellipsis;">
            {{ auth.user.username }}
          </span>
        </div>
      </aside>

      <!-- Main -->
      <div class="claude-main">
        <header class="claude-topbar">
          <h2>{{ pageTitle }}</h2>
          <div class="topbar-actions">
            <span class="status-badge">{{ timeGreeting }} {{ timeStr }}</span>
            <button class="theme-toggle" @click="toggleTheme" :title="isDark ? '日间模式' : '夜间模式'" v-html="isDark ? icons.sun : icons.moon"></button>
            <span class="status-badge">
              <span v-html="icons.dot"
                :style="{ color: wsRef ? 'var(--primary)' : 'var(--muted-foreground)', width:8, height:8 }"></span>
              {{ wsRef ? '实时' : (isOnline() ? '在线' : '离线') }}
            </span>
          </div>
        </header>

        <div class="claude-content" ref="swipeContainer" @touchstart="onTouchStart" @touchend="onTouchEnd">
          <div v-if="store.loading" class="flex-center" style="padding: 100px; flex-direction: column; gap: 16px;">
            <div style="width: 40px; height: 40px; border: 3px solid var(--border); border-top-color: var(--primary); border-radius: 40% 60% 30% 70% / 50% 30% 70% 50%; animation: spin 0.9s linear infinite;"></div>
            <span style="font-family: var(--font-heading); font-size: 16px; color: var(--muted-foreground);">加载中...</span>
          </div>
          <router-view v-slot="{ Component }" v-else>
            <transition name="page" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </div>
      </div>

      <!-- Mobile Bottom Nav -->
      <nav class="mobile-bottom-nav">
        <button v-for="item in sidebarItems" :key="item.path"
          class="mobile-nav-item" :class="{ active: isActive(item.path) }"
          @click="navigateTo(item.path)">
          <span class="nav-icon" v-html="item.icon"></span>
          <span>{{ item.label }}</span>
        </button>
      </nav>
    </div>
  </template>
</template>

<style>
@keyframes spin { to { transform: rotate(360deg); } }
</style>
