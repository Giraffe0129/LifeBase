/**
 * 本地数据库层 (IndexedDB via Dexie.js)
 * 用于离线缓存，有网时作为缓存层，无网时作为主存储。
 *
 * 表结构:
 * - tasks: 任务缓存
 * - travelPlans: 出行计划缓存
 * - notes: 笔记缓存
 * - syncQueue: 离线时产生但未同步的变更队列
 * - meta: 元数据（最后同步时间等）
 */
import Dexie, { type Table } from 'dexie'
import type { TaskItem, TravelPlanItem, NoteItem } from '@/api'

/** 离线同步队列项 */
export interface SyncQueueItem {
  id?: number
  action: 'create' | 'update' | 'delete'
  entity: 'task' | 'travel_plan' | 'note'
  localId?: string
  serverId?: number
  payload: any
  timestamp: number
  synced: boolean
}

class AppDatabase extends Dexie {
  tasks!: Table<TaskItem & { _synced: boolean }, number>
  travelPlans!: Table<TravelPlanItem & { _synced: boolean }, number>
  notes!: Table<NoteItem & { _synced: boolean }, number>
  syncQueue!: Table<SyncQueueItem, number>
  meta!: Table<{ key: string; value: any }, string>

  constructor() {
    super('MyAwesomeAppDB')
    this.version(1).stores({
      tasks: 'id, title, completed, priority, _synced',
      travelPlans: 'id, title, plan_date, completed, _synced',
      notes: 'id, title, category, is_favorite, _synced',
      syncQueue: '++id, action, entity, synced, timestamp',
      meta: 'key',
    })
  }
}

export const db = new AppDatabase()

/** 元数据辅助方法 */
export async function getMeta(key: string): Promise<any | null> {
  const row = await db.meta.get(key)
  return row?.value ?? null
}

export async function setMeta(key: string, value: any) {
  await db.meta.put({ key, value })
}

/** 判断联网状态 */
export function isOnline(): boolean {
  return navigator.onLine
}
