<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { connectWebSocket } from './api'
import { useAppStore } from './stores/useAppStore'
import { taskApi, travelPlanApi, noteApi } from './api'

const route = useRoute()
const router = useRouter()
const store = useAppStore()
const wsRef = ref<WebSocket | null>(null)

const navItems = [
  { path: '/tasks', label: '当前任务', icon: '📋' },
  { path: '/travel', label: '出行计划', icon: '🗺️' },
  { path: '/notes', label: '值得记录', icon: '📝' },
]

function isActive(path: string) {
  return route.path.startsWith(path)
}

onMounted(async () => {
  // 1. 先加载初始数据
  store.loading = true
  try {
    const [tasks, plans, notes] = await Promise.all([
      taskApi.list(),
      travelPlanApi.list(),
      noteApi.list(),
    ])
    store.tasks = tasks
    store.travelPlans = plans
    store.notes = notes
  } catch (e) {
    console.error('加载初始数据失败:', e)
  } finally {
    store.loading = false
  }

  // 2. 建立 WebSocket 实时连接
  wsRef.value = connectWebSocket((type, data) => {
    store.handleWSMessage(type, data)
  })
})

onUnmounted(() => {
  wsRef.value?.close()
})
</script>

<template>
  <div class="app-layout">
    <!-- 顶部导航 -->
    <header class="app-header">
      <h1>
        <template v-if="route.path === '/tasks'">📋 当前任务</template>
        <template v-else-if="route.path === '/travel'">🗺️ 出行计划</template>
        <template v-else-if="route.path === '/notes'">📝 值得记录</template>
      </h1>
      <span style="font-size: 12px; opacity: 0.8">
        实时{{ wsRef ? '●' : '○' }}
      </span>
    </header>

    <!-- 主内容区 -->
    <main class="app-main">
      <div v-if="store.loading" class="flex-center" style="padding: 48px; color: var(--color-text-secondary);">
        加载中...
      </div>
      <router-view v-else />
    </main>

    <!-- 底部导航 -->
    <nav class="bottom-nav">
      <button
        v-for="item in navItems"
        :key="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
        @click="router.push(item.path)"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span>{{ item.label }}</span>
      </button>
    </nav>
  </div>
</template>
