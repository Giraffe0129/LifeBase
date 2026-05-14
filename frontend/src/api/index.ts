/**
 * API 客户端 - 统一封装后端 RESTful 接口和 WebSocket
 *
 * 在线时：直接调用服务器 API
 * 离线时：操作写入本地 IndexedDB 并加入同步队列
 */
import { isOnline } from '@/db/localDB'
import { updateLocalCache, removeLocalCache, enqueueSync } from '@/db/sync'

// 生产环境（Electron 打包后）：API 请求指向本地后端
// 开发环境：由 Vite proxy 转发到 localhost:8000
// Android/Capacitor：修改下面的地址为你电脑的局域网 IP
//
// ⚠️ 部署 APK 前请检查：
//   1. 手机和电脑是否在同一个 WiFi 下
//   2. 电脑的局域网 IP 是否与下面一致（cmd 输入 ipconfig 查看 IPv4 地址）
//   3. 后端服务器是否已启动（uvicorn）
//   4. 电脑防火墙是否放行了 8000 端口
const CAPACITOR_SERVER = import.meta.env.VITE_API_URL || 'http://192.168.3.53:8000'
const BASE_URL = import.meta.env.PROD
  ? (window as any).electronAPI?.isElectron
    ? 'http://localhost:8000'
    : typeof (window as any).Capacitor !== 'undefined'
      ? CAPACITOR_SERVER
      : ''
  : ''

/** 获取带认证头的请求配置（直接从 localStorage 读取，避免对 Pinia 的依赖） */
function authHeaders(): Record<string, string> {
  const token = localStorage.getItem('auth_token')
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`
  return headers
}

/** 在线请求封装 */
async function request<T>(url: string, options?: RequestInit): Promise<T> {
  try {
    const res = await fetch(`${BASE_URL}${url}`, {
      headers: authHeaders(),
      ...options,
    })
    if (res.status === 204) return undefined as T
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: '请求失败' }))
      throw new Error(err.detail || `HTTP ${res.status}`)
    }
    return res.json()
  } catch (e: any) {
    // 网络层面的错误（fetch 抛出 TypeError），例如：
    // - CORS 拒绝
    // - DNS 解析失败
    // - 连接被拒绝 / 超时
    // - Android 明文流量被拦截
    if (e instanceof TypeError && e.message === 'Failed to fetch') {
      const isCapacitor = typeof (window as any).Capacitor !== 'undefined'
      const isElectron = !!(window as any).electronAPI?.isElectron
      const baseUrl = BASE_URL || window.location.origin

      let hint = '无法连接到服务器。'
      if (isCapacitor) {
        hint += `\n\n请检查：\n1. 手机和电脑是否连接同一个 WiFi\n2. 电脑端的后端服务是否已启动（端口 8000）\n3. 电脑的防火墙是否放行了 8000 端口\n4. 当前电脑 IP 是否为 ${CAPACITOR_SERVER.replace('http://', '').replace(':8000', '')}\n\n后端地址：${CAPACITOR_SERVER}\n可在 .env 文件中设置 VITE_API_URL 来自定义`
      } else if (isElectron) {
        hint += `请确保后端服务已启动。\n后端地址：${baseUrl}`
      } else {
        hint += `请检查网络连接或后端服务是否正常运行。\n后端地址：${baseUrl}`
      }
      console.error('[API] 网络请求失败:', { url, baseUrl: BASE_URL, isCapacitor, isElectron, error: e })
      throw new Error(hint)
    }
    throw e
  }
}

/** 安全地在线请求，失败时抛异常（让上层判断是否走离线） */
async function onlineRequest<T>(url: string, options?: RequestInit): Promise<T> {
  if (!isOnline()) throw new Error('OFFLINE')
  return request<T>(url, options)
}

// ===== 任务 API =====
export interface TaskItem {
  id: number
  user_id?: number
  parent_id?: number | null
  title: string
  description: string
  completed: boolean
  priority: number
  sort_order: number
  created_at: string | null
  updated_at: string | null
}

export const taskApi = {
  list: () => onlineRequest<TaskItem[]>('/api/tasks/'),

  getSubtasks: (taskId: number) =>
    onlineRequest<TaskItem[]>(`/api/tasks/${taskId}/subtasks`),

  create: async (data: { title: string; description?: string; priority?: number; parent_id?: number }) => {
    try {
      const result = await onlineRequest<TaskItem>('/api/tasks/', {
        method: 'POST',
        body: JSON.stringify(data),
      })
      await updateLocalCache('task', result)
      return result
    } catch (e: any) {
      if (e.message === 'OFFLINE') {
        const localId = `offline_${Date.now()}`
        await enqueueSync('create', 'task', data, localId)
        throw new Error('已离线保存，联网后自动同步')
      }
      throw e
    }
  },

  update: async (id: number, data: Partial<TaskItem>) => {
    try {
      const result = await onlineRequest<TaskItem>(`/api/tasks/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      })
      await updateLocalCache('task', result)
      return result
    } catch (e: any) {
      if (e.message === 'OFFLINE') {
        await enqueueSync('update', 'task', { id, ...data })
        throw new Error('已离线保存，联网后自动同步')
      }
      throw e
    }
  },

  delete: async (id: number) => {
    try {
      await onlineRequest<void>(`/api/tasks/${id}`, { method: 'DELETE' })
      await removeLocalCache('task', id)
    } catch (e: any) {
      if (e.message === 'OFFLINE') {
        await enqueueSync('delete', 'task', { id })
        throw new Error('已离线标记删除，联网后自动同步')
      }
      throw e
    }
  },

  reorder: async (orders: { id: number; sort_order: number }[]) => {
    try {
      const result = await onlineRequest<TaskItem[]>('/api/tasks/reorder/bulk', {
        method: 'PUT',
        body: JSON.stringify(orders),
      })
      return result
    } catch (e: any) {
      console.warn('[Reorder] 排序同步失败, 本地排序将保持', e)
      throw e
    }
  },
}

