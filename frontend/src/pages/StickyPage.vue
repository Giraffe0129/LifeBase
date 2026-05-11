<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useAppStore } from '@/stores/useAppStore'
import { taskApi } from '@/api'

const store = useAppStore()
const topTasks = computed(() => store.pendingTasks.slice(0, 10))

onMounted(async () => {
  if (store.tasks.length === 0) {
    try { store.tasks = await taskApi.list() } catch {}
  }
})
</script>

<template>
  <div class="sticky-container">
    <div class="sticky-header">
      <div class="sticky-logo">M</div>
      <span class="sticky-title">当前任务</span>
      <span class="sticky-count">{{ store.pendingTasks.length }}</span>
    </div>
    <div class="sticky-body">
      <div v-if="topTasks.length === 0" class="sticky-empty">没有待办任务 ✨</div>
      <div v-for="task in topTasks" :key="task.id" class="sticky-item">
        <span class="sticky-check" :style="{ background: task.completed ? '#5D7052' : 'transparent' }"></span>
        <span class="sticky-text">{{ task.title }}</span>
        <span v-if="task.priority === 2" class="sticky-urgent">!!!</span>
      </div>
      <div v-if="store.pendingTasks.length > 10" class="sticky-more">+ {{ store.pendingTasks.length - 10 }} 更多...</div>
    </div>
    <div class="sticky-footer">Ctrl+Shift+S 切换</div>
  </div>
</template>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: 'Nunito', -apple-system, sans-serif;
  background: #1A1A14;
  color: #E8E4D8;
  overflow: hidden;
  user-select: none;
  -webkit-app-region: drag;
}
.sticky-container { height: 100vh; display: flex; flex-direction: column; padding: 14px; }
.sticky-header { display: flex; align-items: center; gap: 8px; padding-bottom: 10px; border-bottom: 1px solid #3D3D35; -webkit-app-region: drag; }
.sticky-logo { width: 28px; height: 28px; background: #5D7052; border-radius: 40% 60% 30% 70% / 50% 30% 70% 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 800; color: #F3F4F1; font-family: 'Fraunces', serif; }
.sticky-title { font-size: 13px; font-weight: 700; flex: 1; font-family: 'Fraunces', serif; }
.sticky-count { font-size: 11px; background: rgba(93,112,82,0.15); color: #7D9072; padding: 1px 10px; border-radius: 10px; font-weight: 700; }
.sticky-body { flex: 1; overflow-y: auto; padding: 8px 0; -webkit-app-region: no-drag; }
.sticky-empty { text-align: center; padding: 40px 0; color: #78786C; font-size: 13px; }
.sticky-item { display: flex; align-items: center; gap: 8px; padding: 7px 4px; font-size: 13px; border-bottom: 1px solid #2A2A24; }
.sticky-check { width: 10px; height: 10px; min-width: 10px; border: 1.5px solid #5D7052; border-radius: 30% 70% 50% 50% / 50% 40% 60% 50%; }
.sticky-text { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sticky-urgent { color: #A85448; font-size: 11px; font-weight: 700; }
.sticky-more { text-align: center; font-size: 11px; color: #78786C; padding: 8px; }
.sticky-footer { text-align: center; font-size: 10px; color: #3D3D35; padding-top: 8px; border-top: 1px solid #2A2A24; -webkit-app-region: drag; }
</style>
