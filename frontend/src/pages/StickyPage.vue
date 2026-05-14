<script setup lang="ts">
/**
 * 便签模式 v4 - Lucide 图标 + 子任务展开 + 增删改
 */
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { useAppStore } from '@/stores/useAppStore'
import { taskApi, travelPlanApi, noteApi, categoryApi } from '@/api'
import { icons } from '@/utils/icons'

const store = useAppStore()

type StickyTab = 'tasks' | 'travel' | 'notes'
const activeTab = ref<StickyTab>('tasks')
const tabLabels: Record<StickyTab, string> = { tasks: '当前任务', travel: '出行计划', notes: '值得记录' }

// ② 昼夜模式（持久化到 localStorage）
const STORAGE_KEY = 'sticky_theme'
const isDark = ref(localStorage.getItem(STORAGE_KEY) !== 'light')

// 数据
const topTasks = computed(() => store.pendingTasks.filter(t => !t.parent_id).slice(0, 15))
const topPlans = computed(() => store.travelPlans.filter(p => !p.completed).slice(0, 10))
const topNotes = computed(() => store.notes.slice(0, 10))

// ③ 改用 Record<number, boolean> 保证响应式
const expandedSubtasks = ref<Record<number, boolean>>({})
const expandedTaskDetails = ref<Record<number, boolean>>({})
const expandedNoteDetails = ref<Record<number, boolean>>({})
const subtasksMap = ref<Record<number, any[]>>({})

// ④ 添加/删除状态
const showAddInput = ref(false)
const addText = ref('')
const selectedCatId = ref<number | null>(null)
const catOptions = ref<{id: number; name: string; icon: string}[]>([])

onMounted(async () => {
  try {
    if (store.tasks.length === 0) store.tasks = await taskApi.list()
    if (store.travelPlans.length === 0) store.travelPlans = await travelPlanApi.list()
    if (store.notes.length === 0) store.notes = await noteApi.list()
  } catch {}
  // 加载分类选项
  try { const cats = await categoryApi.list(); catOptions.value = cats } catch {}
})

// ④ 打勾
async function toggleTask(task: any) { try { const u = await taskApi.update(task.id, { completed: !task.completed }); Object.assign(task, u) } catch {} }
async function togglePlan(plan: any) { try { const u = await travelPlanApi.update(plan.id, { completed: !plan.completed }); Object.assign(plan, u) } catch {} }

// ③ 子任务展开
async function toggleSubtasks(taskId: number) {
  if (expandedSubtasks.value[taskId]) { expandedSubtasks.value[taskId] = false; return }
  expandedSubtasks.value[taskId] = true
  try { subtasksMap.value[taskId] = await taskApi.getSubtasks(taskId) } catch {}
}

// ③ 任务详情展开
function toggleTaskDetail(taskId: number) { expandedTaskDetails.value[taskId] = !expandedTaskDetails.value[taskId] }
function toggleNoteDetail(noteId: number) { expandedNoteDetails.value[noteId] = !expandedNoteDetails.value[noteId] }

// ② 昼夜（持久化）
function toggleDark() {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark-mode', isDark.value)
  localStorage.setItem(STORAGE_KEY, isDark.value ? 'dark' : 'light')
}

// ④ 新增功能
async function addItem() {
  if (!addText.value.trim()) return
  const text = addText.value.trim()
  addText.value = ''
  showAddInput.value = false
  try {
    if (activeTab.value === 'tasks') { await taskApi.create({ title: text }); store.tasks = await taskApi.list() }
    else if (activeTab.value === 'travel') { await travelPlanApi.create({ title: text }); store.travelPlans = await travelPlanApi.list() }
    else if (activeTab.value === 'notes') {
      const data: any = { title: text, content: '' }
      if (selectedCatId.value) { data.category_id = selectedCatId.value; data.category = 'custom' }
      await noteApi.create(data)
      store.notes = await noteApi.list()
    }
  } catch {}
}

// ④ 删除
async function deleteItem(id: number, type: string) {
  try {
    if (type === 'task') { await taskApi.delete(id); store.tasks = store.tasks.filter(t => t.id !== id) }
    else if (type === 'plan') { await travelPlanApi.delete(id); store.travelPlans = store.travelPlans.filter(p => p.id !== id) }
    else if (type === 'note') { await noteApi.delete(id); store.notes = store.notes.filter(n => n.id !== id) }
  } catch {}
}

// 关闭便签
function closeSticky() { window.close() }

