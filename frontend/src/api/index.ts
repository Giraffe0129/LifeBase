/**
 * API 客户端 - 统一封装后端 RESTful 接口和 WebSocket
 */

const BASE_URL = import.meta.env.PROD ? '' : ''

/** 通用请求封装 */
async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (res.status === 204) return undefined as T
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: '请求失败' }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

// ===== 任务 API =====
export interface TaskItem {
  id: number
  title: string
  description: string
  completed: boolean
  priority: number
  created_at: string | null
  updated_at: string | null
}

export const taskApi = {
  list: () => request<TaskItem[]>('/api/tasks/'),
  create: (data: { title: string; description?: string; priority?: number }) =>
    request<TaskItem>('/api/tasks/', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: number, data: Partial<TaskItem>) =>
    request<TaskItem>(`/api/tasks/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id: number) =>
    request<void>(`/api/tasks/${id}`, { method: 'DELETE' }),
}

// ===== 出行计划 API =====
export interface TravelPlanItem {
  id: number
  title: string
  destination: string
  plan_date: string
  start_time: string
  notes: string
  need_umbrella: boolean
  weather_tip: string
  temperature: string
  completed: boolean
  created_at: string | null
  updated_at: string | null
}

export const travelPlanApi = {
  list: () => request<TravelPlanItem[]>('/api/travel-plans/'),
  create: (data: { title: string; destination?: string; plan_date?: string; start_time?: string; notes?: string }) =>
    request<TravelPlanItem>('/api/travel-plans/', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: number, data: Partial<TravelPlanItem>) =>
    request<TravelPlanItem>(`/api/travel-plans/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id: number) =>
    request<void>(`/api/travel-plans/${id}`, { method: 'DELETE' }),
}

// ===== 笔记 API =====
export interface NoteItem {
  id: number
  title: string
  content: string
  tags: string
  is_favorite: boolean
  category: string
  created_at: string | null
  updated_at: string | null
}

export const noteApi = {
  list: (category?: string) =>
    request<NoteItem[]>(`/api/notes/?${category ? `category=${category}` : ''}`),
  create: (data: { title: string; content?: string; tags?: string; category?: string }) =>
    request<NoteItem>('/api/notes/', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: number, data: Partial<NoteItem>) =>
    request<NoteItem>(`/api/notes/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id: number) =>
    request<void>(`/api/notes/${id}`, { method: 'DELETE' }),
}

// ===== WebSocket 实时连接 =====
type WSCallback = (type: string, data: any) => void

export function connectWebSocket(onMessage: WSCallback): WebSocket {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = import.meta.env.PROD
    ? `${protocol}//${window.location.host}/ws`
    : `ws://localhost:8000/ws`

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
  ws.onclose = () => {
    console.log('[WS] 已断开，5秒后重连...')
    setTimeout(() => connectWebSocket(onMessage), 5000)
  }
  ws.onerror = (e) => console.warn('[WS] 错误:', e)

  return ws
}
