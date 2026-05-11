<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAppStore } from '@/stores/useAppStore'
import { travelPlanApi } from '@/api'
import { icons } from '@/utils/icons'

const store = useAppStore()

const showAddModal = ref(false)
const newPlan = ref({ title: '', destination: '', plan_date: '', start_time: '', notes: '' })
const submitting = ref(false)

// Drag
const dragIndex = ref<number | null>(null)
const dragOverIndex = ref<number | null>(null)
function onDragStart(i: number) { dragIndex.value = i }
function onDragOver(e: DragEvent, i: number) { e.preventDefault(); dragOverIndex.value = i }
function onDragEnd() {
  if (dragIndex.value === null || dragOverIndex.value === null) return
  if (dragIndex.value === dragOverIndex.value) { resetDrag(); return }
  const items = [...store.travelPlans]
  const [moved] = items.splice(dragIndex.value, 1)
  items.splice(dragOverIndex.value, 0, moved)
  const orders = items.map((item, idx) => ({ id: item.id, sort_order: idx }))
  store.travelPlans = items
  travelPlanApi.reorder(orders).catch(() => {})
  resetDrag()
}
function resetDrag() { dragIndex.value = null; dragOverIndex.value = null }

// Time Picker
const showTimePicker = ref(false)
const pickerMode = ref<'date' | 'time'>('date')
const now = new Date()
const pickerYear = ref(now.getFullYear())
const pickerMonth = ref(now.getMonth() + 1)
const pickerDay = ref(now.getDate())
const pickerHour = ref(now.getHours())
const pickerMinute = ref(now.getMinutes())

const years = computed(() => { const y = []; for (let i = 2020; i <= 2040; i++) y.push(i); return y })
const months = computed(() => Array.from({ length: 12 }, (_, i) => i + 1))
const daysInMonth = computed(() => new Date(pickerYear.value, pickerMonth.value, 0).getDate())
const days = computed(() => Array.from({ length: daysInMonth.value }, (_, i) => i + 1))
const hours = computed(() => Array.from({ length: 24 }, (_, i) => i))
const minutes = computed(() => Array.from({ length: 60 }, (_, i) => i))

function openDatePicker() { pickerMode.value = 'date'; showTimePicker.value = true }
function openTimePicker() { pickerMode.value = 'time'; showTimePicker.value = true }
function confirmPicker() {
  if (pickerMode.value === 'date') {
    newPlan.value.plan_date = `${pickerYear.value}-${String(pickerMonth.value).padStart(2,'0')}-${String(pickerDay.value).padStart(2,'0')}`
  } else {
    newPlan.value.start_time = `${String(pickerHour.value).padStart(2,'0')}:${String(pickerMinute.value).padStart(2,'0')}`
  }
  showTimePicker.value = false
}

// Weather
function getWeatherIcon(tip: string, needUmbrella: boolean): string {
  if (!tip) return icons.sunIcon
  const l = tip.toLowerCase()
  if (l.includes('雨') || needUmbrella) return icons.cloudRain
  if (l.includes('雪')) return icons.cloudSnow
  if (l.includes('云') || l.includes('阴')) return icons.cloud
  if (l.includes('晴')) return icons.sunIcon
  if (l.includes('雾')) return icons.cloud
  if (l.includes('风')) return icons.wind
  return icons.cloudSun
}
function getWeatherClass(tip: string, needUmbrella: boolean): string {
  if (!tip) return ''
  const l = tip.toLowerCase()
  if (l.includes('雨') || needUmbrella) return 'rain'
  if (l.includes('雪')) return 'snow'
  if (l.includes('云') || l.includes('阴')) return 'cloudy'
  if (l.includes('晴') || l.includes('雾')) return 'sunny'
  if (l.includes('风')) return 'cloudy'
  return 'sunny'
}

