<script setup lang="ts">
import { ref } from 'vue'
import { useAppStore } from '@/stores/useAppStore'
import { taskApi } from '@/api'
import { icons } from '@/utils/icons'

const store = useAppStore()
const showAddModal = ref(false)
const newTask = ref({ title: '', description: '', priority: 0 })
const submitting = ref(false)

// Drag
const dragIndex = ref<number | null>(null)
const dragOverIndex = ref<number | null>(null)

function onDragStart(index: number) { dragIndex.value = index }
function onDragOver(e: DragEvent, index: number) { e.preventDefault(); dragOverIndex.value = index }
function onDragEnd() {
  if (dragIndex.value === null || dragOverIndex.value === null) return
  if (dragIndex.value === dragOverIndex.value) { resetDrag(); return }
  const items = [...store.pendingTasks]
  const [moved] = items.splice(dragIndex.value, 1)
  items.splice(dragOverIndex.value, 0, moved)
  const newOrders = items.map((item, idx) => ({ id: item.id, sort_order: idx }))
  store.tasks = [...items, ...store.completedTasks]
  taskApi.reorder(newOrders).catch(() => {})
  resetDrag()
}
function resetDrag() { dragIndex.value = null; dragOverIndex.value = null }

// CRUD
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
  } catch (e: any) { alert(e.message || '创建失败') }
  finally { submitting.value = false }
}

async function toggleTask(task: any) {
  try { await taskApi.update(task.id, { completed: !task.completed }) }
  catch (e: any) { alert(e.message || '更新失败') }
}

async function deleteTask(id: number) {
  if (!confirm('确定删除此任务？')) return
  try { await taskApi.delete(id) }
  catch (e: any) { alert(e.message || '删除失败') }
}

function getPriorityLabel(p: number) { return ['普通', '重要', '紧急'][p] || '普通' }

const priorityIcons = ['', icons.star, '']
</script>

<template>
  <div>
    <div v-if="store.pendingTasks.length === 0" class="empty-state">
      <div class="empty-icon" v-html="icons.tasks"></div>
      <p>还没有任务，点击下方按钮添加</p>
    </div>

    <transition-group name="list" tag="div">
      <div v-for="(task, index) in store.pendingTasks" :key="task.id"
        class="claude-card" :class="{ dragging: dragIndex === index }"
        draggable="true" @dragstart="onDragStart(index)" @dragover="onDragOver($event, index)"
        @dragend="onDragEnd" @dragleave="dragOverIndex = null"
        style="display: flex; align-items: center; gap: 12px;">
        <span class="drag-handle" v-html="icons.grip" title="拖拽排序"></span>
        <div class="checkbox-claude" :class="{ checked: task.completed }" @click="toggleTask(task)">
          <span v-if="task.completed" v-html="icons.check"></span>
        </div>
        <div style="flex: 1; min-width: 0;">
          <div class="task-title" :class="{ completed: task.completed }">{{ task.title }}</div>
          <div v-if="task.description" class="task-desc">{{ task.description }}</div>
          <div style="display: flex; gap: 8px; margin-top: 6px; align-items: center; flex-wrap: wrap;">
            <span class="tag" :class="'tag-priority-' + task.priority">
              <span v-if="task.priority === 1" v-html="icons.star" style="width:12px;height:12px;"></span>
              {{ getPriorityLabel(task.priority) }}
            </span>
            <span class="text-sm text-secondary">{{ task.created_at ? new Date(task.created_at).toLocaleDateString() : '' }}</span>
          </div>
        </div>
        <button class="btn btn-sm btn-ghost" @click="deleteTask(task.id)" title="删除" v-html="icons.trash"></button>
      </div>
    </transition-group>

    <div v-if="store.completedTasks.length > 0" class="section-divider">已完成 ({{ store.completedTasks.length }})</div>

    <transition-group name="fade" tag="div">
      <div v-for="task in store.completedTasks" :key="task.id" class="claude-card" style="opacity: 0.5; display: flex; align-items: center; gap: 12px;">
        <div class="checkbox-claude checked" @click="toggleTask(task)" v-html="icons.check"></div>
        <div style="flex: 1"><div class="task-title completed">{{ task.title }}</div></div>
        <button class="btn btn-sm btn-ghost" @click="deleteTask(task.id)" v-html="icons.trash"></button>
      </div>
    </transition-group>

    <div class="fab-area">
      <button class="btn btn-primary btn-round fab-btn" @click="showAddModal = true">
        <span v-html="icons.plus" style="width:20px;height:20px;"></span> 新任务
      </button>
    </div>

    <transition name="fade">
      <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
        <div class="modal-window">
          <div class="modal-header">
            <h3>新建任务</h3>
            <button class="btn btn-sm btn-ghost" @click="showAddModal = false" v-html="icons.close"></button>
          </div>
          <div class="input-group">
            <label>标题</label>
            <input v-model="newTask.title" class="input-field" placeholder="要做什么？" @keyup.enter="addTask" />
          </div>
          <div class="input-group">
            <label>描述</label>
            <textarea v-model="newTask.description" class="input-field" placeholder="补充说明..." rows="3"></textarea>
          </div>
          <div class="input-group">
            <label>优先级</label>
            <div class="priority-group">
              <button class="priority-btn" :class="{ active: newTask.priority === 0 }" @click="newTask.priority = 0">普通</button>
              <button class="priority-btn" :class="{ active: newTask.priority === 1 }" @click="newTask.priority = 1">
                <span v-html="icons.star" style="width:14px;height:14px;display:inline-block;vertical-align:middle;"></span> 重要
              </button>
              <button class="priority-btn" :class="{ active: newTask.priority === 2 }" @click="newTask.priority = 2">紧急</button>
            </div>
          </div>
          <button class="btn btn-primary btn-block mt-16" :disabled="!newTask.title.trim() || submitting" @click="addTask">
            {{ submitting ? '创建中...' : '创建任务' }}
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>