// ===== 出行计划 API =====
export interface TravelPlanItem {
  id: number
  user_id?: number
  title: string
  destination: string
  plan_date: string
  start_time: string
  notes: string
  need_umbrella: boolean
  weather_tip: string
  temperature: string
  completed: boolean
  sort_order: number
  created_at: string | null
  updated_at: string | null
}

export const travelPlanApi = {
  list: () => onlineRequest<TravelPlanItem[]>('/api/travel-plans/'),

  create: async (data: any) => {
    try {
      const result = await onlineRequest<TravelPlanItem>('/api/travel-plans/', {
        method: 'POST',
        body: JSON.stringify(data),
      })
      await updateLocalCache('travel_plan', result)
      return result
    } catch (e: any) {
      if (e.message === 'OFFLINE') {
        await enqueueSync('create', 'travel_plan', data)
        throw new Error('已离线保存，联网后自动同步')
      }
      throw e
    }
  },

  update: async (id: number, data: Partial<TravelPlanItem>) => {
    try {
      const result = await onlineRequest<TravelPlanItem>(`/api/travel-plans/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      })
      await updateLocalCache('travel_plan', result)
      return result
    } catch (e: any) {
      if (e.message === 'OFFLINE') {
        await enqueueSync('update', 'travel_plan', { id, ...data })
        throw new Error('已离线保存，联网后自动同步')
      }
      throw e
    }
  },

  delete: async (id: number) => {
    try {
      await onlineRequest<void>(`/api/travel-plans/${id}`, { method: 'DELETE' })
      await removeLocalCache('travel_plan', id)
    } catch (e: any) {
      if (e.message === 'OFFLINE') {
        await enqueueSync('delete', 'travel_plan', { id })
        throw new Error('已离线标记删除，联网后自动同步')
      }
      throw e
    }
  },

  reorder: async (orders: { id: number; sort_order: number }[]) => {
    try {
      const result = await onlineRequest<TravelPlanItem[]>('/api/travel-plans/reorder/bulk', {
        method: 'PUT',
        body: JSON.stringify(orders),
      })
      return result
    } catch (e: any) {
      console.warn('[Reorder] 排序同步失败', e)
      throw e
    }
  },
}

// ===== 笔记 API =====
export interface NoteItem {
  id: number
  user_id?: number
  title: string
  content: string
  tags: string
  is_favorite: boolean
  category: string
  category_id: number | null
  sort_order: number
  created_at: string | null
  updated_at: string | null
}

export const noteApi = {
  list: (category?: string) =>
    onlineRequest<NoteItem[]>(`/api/notes/?${category ? `category=${category}` : ''}`),

  create: async (data: any) => {
    try {
      const result = await onlineRequest<NoteItem>('/api/notes/', {
        method: 'POST',
        body: JSON.stringify(data),
      })
      await updateLocalCache('note', result)
      return result
    } catch (e: any) {
      if (e.message === 'OFFLINE') {
        await enqueueSync('create', 'note', data)
        throw new Error('已离线保存，联网后自动同步')
      }
      throw e
    }
  },

  update: async (id: number, data: Partial<NoteItem>) => {
    try {
      const result = await onlineRequest<NoteItem>(`/api/notes/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      })
      await updateLocalCache('note', result)
      return result
    } catch (e: any) {
      if (e.message === 'OFFLINE') {
        await enqueueSync('update', 'note', { id, ...data })
        throw new Error('已离线保存，联网后自动同步')
      }
      throw e
    }
  },

  delete: async (id: number) => {
    try {
      await onlineRequest<void>(`/api/notes/${id}`, { method: 'DELETE' })
      await removeLocalCache('note', id)
    } catch (e: any) {
      if (e.message === 'OFFLINE') {
        await enqueueSync('delete', 'note', { id })
        throw new Error('已离线标记删除，联网后自动同步')
      }
      throw e
    }
  },

  reorder: async (orders: { id: number; sort_order: number }[]) => {
    try {
      const result = await onlineRequest<NoteItem[]>('/api/notes/reorder/bulk', {
        method: 'PUT',
        body: JSON.stringify(orders),
      })
      return result
    } catch (e: any) {
      console.warn('[Reorder] 排序同步失败', e)
      throw e
    }
  },
}

