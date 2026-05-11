/**
 * API 客户端 - 统一封装后端 RESTful 接口和 WebSocket
 *
 * 在线时：直接调用服务器 API
 * 离线时：操作写入本地 IndexedDB 并加入同步队列
 */
import { isOnline } from '@/db/localDB'
import { updateLocalCache, removeLocalCache, enqueueSync } from '@/db/sync'

const BASE_URL = import.meta.env.PROD ? '' : ''

/** 获取带认证头的请求配置（直接从 localStorage 读取，避免对 Pinia 的依赖） */
function authHeaders(): Record<string, string> {
  const token = localStorage.getItem('auth_token')
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`
  return headers
}

/** 在线请求封装 */
async function request<T>(url: string, options?: RequestInit): Promise<T> {
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

  create: async (data: { title: string; description?: string; priority?: number }) => {
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

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = import.meta.env.PROD
    ? `${protocol}//${window.location.host}/ws`
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
