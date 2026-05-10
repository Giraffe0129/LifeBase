import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { TaskItem, TravelPlanItem, NoteItem } from '@/api'

/**
 * 全局状态管理 - 管理三个功能模块的数据，
 * WebSocket 推送的数据会实时更新到这些状态中。
 */
export const useAppStore = defineStore('app', () => {
  // ===== 状态 =====
  const tasks = ref<TaskItem[]>([])
  const travelPlans = ref<TravelPlanItem[]>([])
  const notes = ref<NoteItem[]>([])
  const loading = ref(false)

  // ===== 计算属性 =====
  const pendingTasks = computed(() => tasks.value.filter(t => !t.completed))
  const completedTasks = computed(() => tasks.value.filter(t => t.completed))
  const upcomingPlans = computed(() =>
    travelPlans.value
      .filter(p => !p.completed)
      .sort((a, b) => (a.plan_date || '').localeCompare(b.plan_date || ''))
  )
  const favoriteNotes = computed(() => notes.value.filter(n => n.is_favorite))

  // ===== WebSocket 消息处理 =====
  function handleWSMessage(type: string, data: any) {
    // 任务
    if (type === 'sync_task') {
      const idx = tasks.value.findIndex(t => t.id === data.id)
      if (idx >= 0) {
        tasks.value[idx] = data
      } else {
        tasks.value.unshift(data)
      }
    } else if (type === 'delete_task') {
      tasks.value = tasks.value.filter(t => t.id !== data.id)
    }
    // 出行计划
    else if (type === 'sync_travel_plan') {
      const idx = travelPlans.value.findIndex(p => p.id === data.id)
      if (idx >= 0) {
        travelPlans.value[idx] = data
      } else {
        travelPlans.value.unshift(data)
      }
    } else if (type === 'delete_travel_plan') {
      travelPlans.value = travelPlans.value.filter(p => p.id !== data.id)
    }
    // 笔记
    else if (type === 'sync_note') {
      const idx = notes.value.findIndex(n => n.id === data.id)
      if (idx >= 0) {
        notes.value[idx] = data
      } else {
        notes.value.unshift(data)
      }
    } else if (type === 'delete_note') {
      notes.value = notes.value.filter(n => n.id !== data.id)
    }
  }

  return {
    tasks, travelPlans, notes, loading,
    pendingTasks, completedTasks, upcomingPlans, favoriteNotes,
    handleWSMessage,
  }
})