// ===== 分类 API =====
export interface CategoryItem {
  id: number
  user_id: number
  name: string
  icon: string
  color: string
  sort_order: number
  is_builtin: boolean
  created_at: string | null
}

export const categoryApi = {
  list: () => onlineRequest<CategoryItem[]>('/api/categories/'),

  create: async (data: { name: string; icon?: string; color?: string }) => {
    return onlineRequest<CategoryItem>('/api/categories/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  update: async (id: number, data: Partial<CategoryItem>) => {
    return onlineRequest<CategoryItem>(`/api/categories/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  },

  delete: async (id: number) => {
    return onlineRequest<void>(`/api/categories/${id}`, { method: 'DELETE' })
  },
}

// ===== 用户设置 API =====
export interface UserSettings {
  weather_enabled: boolean
  extras: Record<string, any>
}

export const settingsApi = {
  get: () => onlineRequest<UserSettings>('/api/settings/'),

  update: async (data: Partial<UserSettings>) => {
    return onlineRequest<UserSettings>('/api/settings/', {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  },
}

// ===== 认证 API =====
export const authApi = {
  register: (data: { username: string; password: string }) =>
    request<{ access_token: string; token_type: string; user: any }>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  login: (data: { username: string; password: string }) =>
    request<{ access_token: string; token_type: string; user: any }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  getMe: () => request<any>('/api/auth/me'),
  updateQWeatherKey: (qweather_api_key: string) =>
    request<{ message: string }>('/api/auth/qweather-key', {
      method: 'PUT',
      body: JSON.stringify({ qweather_api_key }),
    }),
}

// ===== WebSocket 实时连接 =====
type WSCallback = (type: string, data: any) => void

export function connectWebSocket(onMessage: WSCallback): WebSocket | null {
  if (!isOnline()) return null

  const isElectron = !!(window as any).electronAPI?.isElectron
  const isCapacitor = typeof (window as any).Capacitor !== 'undefined'
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = import.meta.env.PROD
    ? isElectron
      ? 'ws://localhost:8000/ws'
      : isCapacitor
        ? 'ws://192.168.3.53:8000/ws'
        : `${protocol}//${window.location.host}/ws`
    : `ws://${window.location.hostname}:8000/ws`

  const ws = new WebSocket(wsUrl)

  ws.onopen = () => console.log('[WS] 已连接')
  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data)
      onMessage(msg.type, msg.data)
    } catch (e) {
      console.warn('[WS] 消息解析失败:', e)
    }
  }
  ws.onclose = () => console.log('[WS] 已断开')
  ws.onerror = () => {}

  return ws
}
