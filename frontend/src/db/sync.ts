/**
 * 同步引擎 - 离线/在线自动切换，变更队列自动同步。
 *
 * 工作原理：
 * 1. 在线时：每次 API 操作成功后，同步将数据写入 IndexedDB 作为缓存。
 * 2. 离线时：所有变更写入 IndexedDB 的 syncQueue 表。
 * 3. 恢复在线时：自动推送队列中的变更到服务器，然后拉取全量数据刷新本地。
 */
import { db, isOnline, getMeta, setMeta } from './localDB'
import { taskApi, travelPlanApi, noteApi } from '@/api'
import type { TaskItem, TravelPlanItem, NoteItem } from '@/api'
import { useAppStore } from '@/stores/useAppStore'

/** 监听网络状态变化 */
let listeners: (() => void)[] = []

export function onNetworkChange(callback: () => void) {
  listeners.push(callback)
  return () => {
    listeners = listeners.filter(l => l !== callback)
  }
}

function notifyListeners() {
  listeners.forEach(l => l())
}

// 注册网络事件监听
if (typeof window !== 'undefined') {
  window.addEventListener('online', () => {
    console.log('[Sync] 网络已恢复，开始同步...')
    notifyListeners()
    flushSyncQueue().then(() => fullSync())
  })
  window.addEventListener('offline', () => {
    console.log('[Sync] 网络已断开，切换到离线模式')
    notifyListeners()
  })
}

/**
 * 当在线时，API 操作完成后顺便更新本地缓存。
 */
export async function updateLocalCache(entity: string, data: any) {
  if (entity === 'task') {
    const withFlag = { ...data, _synced: true }
    if (data.id) await db.tasks.put(withFlag)
  } else if (entity === 'travel_plan') {
    const withFlag = { ...data, _synced: true }
    if (data.id) await db.travelPlans.put(withFlag)
  } else if (entity === 'note') {
    const withFlag = { ...data, _synced: true }
    if (data.id) await db.notes.put(withFlag)
  }
}

export async function removeLocalCache(entity: string, id: number) {
  if (entity === 'task') await db.tasks.delete(id)
  else if (entity === 'travel_plan') await db.travelPlans.delete(id)
  else if (entity === 'note') await db.notes.delete(id)
}

/**
 * 离线操作入队列
 */
export async function enqueueSync(
  action: 'create' | 'update' | 'delete',
  entity: 'task' | 'travel_plan' | 'note',
  payload: any,
  localId?: string,
) {
  await db.syncQueue.add({
    action,
    entity,
    payload,
    localId,
    timestamp: Date.now(),
    synced: 0,
  })
}

/**
 * 推送离线队列到服务器
 */
export async function flushSyncQueue() {
  const queue = await db.syncQueue
    .where('synced')
    .equals(0)
    .sortBy('timestamp')

  for (const item of queue) {
    try {
      const api = entityToApi(item.entity)
      if (!api) continue

      if (item.action === 'delete') {
        await api.delete(item.payload.id)
      } else if (item.action === 'update') {
        await api.update(item.payload.id, item.payload)
      } else if (item.action === 'create') {
        const result = await api.create(item.payload)
        // 创建成功后，更新本地缓存的 ID 映射
        await updateLocalCache(item.entity, result)
      }

      // 标记为已同步
      if (item.id !== undefined) {
        await db.syncQueue.update(item.id, { synced: 1 })
      }

      console.log(`[Sync] 同步成功: ${item.action} ${item.entity} #${item.payload.id || ''}`)
    } catch (err) {
      console.warn(`[Sync] 同步失败 (稍后重试): ${item.action} ${item.entity}`, err)
      // 失败则保留在队列中，下次重试
      break
    }
  }

  // 清理已同步的记录（保留最近 100 条以备案）
  const syncedItems = await db.syncQueue
    .where('synced')
    .equals(1)
    .count()

  if (syncedItems > 100) {
    const toDelete = await db.syncQueue
      .where('synced')
      .equals(1)
      .limit(syncedItems - 50)
      .toArray()
    for (const item of toDelete) {
      if (item.id !== undefined) await db.syncQueue.delete(item.id)
    }
  }
}

/**
 * 全量同步：从服务器拉取最新数据，刷新本地缓存和 Pinia 状态。
 */
export async function fullSync() {
  if (!isOnline()) return

  const store = useAppStore()

  try {
    const [tasks, plans, notes] = await Promise.all([
      taskApi.list(),
      travelPlanApi.list(),
      noteApi.list(),
    ])

    // 更新本地缓存
    await db.tasks.clear()
    for (const t of tasks) await db.tasks.put({ ...t, _synced: true })

    await db.travelPlans.clear()
    for (const p of plans) await db.travelPlans.put({ ...p, _synced: true })

    await db.notes.clear()
    for (const n of notes) await db.notes.put({ ...n, _synced: true })

    // 更新 Pinia 状态
    store.tasks = tasks
    store.travelPlans = plans
    store.notes = notes

    // 记录最后同步时间
    await setMeta('lastSyncAt', new Date().toISOString())

    console.log('[Sync] 全量同步完成')
  } catch (err) {
    console.warn('[Sync] 全量同步失败:', err)
  }
}

/**
 * 从本地缓存加载数据（离线时使用）
 */
export async function loadFromLocalCache() {
  const store = useAppStore()

  const [tasks, plans, notes] = await Promise.all([
    db.tasks.toArray(),
    db.travelPlans.toArray(),
    db.notes.toArray(),
  ])

  store.tasks = tasks
  store.travelPlans = plans
  store.notes = notes

  console.log('[Sync] 已从本地缓存加载数据')
}

function entityToApi(entity: string) {
  switch (entity) {
    case 'task': return taskApi
    case 'travel_plan': return travelPlanApi
    case 'note': return noteApi
    default: return null
  }
}
