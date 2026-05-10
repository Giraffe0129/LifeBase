<script setup lang="ts">
import { ref, computed } from 'vue'
import { marked } from 'marked'
import { useAppStore } from '@/stores/useAppStore'
import { noteApi } from '@/api'

const store = useAppStore()

const activeCategory = ref('all')
const showAddModal = ref(false)
const showDetailModal = ref(false)
const detailNote = ref<any>(null)
const newNote = ref({ title: '', content: '', tags: '', category: 'life' })
const submitting = ref(false)

const filteredNotes = computed(() => {
  if (activeCategory.value === 'all') return store.notes
  return store.notes.filter(n => n.category === activeCategory.value)
})

function renderMarkdown(text: string): string {
  if (!text) return ''
  return marked.parse(text, { breaks: true }) as string
}

async function addNote() {
  if (!newNote.value.title.trim()) return
  submitting.value = true
  try {
    await noteApi.create({
      title: newNote.value.title.trim(),
      content: newNote.value.content.trim(),
      tags: newNote.value.tags.trim(),
      category: newNote.value.category,
    })
    newNote.value = { title: '', content: '', tags: '', category: 'life' }
    showAddModal.value = false
  } catch (e: any) {
    alert('创建失败: ' + e.message)
  } finally {
    submitting.value = false
  }
}

async function deleteNote(id: number) {
  if (!confirm('确定删除此记录？')) return
  try {
    await noteApi.delete(id)
  } catch (e: any) {
    alert('删除失败: ' + e.message)
  }
}

async function toggleFavorite(note: any) {
  try {
    await noteApi.update(note.id, { is_favorite: !note.is_favorite })
  } catch (e: any) {
    alert('更新失败: ' + e.message)
  }
}

function viewDetail(note: any) {
  detailNote.value = note
  showDetailModal.value = true
}
</script>

<template>
  <div>
    <!-- 分类切换 -->
    <div class="tab-bar">
      <button
        class="tab-item"
        :class="{ active: activeCategory === 'all' }"
        @click="activeCategory = 'all'"
      >全部</button>
      <button
        class="tab-item"
        :class="{ active: activeCategory === 'knowledge' }"
        @click="activeCategory = 'knowledge'"
      >📖 知识点</button>
      <button
        class="tab-item"
        :class="{ active: activeCategory === 'life' }"
        @click="activeCategory = 'life'"
      >✨ 生活碎片</button>
    </div>

    <div v-if="filteredNotes.length === 0" class="empty-state">
      <div class="empty-icon">📝</div>
      <p>还没有记录，记录你的知识和生活碎片吧</p>
    </div>

    <div v-for="note in filteredNotes" :key="note.id" class="card" @click="viewDetail(note)" style="cursor: pointer">
      <div style="display: flex; justify-content: space-between; align-items: flex-start">
        <div style="flex: 1; min-width: 0">
          <div style="display: flex; align-items: center; gap: 6px">
            <h3 style="font-size: 16px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap">
              {{ note.title }}
            </h3>
            <span v-if="note.is_favorite" style="color: #f59e0b">⭐</span>
          </div>
          <div style="display: flex; gap: 6px; margin-top: 4px">
            <span class="tag" :style="{ background: note.category === 'knowledge' ? '#dbeafe' : '#fce7f3', color: note.category === 'knowledge' ? '#1e40af' : '#9d174d' }">
              {{ note.category === 'knowledge' ? '知识点' : '生活碎片' }}
            </span>
            <span v-if="note.tags" v-for="tag in note.tags.split(',').filter(Boolean)" :key="tag" class="tag" style="background: #f1f5f9; color: #475569">
              #{{ tag.trim() }}
            </span>
          </div>
          <div class="text-sm text-secondary" style="margin-top: 4px">
            {{ note.created_at ? new Date(note.created_at).toLocaleString() : '' }}
          </div>
          <!-- 内容预览 -->
          <div class="text-sm text-secondary" style="margin-top: 6px; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">
            {{ note.content?.replace(/[#*`>\[\]]/g, '').substring(0, 100) }}
          </div>
        </div>
        <button class="btn btn-sm btn-danger" @click.stop="deleteNote(note.id)" style="flex-shrink: 0; margin-left: 8px">删除</button>
      </div>
    </div>

    <!-- 添加按钮 -->
    <div style="position: fixed; bottom: 80px; left: 50%; transform: translateX(-50%); z-index: 50; max-width: 480px; width: calc(100% - 32px)">
      <button class="btn btn-primary btn-block" @click="showAddModal = true" style="padding: 14px; border-radius: var(--radius); box-shadow: var(--shadow-lg)">
        + 记录新内容
      </button>
    </div>

    <!-- 新增笔记弹窗 -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>新建记录</h3>
          <button class="modal-close" @click="showAddModal = false">✕</button>
        </div>

        <div class="input-group">
          <label>标题 *</label>
          <input v-model="newNote.title" class="input-field" placeholder="给你的记录取个名字" />
        </div>

        <div class="input-group">
          <label>内容（支持 Markdown）</label>
          <textarea v-model="newNote.content" class="input-field" placeholder="记录你想保存的任何内容..." rows="6"></textarea>
        </div>

        <div style="display: flex; gap: 8px">
          <div class="input-group" style="flex: 1">
            <label>标签（逗号分隔）</label>
            <input v-model="newNote.tags" class="input-field" placeholder="例如：读书,感悟" />
          </div>
          <div class="input-group" style="flex: 1">
            <label>分类</label>
            <select v-model="newNote.category" class="input-field">
              <option value="life">✨ 生活碎片</option>
              <option value="knowledge">📖 知识点</option>
            </select>
          </div>
        </div>

        <button class="btn btn-primary btn-block mt-12" :disabled="!newNote.title.trim() || submitting" @click="addNote">
          {{ submitting ? '保存中...' : '保存记录' }}
        </button>
      </div>
    </div>

    <!-- 笔记详情弹窗 -->
    <div v-if="showDetailModal && detailNote" class="modal-overlay" @click.self="showDetailModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <div style="display: flex; align-items: center; gap: 8px">
            <h3>{{ detailNote.title }}</h3>
            <button
              class="btn btn-sm"
              :style="{ background: 'none', fontSize: '20px' }"
              @click="toggleFavorite(detailNote)"
            >
              {{ detailNote.is_favorite ? '⭐' : '☆' }}
            </button>
          </div>
          <button class="modal-close" @click="showDetailModal = false">✕</button>
        </div>

        <div style="display: flex; gap: 6px; margin-bottom: 12px">
          <span class="tag" :style="{ background: detailNote.category === 'knowledge' ? '#dbeafe' : '#fce7f3', color: detailNote.category === 'knowledge' ? '#1e40af' : '#9d174d' }">
            {{ detailNote.category === 'knowledge' ? '知识点' : '生活碎片' }}
          </span>
          <span v-if="detailNote.tags" v-for="tag in detailNote.tags.split(',').filter(Boolean)" :key="tag" class="tag" style="background: #f1f5f9; color: #475569">
            #{{ tag.trim() }}
          </span>
        </div>

        <div class="markdown-preview" v-html="renderMarkdown(detailNote.content)"></div>

        <div class="text-sm text-secondary" style="margin-top: 16px">
          创建于 {{ detailNote.created_at ? new Date(detailNote.created_at).toLocaleString() : '' }}
        </div>

        <button class="btn btn-danger btn-block mt-12" @click="deleteNote(detailNote.id); showDetailModal = false">
          删除此记录
        </button>
      </div>
    </div>
  </div>
</template>
