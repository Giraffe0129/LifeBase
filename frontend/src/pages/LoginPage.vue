<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/useAuthStore'
import { icons } from '@/utils/icons'

const router = useRouter()
const auth = useAuthStore()

const mode = ref<'login' | 'register'>('login')
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  if (!username.value.trim() || !password.value.trim()) { error.value = '请填写用户名和密码'; return }
  error.value = ''
  loading.value = true
  try {
    if (mode.value === 'login') await auth.login(username.value.trim(), password.value.trim())
    else await auth.register(username.value.trim(), password.value.trim())
    router.push('/tasks')
  } catch (e: any) { error.value = e.message || '操作失败' }
  finally { loading.value = false }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
        <div class="sidebar-logo" v-html="icons.notes" style="width: 44px; height: 44px;"></div>
        <h1>My App</h1>
      </div>
      <p class="subtitle">多端互通任务 · 出行 · 笔记管理</p>

      <div class="login-tabs">
        <button class="login-tab" :class="{ active: mode === 'login' }" @click="mode = 'login'">登录</button>
        <button class="login-tab" :class="{ active: mode === 'register' }" @click="mode = 'register'">注册</button>
      </div>

      <div v-if="error" style="background: rgba(168,84,72,0.1); color: var(--destructive); padding: 12px 16px; border-radius: var(--radius-pill); font-size: 13px; margin-bottom: 20px; display: flex; flex-direction: column; gap: 4px; font-weight: 600;">
        <div style="display: flex; align-items: flex-start; gap: 8px;">
          <span style="flex-shrink:0; margin-top: 2px;" v-html="icons.close"></span>
          <span style="white-space: pre-line;">{{ error }}</span>
        </div>
      </div>

      <form @submit.prevent="submit">
        <div class="input-group">
          <label>用户名</label>
          <input v-model="username" class="input-field" placeholder="输入用户名" autocomplete="username" />
        </div>
        <div class="input-group">
          <label>密码</label>
          <input v-model="password" class="input-field" type="password" placeholder="输入密码" autocomplete="current-password" />
        </div>
        <button type="submit" class="btn btn-primary btn-block mt-16" :disabled="loading" style="height: 52px;">
          <span v-if="loading" style="display:inline-block; width:18px; height:18px; border:2px solid rgba(255,255,255,0.3); border-top-color:white; border-radius:50%; animation:spin 0.7s linear;"></span>
          {{ loading ? '处理中...' : (mode === 'login' ? '登录' : '注册') }}
        </button>
      </form>

      <div class="text-center text-sm mt-16" style="color: var(--muted-foreground);">
        {{ mode === 'login' ? '还没有账号？' : '已有账号？' }}
        <a href="#" @click.prevent="mode = mode === 'login' ? 'register' : 'login'" style="color: var(--primary); font-weight: 700; text-decoration: none;">
          {{ mode === 'login' ? '注册' : '登录' }}
        </a>
      </div>
    </div>
  </div>
</template>