// CRUD
async function addPlan() {
  if (!newPlan.value.title.trim()) return
  submitting.value = true
  try {
    await travelPlanApi.create({
      title: newPlan.value.title.trim(), destination: newPlan.value.destination.trim(),
      plan_date: newPlan.value.plan_date, start_time: newPlan.value.start_time,
      notes: newPlan.value.notes.trim(),
    })
    const n = new Date()
    newPlan.value = { title: '', destination: '', plan_date: '', start_time: '', notes: '' }
    pickerYear.value = n.getFullYear(); pickerMonth.value = n.getMonth() + 1; pickerDay.value = n.getDate()
    pickerHour.value = n.getHours(); pickerMinute.value = n.getMinutes()
    showAddModal.value = false
  } catch (e: any) { alert(e.message || '创建失败') }
  finally { submitting.value = false }
}
async function deletePlan(id: number) { if (!confirm('确定删除？')) return; try { await travelPlanApi.delete(id) } catch (e: any) { alert(e.message || '删除失败') } }
async function toggleComplete(plan: any) { try { await travelPlanApi.update(plan.id, { completed: !plan.completed }) } catch (e: any) { alert(e.message || '更新失败') } }
function openPaymentApp() {
  if (!/Android|iPhone|iPad|iPod/i.test(navigator.userAgent)) { alert('请在手机端打开使用乘车码'); return }
  window.location.href = 'alipays://platformapi/startapp?appId=200001235'
  setTimeout(() => { window.location.href = 'weixin://' }, 500)
}
</script>

