<script setup lang="ts">
import { ref } from 'vue'
import { useAppStore } from '@/stores/useAppStore'
import { taskApi } from '@/api'

const store = useAppStore()

// 新增任务弹窗
const showAddModal = ref(false)
const newTask = ref({ title: '', description: '', priority: 0 })
const submitting = ref(false)

async function addTask() {
  if (!newTask.value.title.trim()) return
  submitting.value = true
  try {
    await taskApi.create({
      title: newTask.value.title.trim(),
      description: newTask.value.description.trim(),
      priority: newTask.value.priority,
    })
    newTask.value = { title: '', description: '', priority: 0 }
    showAddModal.value = false
  } catch (e: any) {
    alert('创建失败: ' + e.message)
  } finally {
    submitting.value = false
  }
}

async function toggleTask(task: any) {
  try {
    await taskApi.update(task.id, { completed: !task.completed })
  } catch (e: any) {
    alert('更新失败: ' + e.message)
  }
}

async function deleteTask(id: number) {
  if (!confirm('确定删除此任务？')) return
  try {
    await taskApi.delete(id)
  } catch (e: any) {
    alert('删除失败: ' + e.message)
  }
}

function getPriorityLabel(p: number) {
  return ['普通', '重要', '紧急'][p] || '普通'
}
</script>

<template>
  <div>
    <!-- 待办任务 -->
    <div v-if="store.pendingTasks.length === 0" class="empty-state">
      <div class="empty-icon">📋</div>
      <p>还没有任务，点击下方按钮添加</p>
    </div>

    <div v-for="task in store.pendingTasks" :key="task.id" class="card">
      <div style="display: flex; align-items: flex-start; gap: 12px">
        <div class="checkbox-wrapper" @click="toggleTask(task)">
          <div class="checkbox-custom" :class="{ checked: task.completed }">
            {{ task.completed ? '✓' : '' }}
          </div>
        </div>
        <div class="task-content">
          <div class="task-title">{{ task.title }}</div>
          <div v-if="task.description" class="task-desc">{{ task.description }}</div>
          <div style="display: flex; gap: 6px; margin-top: 6px; align-items: center">
            <span class="tag" :class="'tag-priority-' + task.priority">
              {{ getPriorityLabel(task.priority) }}
            </span>
            <span class="text-sm text-secondary">
              {{ task.created_at ? new Date(task.created_at).toLocaleDateString() : '' }}
            </span>
          </div>
        </div>
        <button class="btn btn-sm btn-danger" @click="deleteTask(task.id)" style="flex-shrink: 0">删除</button>
      </div>
    </div>

    <!-- 已完成任务 -->
    <details v-if="store.completedTasks.length > 0" style="margin-top: 16px">
      <summary style="font-size: 14px; color: var(--color-text-secondary); cursor: pointer; padding: 8px 0">
        已完成 ({{ store.completedTasks.length }})
      </summary>
      <div v-for="task in store.completedTasks" :key="task.id" class="card" style="opacity: 0.7">
        <div style="display: flex; align-items: flex-start; gap: 12px">
          <div class="checkbox-wrapper" @click="toggleTask(task)">
            <div class="checkbox-custom checked">✓</div>
          </div>
          <div class="task-content">
            <div class="task-title completed">{{ task.title }}</div>
            <div class="text-sm text-secondary">
              {{ task.created_at ? new Date(task.created_at).toLocaleDateString() : '' }}
            </div>
          </div>
          <button class="btn btn-sm btn-danger" @click="deleteTask(task.id)" style="flex-shrink: 0">删除</button>
        </div>
      </div>
    </details>

    <!-- 添加按钮 -->
    <div style="position: fixed; bottom: 80px; left: 50%; transform: translateX(-50%); z-index: 50; max-width: 480px; width: calc(100% - 32px)">
      <button class="btn btn-primary btn-block" @click="showAddModal = true" style="padding: 14px; border-radius: var(--radius); box-shadow: var(--shadow-lg)">
        + 添加新任务
      </button>
    </div>

    <!-- 新增任务弹窗 -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>新建任务</h3>
          <button class="modal-close" @click="showAddModal = false">✕</button>
        </div>

        <div class="input-group">
          <label>任务标题 *</label>
          <input v-model="newTask.title" class="input-field" placeholder="要做什么？" @keyup.enter="addTask" />
        </div>

        <div class="input-group">
          <label>任务描述</label>
          <textarea v-model="newTask.description" class="input-field" placeholder="补充说明..." rows="3"></textarea>
        </div>

        <div class="priority-selector">
          <label style="width: 100%; font-size: 13px; font-weight: 500; color: var(--color-text-secondary); margin-bottom: 4px;">优先级</label>
          <div style="display: flex; gap: 8px; width: 100%;">
            <button class="priority-btn" :class="{ active: newTask.priority === 0 }" @click="newTask.priority = 0">普通</button>
            <button class="priority-btn" :class="{ active: newTask.priority === 1 }" @click="newTask.priority = 1">重要</button>
            <button class="priority-btn" :class="{ active: newTask.priority === 2 }" @click="newTask.priority = 2">紧急</button>
          </div>
        </div>

        <button class="btn btn-primary btn-block mt-12" :disabled="!newTask.title.trim() || submitting" @click="addTask">
          {{ submitting ? '创建中...' : '创建任务' }}
        </button>
      </div>
    </div>
  </div>
</template>