// 键盘
function onKeydown(e: KeyboardEvent) {
  if (e.key === 'ArrowLeft') { const tabs: StickyTab[] = ['tasks','travel','notes']; activeTab.value = tabs[(tabs.indexOf(activeTab.value) - 1 + 3) % 3] }
  else if (e.key === 'ArrowRight') { const tabs: StickyTab[] = ['tasks','travel','notes']; activeTab.value = tabs[(tabs.indexOf(activeTab.value) + 1) % 3] }
  else if (e.key === 'Escape') closeSticky()
}
onMounted(() => { if (typeof window !== 'undefined') window.addEventListener('keydown', onKeydown) })
onUnmounted(() => { if (typeof window !== 'undefined') window.removeEventListener('keydown', onKeydown) })
</script>

<template>
  <div class="sticky" :class="isDark ? 's-dark' : 's-light'">
    <!-- Header -->
    <div class="s-header">
      <button class="s-btn" @click="closeSticky()" v-html="icons.close" title="关闭 (Esc)"></button>
      <button class="s-btn" @click="toggleDark" v-html="isDark ? icons.sun : icons.moon" title="切换模式"></button>
      <span class="s-title">{{ tabLabels[activeTab] }}</span>
      <span class="s-badge">{{ activeTab === 'tasks' ? store.pendingTasks.length : activeTab === 'travel' ? store.travelPlans.filter(p=>!p.completed).length : store.notes.length }}</span>
    </div>

    <!-- Tabs -->
    <div class="s-tabs">
      <button class="s-tab" :class="{on:activeTab==='tasks'}" @click="activeTab='tasks'" v-html="icons.list" title="当前任务"></button>
      <button class="s-tab" :class="{on:activeTab==='travel'}" @click="activeTab='travel'" v-html="icons.travel" title="出行计划"></button>
      <button class="s-tab" :class="{on:activeTab==='notes'}" @click="activeTab='notes'" v-html="icons.notes" title="值得记录"></button>
    </div>

    <!-- Body -->
    <div class="s-body">

      <!-- ===== TASKS ===== -->
      <template v-if="activeTab === 'tasks'">
        <div v-if="topTasks.length === 0" class="s-empty">
          <span v-html="icons.list" style="width:24px;height:24px;opacity:0.3;"></span>
          <span>暂无任务</span>
        </div>
        <div v-for="task in topTasks" :key="task.id" class="s-item">
          <span class="s-cb" :class="{done:task.completed}" @click="toggleTask(task)">{{ task.completed ? '✓' : '' }}</span>
          <button class="s-arr" @click="toggleSubtasks(task.id)" v-html="expandedSubtasks[task.id] ? icons.chevronDown : icons.chevronUp" :style="{opacity:0.5}"></button>
          <span class="s-txt" @click="toggleTaskDetail(task.id)">{{ task.title }}</span>
          <span v-if="task.priority===2" class="s-urg">!!!</span>
          <span class="s-del" @click="deleteItem(task.id,'task')" v-html="icons.trash" style="width:12px;height:12px;flex-shrink:0;cursor:pointer;opacity:0.3;"></span>
          <!-- ③ 子任务（独立于详情，点击箭头即可展开） -->
          <div v-if="expandedSubtasks[task.id]" class="s-detail">
            <div v-if="subtasksMap[task.id]?.length" class="s-subs">
              <div v-for="sub in subtasksMap[task.id]" :key="sub.id" class="s-sub">
                <span class="s-cb sm" :class="{done:sub.completed}" @click="toggleTask(sub)">{{ sub.completed ? '✓' : '' }}</span>
                <span class="s-txt">{{ sub.title }}</span>
                <span v-if="sub.description" class="s-desc" style="padding-left:18px;">{{ sub.description }}</span>
              </div>
            </div>
            <div v-else class="s-empty" style="padding:4px 0;font-size:10px;">暂无子任务</div>
          </div>
          <!-- ③ 详情（点击文字展开） -->
          <div v-if="expandedTaskDetails[task.id]" class="s-detail">
            <div v-if="task.description" class="s-desc">{{ task.description }}</div>
          </div>
        </div>
      </template>

      <!-- ===== TRAVEL ===== -->
      <template v-if="activeTab === 'travel'">
        <div v-if="topPlans.length === 0" class="s-empty">
          <span v-html="icons.travel" style="width:24px;height:24px;opacity:0.3;"></span>
          <span>暂无计划</span>
        </div>
        <div v-for="plan in topPlans" :key="plan.id" class="s-item">
          <span class="s-cb" :class="{done:plan.completed}" @click="togglePlan(plan)">{{ plan.completed ? '✓' : '' }}</span>
          <span class="s-txt" @click="toggleTaskDetail(plan.id)">{{ plan.title }}</span>
          <span v-if="plan.destination" v-html="icons.mapPin" style="width:11px;height:11px;opacity:0.4;flex-shrink:0;"></span>
          <span class="s-del" @click="deleteItem(plan.id,'plan')" v-html="icons.trash" style="width:12px;height:12px;flex-shrink:0;cursor:pointer;opacity:0.3;"></span>
          <div v-if="expandedTaskDetails[plan.id] && (plan.destination||plan.notes)" class="s-detail">
            <div v-if="plan.destination" class="s-desc">📍 {{ plan.destination }} · {{ plan.plan_date || '' }} {{ plan.start_time || '' }}</div>
            <div v-if="plan.notes" class="s-desc">{{ plan.notes }}</div>
          </div>
        </div>
      </template>

      <!-- ===== NOTES ===== -->
      <template v-if="activeTab === 'notes'">
        <div v-if="topNotes.length === 0" class="s-empty">
          <span v-html="icons.notes" style="width:24px;height:24px;opacity:0.3;"></span>
          <span>暂无记录</span>
        </div>
        <div v-for="note in topNotes" :key="note.id" class="s-item">
          <span class="s-txt" @click="toggleNoteDetail(note.id)">{{ note.title }}</span>
          <button class="s-arr" @click="toggleNoteDetail(note.id)" v-html="expandedNoteDetails[note.id] ? icons.chevronDown : icons.chevronUp" :style="{opacity:0.5}"></button>
          <span class="s-del" @click="deleteItem(note.id,'note')" v-html="icons.trash" style="width:12px;height:12px;flex-shrink:0;cursor:pointer;opacity:0.3;"></span>
          <div v-if="expandedNoteDetails[note.id]" class="s-detail">
            <div v-if="note.content" class="s-desc">{{ note.content.substring(0,150) }}{{ note.content.length>150?'...':'' }}</div>
          </div>
        </div>
      </template>
    </div>

    <!-- ④ 添加按钮 + 输入框 -->
    <div class="s-footer">
      <template v-if="showAddInput">
        <div style="display:flex;gap:4px;width:100%;">
          <input v-model="addText" class="s-input" :placeholder="'输入' + (activeTab==='tasks'?'任务':activeTab==='travel'?'计划':'标题')" @keyup.enter="addItem" @keyup.escape="showAddInput=false" ref="addInput" />
          <button class="s-btn-add" @click="addItem" v-html="icons.plus" title="添加"></button>
          <button class="s-btn-add" @click="showAddInput=false" v-html="icons.close" title="取消"></button>
        </div>
        <select v-if="activeTab==='notes'" v-model="selectedCatId" class="s-input" style="margin-top:4px;font-size:10px;height:28px;">
          <option :value="null">未分类</option>
          <option v-for="c in catOptions" :key="c.id" :value="c.id">{{ c.icon }} {{ c.name }}</option>
        </select>
      </template>
      <button v-else class="s-add-btn" @click="showAddInput=true">
        <span v-html="icons.plus" style="width:14px;height:14px;"></span> 添加{{ activeTab==='tasks'?'任务':activeTab==='travel'?'计划':'记录' }}
      </button>
      <div class="s-hints">← → 切换 · Esc 关闭</div>
    </div>
  </div>
