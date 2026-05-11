<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/useAuthStore'
import { useAppStore } from '@/stores/useAppStore'
import { authApi, settingsApi } from '@/api'
import { icons } from '@/utils/icons'

const router = useRouter()
const auth = useAuthStore()
const store = useAppStore()

const qweatherKey = ref('')
const saved = ref(false)
const saving = ref(false)
const weatherEnabled = ref(true)
const weatherSaving = ref(false)
const isDark = ref(false)

onMounted(() => {
  if (auth.user?.has_qweather_key) qweatherKey.value = '已配置'
  weatherEnabled.value = store.settings?.weather_enabled !== false
  isDark.value = document.documentElement.classList.contains('dark-mode')
})

async function saveKey() {
  if (!qweatherKey.value.trim() || qweatherKey.value === '已配置') return
  saving.value = true; saved.value = false
  try { await authApi.updateQWeatherKey(qweatherKey.value.trim()); saved.value = true; setTimeout(() => saved.value = false, 3000) }
  catch (e: any) { alert('保存失败: ' + e.message) }
  finally { saving.value = false }
}

async function toggleWeather() {
  weatherSaving.value = true
  try { const r = await settingsApi.update({ weather_enabled: weatherEnabled.value }); store.settings = r }
  catch (e: any) { weatherEnabled.value = !weatherEnabled.value; alert('设置保存失败') }
  finally { weatherSaving.value = false }
}

function toggleDarkMode() {
  isDark.value = !isDark.value
  if (isDark.value) document.documentElement.classList.add('dark-mode')
  else document.documentElement.classList.remove('dark-mode')
  localStorage.setItem('theme_manual', isDark.value ? 'dark' : 'light')
}

function logout() { auth.logout(); router.push('/login') }
</script>

<template>
  <div>
    <div class="claude-card">
      <div class="settings-section" style="margin-bottom: 0;">
        <h3><span v-html="icons.settings" style="width:18px;height:18px;"></span> 用户信息</h3>
        <div class="text-sm" style="color: var(--muted-foreground);">
          <p>用户名：<strong style="color: var(--foreground);">{{ auth.user?.username || '未知' }}</strong></p>
          <p class="mt-8">ID：<code style="background: var(--muted); padding: 2px 8px; border-radius: 6px; font-size: 12px;">{{ auth.user?.id }}</code></p>
        </div>
      </div>
    </div>

    <div class="claude-card">
      <div class="settings-section" style="margin-bottom: 0;">
        <h3><span v-html="icons.cloudSun" style="width:18px;height:18px;color:var(--primary);"></span> 天气设置</h3>
        <div class="desc">在<strong>出行计划</strong>功能中，系统会自动查询目的地的天气预报。</div>

        <div style="display: flex; align-items: center; justify-content: space-between; padding: 14px 0; border-top: 1px solid var(--border);">
          <div>
            <div style="font-weight: 700; font-size: 14px;">天气显示</div>
            <div class="text-sm text-secondary">在主界面和出行界面显示天气可视化效果</div>
          </div>
          <div class="toggle-switch" @click="weatherEnabled = !weatherEnabled; toggleWeather()">
            <div class="toggle-track" :class="{ active: weatherEnabled }"><div class="toggle-thumb"></div></div>
          </div>
        </div>

        <div style="padding-top: 14px; border-top: 1px solid var(--border);">
          <div class="desc mt-8">请输入你的和风天气 API Key（<a href="https://dev.qweather.com" target="_blank">免费申请</a>）。</div>
          <div class="input-group">
            <input v-model="qweatherKey" class="input-field" :placeholder="auth.user?.has_qweather_key ? '已配置，输入新 Key 可覆盖' : '输入你的和风天气 API Key'" />
          </div>
          <button class="btn btn-primary btn-sm" :disabled="!qweatherKey.trim() || qweatherKey === '已配置' || saving" @click="saveKey">
            {{ saving ? '保存中...' : '保存配置' }}
          </button>
          <span v-if="saved" style="color: var(--primary); font-size: 13px; margin-left: 10px; font-weight: 600;">✓ 已保存</span>
        </div>
      </div>
    </div>

    <div class="claude-card">
      <div class="settings-section" style="margin-bottom: 0;">
        <h3>ℹ️ 关于</h3>
        <div class="desc">
          <p>版本：v3.0.0</p>
          <p class="mt-8">架构：云端部署 + 离线缓存 + 多端同步</p>
          <p class="mt-8">支持：桌面端 (Electron) / 移动端 (Capacitor) / PWA</p>
        </div>
        <div class="mt-12" style="padding-top: 14px; border-top: 1px solid var(--border);">
          <div style="display: flex; align-items: center; gap: 14px;">
            <span class="text-sm" style="font-weight: 600;">夜间模式</span>
            <div class="toggle-switch" @click="toggleDarkMode()">
              <div class="toggle-track" :class="{ active: isDark }"><div class="toggle-thumb"></div></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <button class="btn btn-danger btn-block mt-16" @click="logout">
      <span v-html="icons.close" style="width:18px;height:18px;"></span> 退出登录
    </button>
  </div>
</template>
