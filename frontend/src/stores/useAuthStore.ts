import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'
import { db } from '@/db/localDB'

/**
 * 用户认证状态管理
 *
 * Token 持久化到 localStorage，应用重启后自动恢复登录态。
 */
export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('auth_token'))
  const user = ref<any | null>(null)

  const isLoggedIn = computed(() => !!token.value)

  /** 保存 Token */
  function setToken(t: string) {
    token.value = t
    localStorage.setItem('auth_token', t)
  }

  /** 清除 Token */
  function clearToken() {
    token.value = null
    user.value = null
    localStorage.removeItem('auth_token')
  }

  /** 注册 */
  async function register(username: string, password: string) {
    const res = await authApi.register({ username, password })
    setToken(res.access_token)
    user.value = res.user
    return res
  }

  /** 登录 */
  async function login(username: string, password: string) {
    const res = await authApi.login({ username, password })
    setToken(res.access_token)
    user.value = res.user
    return res
  }

  /** 退出登录 */
  function logout() {
    clearToken()
  }

  /** 从 Token 恢复用户信息 */
  async function restoreSession() {
    if (!token.value) return false
    try {
      user.value = await authApi.getMe()
      return true
    } catch {
      clearToken()
      return false
    }
  }

  return {
    token, user, isLoggedIn,
    register, login, logout, restoreSession,
  }
})