<template>
  <div>
    <div v-if="store.travelPlans.length === 0" class="empty-state">
      <div class="empty-icon" v-html="icons.travel"></div>
      <p>还没有出行计划</p>
      <p class="text-sm mt-8" style="color: var(--muted-foreground);">添加目的地后自动显示天气预报</p>
    </div>

    <transition-group name="list" tag="div">
      <div v-for="(plan, index) in store.travelPlans" :key="plan.id"
        class="claude-card" :class="{ dragging: dragIndex === index }"
        :style="{ opacity: plan.completed ? 0.55 : 1 }"
        draggable="true" @dragstart="onDragStart(index)" @dragover="onDragOver($event, index)"
        @dragend="onDragEnd" @dragleave="dragOverIndex = null"
        style="display: flex; align-items: flex-start; gap: 12px;">
        <span class="drag-handle" style="margin-top: 4px;" v-html="icons.grip" title="拖拽排序"></span>
        <div style="flex: 1; min-width: 0;">
          <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
            <div class="checkbox-claude" :class="{ checked: plan.completed }" @click="toggleComplete(plan)">
              <span v-if="plan.completed" v-html="icons.check"></span>
            </div>
            <h3 style="font-family: var(--font-heading); font-size: 16px; font-weight: 700; flex:1;"
              :style="{ textDecoration: plan.completed ? 'line-through' : 'none' }">{{ plan.title }}</h3>
          </div>
          <div style="display: flex; flex-wrap: wrap; gap: 8px; font-size: 13px; color: var(--muted-foreground);">
            <span v-if="plan.destination" style="display: flex; align-items: center; gap: 4px;"><span v-html="icons.travel" style="width:14px;height:14px;"></span> {{ plan.destination }}</span>
            <span v-if="plan.plan_date" style="display: flex; align-items: center; gap: 4px;">📅 {{ plan.plan_date }}</span>
            <span v-if="plan.start_time" style="display: flex; align-items: center; gap: 4px;">⏰ {{ plan.start_time }}</span>
          </div>

          <div v-if="plan.weather_tip && store.settings?.weather_enabled !== false"
            class="weather-banner" :class="getWeatherClass(plan.weather_tip, plan.need_umbrella)">
            <span class="weather-icon-anim" v-html="getWeatherIcon(plan.weather_tip, plan.need_umbrella)"></span>
            <div style="flex: 1">
              <div style="font-weight: 700;">{{ plan.weather_tip }}</div>
              <div v-if="plan.need_umbrella" style="font-size: 12px; margin-top: 2px; display: flex; align-items: center; gap: 4px;">
                <span v-html="icons.umbrella" style="width:14px;height:14px;"></span> 记得带伞
              </div>
            </div>
            <span class="weather-temp" v-if="plan.temperature">{{ plan.temperature }}</span>
          </div>

          <div v-if="plan.notes" class="text-sm text-secondary" style="margin-top: 8px; padding: 10px 16px; background: var(--muted); border-radius: var(--radius-sm);">
            {{ plan.notes }}
          </div>
        </div>
        <button class="btn btn-sm btn-ghost" @click="deletePlan(plan.id)" style="flex-shrink: 0; margin-top: 4px;" v-html="icons.trash"></button>
      </div>
    </transition-group>

    <div class="fab-group">
      <button class="btn btn-secondary btn-round" @click="openPaymentApp" style="flex:1;">
        <span v-html="icons.search" style="width:18px;height:18px;"></span> 乘车码
      </button>
      <button class="btn btn-primary btn-round fab-btn" @click="showAddModal = true" style="flex:1;">
        <span v-html="icons.plus" style="width:20px;height:20px;"></span> 新计划
      </button>
    </div>

    <!-- Add Modal -->
    <transition name="fade">
      <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
        <div class="modal-window">
          <div class="modal-header">
            <h3>新建出行计划</h3>
            <button class="btn btn-sm btn-ghost" @click="showAddModal = false" v-html="icons.close"></button>
          </div>
          <div class="input-group">
            <label>标题</label>
            <input v-model="newPlan.title" class="input-field" placeholder="例如：周末去颐和园" />
          </div>
          <div class="input-group">
            <label>目的地（用于查询天气）</label>
            <input v-model="newPlan.destination" class="input-field" placeholder="例如：北京" />
          </div>
          <div style="display: flex; gap: 10px">
            <div class="input-group" style="flex: 1" @click="openDatePicker">
              <label>日期</label>
              <div class="input-field" style="cursor: pointer; display: flex; align-items: center; gap: 8px;">
                📅 <span :style="{ color: newPlan.plan_date ? 'var(--foreground)' : 'var(--muted-foreground)' }">{{ newPlan.plan_date || '选择日期' }}</span>
              </div>
            </div>
            <div class="input-group" style="flex: 1" @click="openTimePicker">
              <label>时间</label>
              <div class="input-field" style="cursor: pointer; display: flex; align-items: center; gap: 8px;">
                ⏰ <span :style="{ color: newPlan.start_time ? 'var(--foreground)' : 'var(--muted-foreground)' }">{{ newPlan.start_time || '选择时间' }}</span>
              </div>
            </div>
          </div>
          <div class="input-group">
            <label>备注</label>
            <textarea v-model="newPlan.notes" class="input-field" placeholder="补充信息..." rows="3"></textarea>
          </div>
          <button class="btn btn-primary btn-block mt-12" :disabled="!newPlan.title.trim() || submitting" @click="addPlan">
            {{ submitting ? '创建中...' : '创建计划' }}
          </button>
          <div class="text-center text-sm text-secondary mt-8">创建后自动查询目的地天气预报</div>
        </div>
      </div>
    </transition>

    <!-- Time Picker -->
    <transition name="fade">
      <div v-if="showTimePicker" class="modal-overlay" @click.self="showTimePicker = false">
        <div class="modal-window" style="max-width: 360px;">
          <div class="modal-header">
            <h3>{{ pickerMode === 'date' ? '选择日期' : '选择时间' }}</h3>
            <button class="btn btn-sm btn-ghost" @click="showTimePicker = false" v-html="icons.close"></button>
          </div>
          <div v-if="pickerMode === 'date'" class="time-picker-container">
            <div><div class="time-picker-label text-center">年</div>
              <div class="time-picker-column"><div class="time-picker-highlight"></div>
                <div v-for="y in years" :key="y" class="time-picker-item" :class="{ selected: y === pickerYear }" @click="pickerYear = y">{{ y }}</div>
              </div></div>
            <div><div class="time-picker-label text-center">月</div>
              <div class="time-picker-column"><div class="time-picker-highlight"></div>
                <div v-for="m in months" :key="m" class="time-picker-item" :class="{ selected: m === pickerMonth }" @click="pickerMonth = m">{{ String(m).padStart(2,'0') }}</div>
              </div></div>
            <div><div class="time-picker-label text-center">日</div>
              <div class="time-picker-column"><div class="time-picker-highlight"></div>
                <div v-for="d in days" :key="d" class="time-picker-item" :class="{ selected: d === pickerDay }" @click="pickerDay = d">{{ String(d).padStart(2,'0') }}</div>
              </div></div>
          </div>
          <div v-else class="time-picker-container">
            <div><div class="time-picker-label text-center">时</div>
              <div class="time-picker-column"><div class="time-picker-highlight"></div>
                <div v-for="h in hours" :key="h" class="time-picker-item" :class="{ selected: h === pickerHour }" @click="pickerHour = h">{{ String(h).padStart(2,'0') }}</div>
              </div></div>
            <div><div class="time-picker-label text-center">分</div>
              <div class="time-picker-column"><div class="time-picker-highlight"></div>
                <div v-for="m in minutes" :key="m" class="time-picker-item" :class="{ selected: m === pickerMinute }" @click="pickerMinute = m">{{ String(m).padStart(2,'0') }}</div>
              </div></div>
          </div>
          <div style="display: flex; gap: 8px; margin-top: 16px;">
            <button class="btn btn-secondary" style="flex:1" @click="showTimePicker = false">取消</button>
            <button class="btn btn-primary" style="flex:1" @click="confirmPicker">确定</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>
