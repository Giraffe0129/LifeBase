<script setup lang="ts">
import { ref } from 'vue'
import { useAppStore } from '@/stores/useAppStore'
import { travelPlanApi } from '@/api'

const store = useAppStore()

const showAddModal = ref(false)
const newPlan = ref({ title: '', destination: '', plan_date: '', start_time: '', notes: '' })
const submitting = ref(false)

async function addPlan() {
  if (!newPlan.value.title.trim()) return
  submitting.value = true
  try {
    await travelPlanApi.create({
      title: newPlan.value.title.trim(),
      destination: newPlan.value.destination.trim(),
      plan_date: newPlan.value.plan_date,
      start_time: newPlan.value.start_time,
      notes: newPlan.value.notes.trim(),
    })
    newPlan.value = { title: '', destination: '', plan_date: '', start_time: '', notes: '' }
    showAddModal.value = false
  } catch (e: any) {
    alert('创建失败: ' + e.message)
  } finally {
    submitting.value = false
  }
}

async function deletePlan(id: number) {
  if (!confirm('确定删除此出行计划？')) return
  try {
    await travelPlanApi.delete(id)
  } catch (e: any) {
    alert('删除失败: ' + e.message)
  }
}

async function toggleComplete(plan: any) {
  try {
    await travelPlanApi.update(plan.id, { completed: !plan.completed })
  } catch (e: any) {
    alert('更新失败: ' + e.message)
  }
}

/**
 * 打开支付宝付款码 / 乘车码
 * URL Scheme 说明（仅移动端有效）：
 * - alipays://platformapi/startapp?appId=20000056  → 支付宝付款码
 * - alipays://platformapi/startapp?appId=200001235 → 支付宝乘车码
 * - weixin://  → 微信（仅限支持 URL Scheme 的环境）
 */
function openPaymentApp() {
  const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent)
  if (!isMobile) {
    alert('请在手机端打开以使用支付宝/微信联动')
    return
  }
  // 优先尝试支付宝乘车码
  window.location.href = 'alipays://platformapi/startapp?appId=200001235'
  // 如果未安装支付宝，可尝试微信（备选）
  setTimeout(() => {
    window.location.href = 'weixin://'
  }, 500)
}
</script>

<template>
  <div>
    <div v-if="store.travelPlans.length === 0" class="empty-state">
      <div class="empty-icon">🗺️</div>
      <p>还没有出行计划</p>
    </div>

    <div v-for="plan in store.travelPlans" :key="plan.id" class="card" :style="{ opacity: plan.completed ? 0.6 : 1 }">
      <div style="display: flex; justify-content: space-between; align-items: flex-start">
        <div style="flex: 1">
          <div style="display: flex; align-items: center; gap: 8px">
            <div
              class="checkbox-wrapper"
              @click="toggleComplete(plan)"
              style="font-size: 12px"
            >
              <div
                class="checkbox-custom"
                :class="{ checked: plan.completed }"
                style="width: 18px; height: 18px"
              >
                {{ plan.completed ? '✓' : '' }}
              </div>
            </div>
            <h3 style="font-size: 16px; font-weight: 600" :style="{ textDecoration: plan.completed ? 'line-through' : 'none' }">
              {{ plan.title }}
            </h3>
          </div>

          <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; font-size: 13px; color: var(--color-text-secondary)">
            <span v-if="plan.destination">📍 {{ plan.destination }}</span>
            <span v-if="plan.plan_date">📅 {{ plan.plan_date }}</span>
            <span v-if="plan.start_time">⏰ {{ plan.start_time }}</span>
          </div>

          <!-- 天气信息 -->
          <div v-if="plan.weather_tip" class="weather-banner" :class="plan.need_umbrella ? 'rain' : 'sunny'">
            <span class="umbrella-icon">{{ plan.need_umbrella ? '☂️' : '☀️' }}</span>
            <span>{{ plan.weather_tip }}</span>
            <span v-if="plan.temperature" style="margin-left: auto; font-weight: 600">
              {{ plan.temperature }}
            </span>
          </div>

          <!-- 带伞提示 -->
          <div v-if="plan.need_umbrella" class="weather-banner rain" style="margin-top: 4px">
            <span>🌂 <strong>提醒：</strong>今天可能有雨，出门记得带伞！</span>
          </div>

          <div v-if="plan.notes" class="text-sm text-secondary" style="margin-top: 8px">
            {{ plan.notes }}
          </div>
        </div>

        <button class="btn btn-sm btn-danger" @click="deletePlan(plan.id)" style="flex-shrink: 0; margin-left: 8px">删除</button>
      </div>
    </div>

    <!-- 添加 & 支付按钮 -->
    <div style="display: flex; gap: 8px; position: fixed; bottom: 80px; left: 50%; transform: translateX(-50%); z-index: 50; max-width: 480px; width: calc(100% - 32px)">
      <button class="btn btn-success" style="flex: 1; padding: 14px; border-radius: var(--radius); box-shadow: var(--shadow-lg)" @click="openPaymentApp">
        🚇 乘车码
      </button>
      <button class="btn btn-primary" style="flex: 1; padding: 14px; border-radius: var(--radius); box-shadow: var(--shadow-lg)" @click="showAddModal = true">
        + 添加计划
      </button>
    </div>

    <!-- 新增出行计划弹窗 -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>新建出行计划</h3>
          <button class="modal-close" @click="showAddModal = false">✕</button>
        </div>

        <div class="input-group">
          <label>标题 *</label>
          <input v-model="newPlan.title" class="input-field" placeholder="例如：周末去颐和园" />
        </div>

        <div class="input-group">
          <label>目的地（用于查询天气）</label>
          <input v-model="newPlan.destination" class="input-field" placeholder="例如：北京" />
        </div>

        <div style="display: flex; gap: 8px">
          <div class="input-group" style="flex: 1">
            <label>日期</label>
            <input v-model="newPlan.plan_date" class="input-field" type="date" />
          </div>
          <div class="input-group" style="flex: 1">
            <label>时间</label>
            <input v-model="newPlan.start_time" class="input-field" type="time" />
          </div>
        </div>

        <div class="input-group">
          <label>备注</label>
          <textarea v-model="newPlan.notes" class="input-field" placeholder="补充信息..." rows="3"></textarea>
        </div>

        <button class="btn btn-primary btn-block mt-12" :disabled="!newPlan.title.trim() || submitting" @click="addPlan">
          {{ submitting ? '创建中...' : '创建计划' }}
        </button>

        <div class="text-center text-sm text-secondary" style="margin-top: 8px">
          创建后自动查询目的地天气预报
        </div>
      </div>
    </div>
  </div>
</template>
