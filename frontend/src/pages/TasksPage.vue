<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAppStore } from '@/stores/useAppStore'
import { taskApi } from '@/api'
import type { TaskItem } from '@/api'
import { icons } from '@/utils/icons'

const store = useAppStore()
const showAddModal = ref(false)
const showSubtaskModal = ref(false)
const subtaskParent = ref<TaskItem | null>(null)
const newTask = ref({ title: '', description: '', priority: 0 })
const newSubtask = ref({ title: '', description: '' })
const submitting = ref(false)
const subtasksMap = ref<Record<number, TaskItem[]>>({})
const expandedParents = ref<Set<number>>(new Set())

// Drag for top-level tasks
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

// ② Filter parent tasks only for the main list
const parentTasks = computed(() =>
  store.pendingTasks.filter(t => !t.parent_id)
)

// CRUD
async function addTask() {
  if (!newTask.value.title.trim()) return
  submitting.value = true
  try {
    const result = await taskApi.create({
      title: newTask.value.title.trim(),
      description: newTask.value.description.trim(),
      priority: newTask.value.priority,
    })
    store.tasks.push(result)
    newTask.value = { title: '', description: '', priority: 0 }
    showAddModal.value = false
  } catch (e: any) { alert(e.message || '创建失败') }
  finally { submitting.value = false }
}

async function addSubtask(parentId: number) {
  if (!newSubtask.value.title.trim()) return
  submitting.value = true
  try {
    await taskApi.create({
      title: newSubtask.value.title.trim(),
      description: newSubtask.value.description.trim(),
      parent_id: parentId,
    })
    newSubtask.value = { title: '', description: '' }
    showSubtaskModal.value = false
    subtaskParent.value = null
    // Refresh subtasks for this parent
    await loadSubtasks(parentId)
    expandedParents.value.add(parentId)
  } catch (e: any) { alert(e.message || '创建失败') }
  finally { submitting.value = false }
}

async function loadSubtasks(parentId: number) {
  try {
    const subs = await taskApi.getSubtasks(parentId)
    subtasksMap.value[parentId] = subs
  } catch {}
}

function openSubtaskModal(task: TaskItem) {
  subtaskParent.value = task
  newSubtask.value = { title: '', description: '' }
  showSubtaskModal.value = true
  loadSubtasks(task.id)
}

function toggleExpand(taskId: number) {
  if (expandedParents.value.has(taskId)) {
    expandedParents.value.delete(taskId)
  } else {
    expandedParents.value.add(taskId)
    loadSubtasks(taskId)
  }
}

async function toggleTask(task: any) {
  try { const updated = await taskApi.update(task.id, { completed: !task.completed }); Object.assign(task, updated) }
  catch (e: any) { alert(e.message || '更新失败') }
}

async function deleteTask(id: number) {
  if (!confirm('确定删除此任务？')) return
  try { await taskApi.delete(id); store.tasks = store.tasks.filter(t => t.id !== id) }
  catch (e: any) { alert(e.message || '删除失败') }
}

function getPriorityLabel(p: number) { return ['普通', '重要', '紧急'][p] || '普通' }
function getPriorityIconSvg(p: number): string {
  if (p === 1) return icons.star
  if (p === 2) return icons.flame
  return ''
}
</script>