</template>

<style>
/* ===== Reset ===== */
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'Nunito',-apple-system,sans-serif;overflow:hidden;user-select:none;-webkit-app-region:drag;}

.sticky{height:100vh;display:flex;flex-direction:column;}

/* ===== Light ===== */
.s-light{background:#FDFCF8;color:#2C2C24;}
.s-light .s-header{border-color:#DED8CF;}
.s-light .s-item{border-color:#EDE8E0;}
.s-light .s-badge{background:rgba(93,112,82,0.1);color:#5D7052;}
.s-light .s-cb{border-color:#5D7052;}
.s-light .s-cb.done{background:#5D7052;color:white;}
.s-light .s-detail{background:#F0EBE5;color:#4A4A40;}
.s-light .s-sub{background:rgba(93,112,82,0.04);}
.s-light .s-tabs{border-color:#DED8CF;}
.s-light .s-tab{color:#B0AFA0;}
.s-light .s-tab.on{color:#5D7052;}
.s-light .s-footer{background:#F0EBE5;border-color:#DED8CF;}
.s-light .s-input{border-color:#DED8CF;background:white;color:#2C2C24;}
.s-light .s-btn-add{color:#5D7052;}
.s-light .s-hints{color:#B0AFA0;}

/* ===== Dark ===== */
.s-dark{background:#1A1A14;color:#E8E4D8;}
.s-dark .s-header{border-color:#3D3D35;}
.s-dark .s-item{border-color:#2A2A24;}
.s-dark .s-badge{background:rgba(93,112,82,0.15);color:#7D9072;}
.s-dark .s-cb{border-color:#5D7052;}
.s-dark .s-cb.done{background:#5D7052;color:white;}
.s-dark .s-detail{background:#2A2A24;color:#C4C0B4;}
.s-dark .s-sub{background:rgba(93,112,82,0.06);}
.s-dark .s-tabs{border-color:#3D3D35;}
.s-dark .s-tab{color:#5A5A50;}
.s-dark .s-tab.on{color:#7D9072;}
.s-dark .s-footer{background:#22221C;border-color:#3D3D35;}
.s-dark .s-input{border-color:#3D3D35;background:#1A1A14;color:#E8E4D8;}
.s-dark .s-btn-add{color:#7D9072;}
.s-dark .s-hints{color:#5A5A50;}

/* ===== Components ===== */
.s-header{display:flex;align-items:center;gap:6px;padding:8px;border-bottom:1px solid;-webkit-app-region:drag;}
.s-title{flex:1;font-size:13px;font-weight:700;font-family:'Fraunces',serif;text-align:center;}
.s-badge{font-size:10px;padding:1px 8px;border-radius:8px;font-weight:700;}
.s-btn{background:none;border:none;cursor:pointer;width:24px;height:24px;display:flex;align-items:center;justify-content:center;border-radius:50%;color:inherit;opacity:0.5;transition:all 0.2s;-webkit-app-region:no-drag;}
.s-btn:hover{opacity:1;background:rgba(168,84,72,0.15);color:#A85448;}

.s-tabs{display:flex;border-bottom:1px solid;-webkit-app-region:no-drag;}
.s-tab{flex:1;padding:6px;border:none;background:none;cursor:pointer;display:flex;align-items:center;justify-content:center;height:32px;transition:all 0.2s;}
.s-tab:hover{opacity:0.8;}
.s-tab.on{font-weight:700;}

.s-body{flex:1;overflow-y:auto;padding:2px 0;-webkit-app-region:no-drag;scrollbar-width:thin;}
.s-empty{display:flex;flex-direction:column;align-items:center;gap:8px;padding:30px;font-size:12px;opacity:0.4;}
.s-item{display:flex;align-items:flex-start;gap:5px;padding:5px 8px;font-size:12px;flex-wrap:wrap;border-bottom:1px solid;}
.s-cb{width:15px;height:15px;min-width:15px;border:1.5px solid;border-radius:30% 70% 50% 50%/50% 40% 60% 50%;display:flex;align-items:center;justify-content:center;font-size:8px;font-weight:700;cursor:pointer;-webkit-app-region:no-drag;transition:all 0.2s;margin-top:1px;}
.s-cb.sm{width:11px;height:11px;min-width:11px;font-size:7px;margin-top:0;}
.s-arr{background:none;border:none;cursor:pointer;padding:0;width:14px;height:14px;display:flex;align-items:center;justify-content:center;color:inherit;-webkit-app-region:no-drag;flex-shrink:0;margin-top:2px;}
.s-txt{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;cursor:pointer;line-height:1.5;}
.s-urg{color:#A85448;font-size:9px;font-weight:700;}
.s-del:hover{opacity:1!important;color:#A85448!important;}

.s-detail{width:100%;padding:6px 8px;border-radius:6px;margin:2px 0;font-size:11px;line-height:1.5;}
.s-desc{margin:2px 0;}
.s-subs{padding:4px 0;}
.s-sub{display:flex;flex-wrap:wrap;align-items:flex-start;gap:4px;padding:3px 6px;border-radius:4px;margin:2px 0;font-size:11px;}

.s-footer{padding:6px 8px;border-top:1px solid;-webkit-app-region:no-drag;}
.s-add-btn{display:flex;align-items:center;gap:6px;width:100%;padding:6px 10px;border:1.5px dashed;border-radius:20px;background:none;cursor:pointer;font-size:12px;font-weight:600;color:inherit;opacity:0.5;transition:all 0.2s;justify-content:center;}
.s-add-btn:hover{opacity:1;border-style:solid;}
.s-input{flex:1;padding:6px 10px;border:1.5px solid;border-radius:20px;font-size:12px;font-family:inherit;outline:none;height:32px;}
.s-input:focus{border-color:var(--primary,#5D7052);}
.s-btn-add{background:none;border:none;cursor:pointer;width:30px;height:30px;display:flex;align-items:center;justify-content:center;border-radius:50%;opacity:0.6;transition:all 0.2s;}
.s-btn-add:hover{opacity:1;background:rgba(93,112,82,0.15);}
.s-hints{display:flex;justify-content:center;gap:8px;font-size:9px;margin-top:4px;}
</style>