<template>
  <div>
    <div v-if="parentTasks.length === 0 && store.completedTasks.length === 0" class="empty-state">
      <div class="empty-icon" v-html="icons.tasks"></div>
      <p>还没有任务，点击下方按钮添加</p>
    </div>

    <!-- Parent Tasks with expand/subtask support -->
    <transition-group name="list" tag="div">
      <div v-for="(task, index) in parentTasks" :key="task.id">
        <!-- Parent Task Card -->
        <div class="claude-card" :class="{ dragging: dragIndex === index }"
          draggable="true" @dragstart="onDragStart(index)" @dragover="onDragOver($event, index)"
          @dragend="onDragEnd" @dragleave="dragOverIndex = null"
          style="display: flex; align-items: center; gap: 12px;">
          <span class="drag-handle" v-html="icons.grip" title="拖拽排序"></span>
          <div class="checkbox-claude" :class="{ checked: task.completed }" @click="toggleTask(task)">
            <span v-if="task.completed" v-html="icons.check"></span>
          </div>
          <div style="flex: 1; min-width: 0;">
            <div class="task-title">{{ task.title }}</div>
            <div v-if="task.description" class="task-desc">{{ task.description }}</div>
            <div style="display: flex; gap: 8px; margin-top: 6px; align-items: center; flex-wrap: wrap;">
              <span class="tag" :class="'tag-priority-' + task.priority">
                <span v-if="task.priority === 1" v-html="icons.star" style="width:12px;height:12px;display:inline-block;vertical-align:middle;"></span>
                <span v-if="task.priority === 2" v-html="icons.flame" style="width:12px;height:12px;display:inline-block;vertical-align:middle;"></span>
                {{ getPriorityLabel(task.priority) }}
              </span>
              <span class="text-sm text-secondary">{{ task.created_at ? new Date(task.created_at).toLocaleDateString() : '' }}</span>
              <!-- Subtask toggle -->
              <button class="btn btn-sm btn-ghost" @click.stop="toggleExpand(task.id)" title="子任务"
                style="display: inline-flex; align-items: center; gap: 4px; padding: 2px 10px;">
                <span v-html="icons.subTask" style="width:13px;height:13px;"></span>
                <span v-if="subtasksMap[task.id]?.length">({{ subtasksMap[task.id].length }})</span>
              </button>
            </div>
          </div>
          <div style="display: flex; gap: 4px; align-items: center;">
            <button class="btn btn-sm btn-ghost" @click.stop="openSubtaskModal(task)" title="添加子任务"
              v-html="icons.plusCircle" style="padding: 6px;"></button>
            <button class="btn btn-sm btn-ghost" @click="deleteTask(task.id)" title="删除"
              v-html="icons.trash" style="padding: 6px;"></button>
          </div>
        </div>

        <!-- Subtask List (expandable) -->
        <transition name="fade">
          <div v-if="expandedParents.has(task.id)" style="padding-left: 36px; margin-bottom: 8px;">
            <div v-if="!subtasksMap[task.id]?.length" class="text-sm text-secondary" style="padding: 8px 0;">暂无子任务</div>
            <div v-for="sub in subtasksMap[task.id] || []" :key="sub.id"
              class="claude-card" style="display: flex; align-items: center; gap: 10px; padding: 12px 16px; margin-bottom: 6px; border-radius: 20px;">
              <div class="checkbox-claude" :class="{ checked: sub.completed }" @click="toggleTask(sub)"
                style="width: 20px; height: 20px; font-size: 10px;">
                <span v-if="sub.completed" v-html="icons.check"></span>
              </div>
              <div style="flex: 1; min-width: 0;">
                <div class="task-title" style="font-size: 14px;">{{ sub.title }}</div>
                <div v-if="sub.description" class="task-desc" style="font-size: 12px;">{{ sub.description }}</div>
              </div>
              <div style="display: flex; gap: 4px;">
                <span class="tag" :class="'tag-priority-' + sub.priority" style="font-size: 10px;">
                  <span v-if="sub.priority === 1" v-html="icons.star" style="width:10px;height:10px;display:inline-block;"></span>
                  <span v-if="sub.priority === 2" v-html="icons.flame" style="width:10px;height:10px;display:inline-block;"></span>
                  {{ getPriorityLabel(sub.priority) }}
                </span>
                <button class="btn btn-sm btn-ghost" @click="deleteTask(sub.id)" v-html="icons.trash" style="padding: 4px;"></button>
              </div>
            </div>
            <button class="btn btn-sm btn-ghost" @click="openSubtaskModal(task)"
              style="display: flex; align-items: center; gap: 6px; padding: 6px 12px; margin-top: 4px;">
              <span v-html="icons.plus" style="width:14px;height:14px;"></span> 添加子任务
            </button>
          </div>
        </transition>
      </div>
    </transition-group>

    <!-- Completed -->
    <div v-if="store.completedTasks.length > 0" class="section-divider">已完成 ({{ store.completedTasks.length }})</div>
    <transition-group name="fade" tag="div">
      <div v-for="task in store.completedTasks" :key="task.id" class="claude-card" style="opacity: 0.5; display: flex; align-items: center; gap: 12px;">
        <div class="checkbox-claude checked" @click="toggleTask(task)" v-html="icons.check"></div>
        <div style="flex: 1"><div class="task-title completed">{{ task.title }}</div></div>
        <button class="btn btn-sm btn-ghost" @click="deleteTask(task.id)" v-html="icons.trash"></button>
      </div>
    </transition-group>

    <!-- FAB -->
    <div class="fab-area">
      <button class="btn btn-primary btn-round fab-btn" @click="showAddModal = true">
        <span v-html="icons.plus" style="width:20px;height:20px;"></span> 新任务
      </button>
    </div>

    <!-- Add Task Modal -->
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
            <textarea v-model="newTask.description" class="input-field" placeholder="任务描述..." rows="3"></textarea>
          </div>
          <div class="input-group">
            <label>优先级</label>
            <div class="priority-group">
              <button class="priority-btn" :class="{ active: newTask.priority === 0 }" @click="newTask.priority = 0">普通</button>
              <button class="priority-btn" :class="{ active: newTask.priority === 1 }" @click="newTask.priority = 1">
                <span v-html="icons.star" style="width:14px;height:14px;display:inline-block;vertical-align:middle;"></span> 重要
              </button>
              <button class="priority-btn" :class="{ active: newTask.priority === 2 }" @click="newTask.priority = 2">
                <span v-html="icons.flame" style="width:14px;height:14px;display:inline-block;vertical-align:middle;"></span> 紧急
              </button>
            </div>
          </div>
          <button class="btn btn-primary btn-block mt-16" :disabled="!newTask.title.trim() || submitting" @click="addTask">
            {{ submitting ? '创建中...' : '创建任务' }}
          </button>
        </div>
      </div>
    </transition>

    <!-- Add Subtask Modal -->
    <transition name="fade">
      <div v-if="showSubtaskModal && subtaskParent" class="modal-overlay" @click.self="showSubtaskModal = false">
        <div class="modal-window">
          <div class="modal-header">
            <h3 style="display: flex; align-items: center; gap: 8px;">
              <span v-html="icons.subTask" style="width:18px;height:18px;"></span>
              添加子任务
            </h3>
            <button class="btn btn-sm btn-ghost" @click="showSubtaskModal = false" v-html="icons.close"></button>
          </div>
          <div class="text-sm text-secondary mb-12" style="display: flex; align-items: center; gap: 6px; padding: 8px 14px; background: var(--muted); border-radius: var(--radius-pill);">
            父任务：<strong style="color: var(--foreground);">{{ subtaskParent.title }}</strong>
          </div>
          <div class="input-group">
            <label>子任务标题</label>
            <input v-model="newSubtask.title" class="input-field" placeholder="细化任务..." @keyup.enter="addSubtask(subtaskParent.id)" />
          </div>
          <div class="input-group">
            <label>描述（可选）</label>
            <textarea v-model="newSubtask.description" class="input-field" placeholder="补充说明..." rows="2"></textarea>
          </div>
          <button class="btn btn-primary btn-block mt-12" :disabled="!newSubtask.title.trim() || submitting" @click="addSubtask(subtaskParent.id)">
            {{ submitting ? '创建中...' : '创建子任务' }}
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>
