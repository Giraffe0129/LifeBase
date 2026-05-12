<script setup lang="ts">
import { ref, computed } from 'vue'
import { marked } from 'marked'
import { useAppStore } from '@/stores/useAppStore'
import { noteApi, categoryApi } from '@/api'
import { icons } from '@/utils/icons'

const store = useAppStore()

const activeCategoryId = ref<number | 'all'>('all')
const showAddModal = ref(false)
const showDetailModal = ref(false)
const showCatModal = ref(false)
const showEditCatModal = ref(false)
const detailNote = ref<any>(null)
const newNote = ref({ title: '', content: '', tags: '', category: 'life', category_id: null as number | null })
const submitting = ref(false)
const catForm = ref({ name: '', icon: 'penSquare', color: '#5D7052' })
const editCatForm = ref({ id: 0, name: '', icon: 'penSquare', color: '#5D7052' })
const catLoading = ref(false)

// Drag
const dragIndex = ref<number | null>(null)
const dragOverIndex = ref<number | null>(null)
function onDragStart(i: number) { dragIndex.value = i }
function onDragOver(e: DragEvent, i: number) { e.preventDefault(); dragOverIndex.value = i }
function onDragEnd() {
  if (dragIndex.value === null || dragOverIndex.value === null) return
  if (dragIndex.value === dragOverIndex.value) { resetDrag(); return }
  const items = [...filteredNotes.value]
  const [moved] = items.splice(dragIndex.value, 1)
  items.splice(dragOverIndex.value, 0, moved)
  const orders = items.map((item, idx) => ({ id: item.id, sort_order: idx }))
  const ids = new Set(items.map(i => i.id))
  store.notes = [...items, ...store.notes.filter(n => !ids.has(n.id))]
  noteApi.reorder(orders).catch(() => {})
  resetDrag()
}
function resetDrag() { dragIndex.value = null; dragOverIndex.value = null }

const filteredNotes = computed(() => {
  if (activeCategoryId.value === 'all') return store.notes
  return store.notes.filter(n => n.category_id === activeCategoryId.value)
})
const currentCategory = computed(() => {
  if (activeCategoryId.value === 'all') return null
  return store.getCategory(activeCategoryId.value as number)
})

function getCatName(id: number | null): string {
  if (!id) return '未分类'
  const c = store.getCategory(id)
  return c ? c.name : '未分类'
}
function getCatIconHtmlById(id: number | null): string {
  if (!id) return ''
  const c = store.getCategory(id)
  if (!c) return ''
  const svg = (icons.category as Record<string, string>)[c.icon]
  return svg || c.icon
}
function getCatColor(id: number | null): string {
  if (!id) return 'var(--muted-foreground)'
  const c = store.getCategory(id)
  return c?.color || 'var(--muted-foreground)'
}
function renderMarkdown(text: string): string {
  if (!text) return ''
  return marked.parse(text, { breaks: true }) as string
}

function openAddModal() {
  if (activeCategoryId.value !== 'all') {
    const cat = store.getCategory(activeCategoryId.value as number)
    if (cat) { newNote.value.category_id = cat.id; newNote.value.category = cat.is_builtin ? (cat.name === '生活碎片' ? 'life' : 'knowledge') : 'custom' }
  } else { newNote.value.category_id = null; newNote.value.category = 'life' }
  showAddModal.value = true
}

async function addNote() {
  if (!newNote.value.title.trim()) return; submitting.value = true
  try {
    const data: any = { title: newNote.value.title.trim(), content: newNote.value.content.trim(), tags: newNote.value.tags.trim() }
    if (newNote.value.category_id) { data.category_id = newNote.value.category_id; data.category = 'custom' }
    else data.category = 'life'
    const result = await noteApi.create(data)
    store.notes.push(result)
    newNote.value = { title: '', content: '', tags: '', category: 'life', category_id: null }
    showAddModal.value = false
  } catch (e: any) { alert(e.message || '创建失败') }
  finally { submitting.value = false }
}
async function deleteNote(id: number) { if (!confirm('确定删除？')) return; try { await noteApi.delete(id); store.notes = store.notes.filter(n => n.id !== id) } catch (e: any) { alert(e.message || '删除失败') } }
async function toggleFavorite(note: any) { try { const updated = await noteApi.update(note.id, { is_favorite: !note.is_favorite }); Object.assign(note, updated) } catch (e: any) { alert(e.message || '更新失败') } }
function viewDetail(note: any) { detailNote.value = note; showDetailModal.value = true }

async function addCategory() {
  if (!catForm.value.name.trim()) return; catLoading.value = true
  try {
    await categoryApi.create({ name: catForm.value.name.trim(), icon: catForm.value.icon, color: catForm.value.color })
    await store.fetchCategories(); catForm.value = { name: '', icon: 'penSquare', color: '#5D7052' }; showCatModal.value = false
  } catch (e: any) { alert(e.message || '创建分类失败') }
  finally { catLoading.value = false }
}
function openEditCat(cat: any) { editCatForm.value = { id: cat.id, name: cat.name, icon: cat.icon, color: cat.color }; showEditCatModal.value = true }
async function updateCategory() {
  if (!editCatForm.value.name.trim()) return; catLoading.value = true
  try { await categoryApi.update(editCatForm.value.id, { name: editCatForm.value.name.trim(), icon: editCatForm.value.icon, color: editCatForm.value.color }); await store.fetchCategories(); showEditCatModal.value = false }
  catch (e: any) { alert(e.message || '更新分类失败') }
  finally { catLoading.value = false }
}
async function deleteCategory(id: number) {
  if (!confirm('确定删除此分类？该分类下的笔记将变为"未分类"')) return
  try { await categoryApi.delete(id); await store.fetchCategories(); if (activeCategoryId.value === id) activeCategoryId.value = 'all' }
  catch (e: any) { alert(e.message || '删除分类失败') }
}

const colorOptions = ['#5D7052', '#C18C5D', '#A85448', '#D4A87D', '#78786C', '#8DA382', '#4A4A40', '#E6DCCD']
const catIcons = ['penSquare', 'sparkles', 'lightbulb', 'target', 'palette', 'music', 'cookingPot', 'globe', 'monitor', 'bookMarked', 'film', 'home', 'heart', 'feather', 'smile', 'camera', 'shoppingCart', 'dumbbell', 'wallet', 'gift']

function getCatIconHtml(iconName: string): string {
  const svg = (icons.category as Record<string, string>)[iconName]
  return svg || iconName
}
</script>

<template>
  <div>
    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px; flex-wrap: wrap;">
      <div class="claude-tabs">
        <button class="claude-tab" :class="{ active: activeCategoryId === 'all' }" @click="activeCategoryId = 'all'">
          <span v-html="icons.list" style="width:16px;height:16px;"></span> 全部
        </button>
        <button v-for="cat in store.categories" :key="cat.id" class="claude-tab"
          :class="{ active: activeCategoryId === cat.id }"
          @click="activeCategoryId = cat.id" @contextmenu.prevent="openEditCat(cat)">
          <span v-if="getCatIconHtml(cat.icon).startsWith('<')" v-html="getCatIconHtml(cat.icon)" style="width:18px;height:18px;display:inline-block;vertical-align:middle;"></span>
          <template v-else>{{ cat.icon }}</template>
          {{ cat.name }}
        </button>
      </div>
      <button class="btn btn-sm btn-ghost" @click="showCatModal = true" title="添加分类" style="font-size: 20px; width: 38px; height: 38px; padding: 0; border-radius: 50%; border: 1.5px dashed var(--border); display: inline-flex; align-items: center; justify-content: center; color: var(--muted-foreground);">
        <span v-html="icons.plus" style="width:16px;height:16px;"></span>
      </button>
    </div>

    <div v-if="currentCategory" class="flex-center gap-8 mb-12" style="justify-content: flex-start;">
      <span v-html="getCatIconHtmlById(currentCategory.id)" style="width:20px;height:20px;display:inline-flex;align-items:center;"></span>
      <span style="font-family: var(--font-heading); font-weight: 700; font-size: 15px;">{{ currentCategory.name }}</span>
      <button v-if="!currentCategory.is_builtin" class="btn btn-sm btn-ghost" @click="openEditCat(currentCategory)" style="font-size: 12px;">
        <span v-html="icons.edit" style="width:14px;height:14px;"></span>
      </button>
    </div>

    <transition-group name="list" tag="div">
      <div v-for="(note, index) in filteredNotes" :key="note.id"
        class="claude-card" :class="{ dragging: dragIndex === index }"
        draggable="true" @dragstart="onDragStart(index)" @dragover="onDragOver($event, index)"
        @dragend="onDragEnd" @dragleave="dragOverIndex = null"
        style="display: flex; align-items: flex-start; gap: 12px;">
        <span class="drag-handle" style="margin-top: 4px;" v-html="icons.grip" title="拖拽排序"></span>
        <div style="flex: 1; min-width: 0;" @click="viewDetail(note)">
          <div style="display: flex; align-items: center; gap: 8px">
            <h3 style="font-family: var(--font-heading); font-size: 15px; font-weight: 700; overflow: hidden; text-overflow: ellipsis; white-space: nowrap">{{ note.title }}</h3>
            <span v-if="note.is_favorite" v-html="icons.star" style="color: var(--secondary); width:16px;height:16px;flex-shrink:0;"></span>
          </div>
          <div style="display: flex; gap: 6px; margin-top: 6px; flex-wrap: wrap; align-items: center;">
            <span class="category-badge" v-if="note.category_id" :style="{ background: getCatColor(note.category_id)+'20', color: getCatColor(note.category_id) }">
              <span v-if="getCatIconHtmlById(note.category_id).startsWith('<')" v-html="getCatIconHtmlById(note.category_id)" style="width:14px;height:14px;display:inline-block;vertical-align:middle;"></span>
              <template v-else>{{ getCatIconHtmlById(note.category_id) }}</template>
              {{ getCatName(note.category_id) }}
            </span>
            <span v-if="note.tags" v-for="tag in note.tags.split(',').filter(Boolean)" :key="tag" class="tag" style="background: var(--muted); color: var(--muted-foreground);">
              <span v-html="icons.hash" style="width:12px;height:12px;"></span>{{ tag.trim() }}
            </span>
          </div>
          <div class="text-sm text-secondary mt-8" style="overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">
            {{ note.content?.replace(/[#*`>\[\]]/g, '').substring(0, 120) }}
          </div>
        </div>
        <button class="btn btn-sm btn-ghost" @click.stop="deleteNote(note.id)" style="flex-shrink: 0; margin-top: 4px;" v-html="icons.trash"></button>
      </div>
    </transition-group>

    <div v-if="filteredNotes.length === 0" class="empty-state">
      <div class="empty-icon" v-html="icons.notes"></div>
      <p>还没有记录</p>
    </div>

    <div class="fab-area">
      <button class="btn btn-primary btn-round fab-btn" @click="openAddModal()">
        <span v-html="icons.plus" style="width:20px;height:20px;"></span> 新记录
      </button>
    </div>

    <!-- Add Note Modal -->
    <transition name="fade">
      <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
        <div class="modal-window">
          <div class="modal-header"><h3>新建记录</h3><button class="btn btn-sm btn-ghost" @click="showAddModal = false" v-html="icons.close"></button></div>
          <div class="input-group"><label>标题</label><input v-model="newNote.title" class="input-field" placeholder="给你的记录取个名字" /></div>
          <div class="input-group"><label>内容（支持 Markdown）</label><textarea v-model="newNote.content" class="input-field" placeholder="记录你想保存的任何内容..." rows="6"></textarea></div>
          <div style="display: flex; gap: 8px">
            <div class="input-group" style="flex: 1"><label>标签（逗号分隔）</label><input v-model="newNote.tags" class="input-field" placeholder="例如：读书,感悟" /></div>
            <div class="input-group" style="flex: 1"><label>分类</label>
              <select v-model="newNote.category_id" class="input-field">
                <option :value="null">未分类</option>
                <option v-for="cat in store.categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
              </select></div>
          </div>
          <button class="btn btn-primary btn-block mt-12" :disabled="!newNote.title.trim() || submitting" @click="addNote">{{ submitting ? '保存中...' : '保存记录' }}</button>
        </div>
      </div>
    </transition>

    <!-- Detail Modal -->
    <transition name="fade">
      <div v-if="showDetailModal && detailNote" class="modal-overlay" @click.self="showDetailModal = false">
        <div class="modal-window">
          <div class="modal-header">
            <div style="display: flex; align-items: center; gap: 8px"><h3>{{ detailNote.title }}</h3>
              <button class="btn btn-sm btn-icon" @click="toggleFavorite(detailNote)" style="background:none;border:none;cursor:pointer;padding:0;" v-html="detailNote.is_favorite ? icons.star : ''"></button>
            </div>
            <button class="btn btn-sm btn-ghost" @click="showDetailModal = false" v-html="icons.close"></button>
          </div>
          <div style="display: flex; gap: 6px; margin-bottom: 12px; flex-wrap: wrap; align-items: center;">
            <span class="category-badge" v-if="detailNote.category_id" :style="{ background: getCatColor(detailNote.category_id)+'20', color: getCatColor(detailNote.category_id) }">
              <span v-if="getCatIconHtmlById(detailNote.category_id).startsWith('<')" v-html="getCatIconHtmlById(detailNote.category_id)" style="width:14px;height:14px;display:inline-block;vertical-align:middle;"></span>
              <template v-else>{{ getCatIconHtmlById(detailNote.category_id) }}</template>
              {{ getCatName(detailNote.category_id) }}
            </span>
            <span v-if="detailNote.tags" v-for="tag in detailNote.tags.split(',').filter(Boolean)" :key="tag" class="tag" style="background: var(--muted); color: var(--muted-foreground);">#{{ tag.trim() }}</span>
          </div>
          <div class="markdown-preview" v-html="renderMarkdown(detailNote.content)"></div>
          <div class="text-sm text-secondary mt-16">{{ detailNote.created_at ? new Date(detailNote.created_at).toLocaleString() : '' }}</div>
          <button class="btn btn-danger btn-block mt-16" @click="deleteNote(detailNote.id); showDetailModal = false;">删除此记录</button>
        </div>
      </div>
    </transition>

    <!-- Add Category Modal -->
    <transition name="fade">
      <div v-if="showCatModal" class="modal-overlay" @click.self="showCatModal = false">
        <div class="modal-window" style="max-width: 400px;">
          <div class="modal-header"><h3>新建分类</h3><button class="btn btn-sm btn-ghost" @click="showCatModal = false" v-html="icons.close"></button></div>
          <div class="input-group"><label>分类名称</label><input v-model="catForm.name" class="input-field" placeholder="例如：每日感想" @keyup.enter="addCategory" /></div>
          <div class="input-group"><label>图标</label>
            <div style="display: flex; flex-wrap: wrap; gap: 6px;">
              <button v-for="iconName in catIcons" :key="iconName" class="btn btn-sm" :class="catForm.icon === iconName ? 'btn-primary' : 'btn-secondary'" @click="catForm.icon = iconName" style="width: 42px; height: 42px; padding: 0; display: inline-flex; align-items: center; justify-content: center;">
                <span v-html="getCatIconHtml(iconName)" style="width:20px;height:20px;color:var(--foreground);"></span>
              </button>
            </div>
          </div>
          <div class="input-group"><label>颜色</label>
            <div style="display: flex; flex-wrap: wrap; gap: 6px;">
              <button v-for="c in colorOptions" :key="c" class="btn btn-sm" :style="{ background: c, width: 36, height: 36, padding: 0, border: catForm.color === c ? '3px solid var(--foreground)' : '3px solid transparent' }" @click="catForm.color = c"></button>
            </div>
          </div>
          <div style="display: flex; gap: 8px; margin-top: 8px;">
            <button class="btn btn-secondary" style="flex:1" @click="showCatModal = false">取消</button>
            <button class="btn btn-primary" style="flex:1" :disabled="!catForm.name.trim() || catLoading" @click="addCategory">{{ catLoading ? '创建中...' : '创建' }}</button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Edit Category Modal -->
    <transition name="fade">
      <div v-if="showEditCatModal" class="modal-overlay" @click.self="showEditCatModal = false">
        <div class="modal-window" style="max-width: 400px;">
          <div class="modal-header"><h3>编辑分类</h3><button class="btn btn-sm btn-ghost" @click="showEditCatModal = false" v-html="icons.close"></button></div>
          <div class="input-group"><label>名称</label><input v-model="editCatForm.name" class="input-field" @keyup.enter="updateCategory" /></div>
          <div class="input-group"><label>图标</label>
            <div style="display: flex; flex-wrap: wrap; gap: 6px;">
              <button v-for="iconName in catIcons" :key="iconName" class="btn btn-sm" :class="editCatForm.icon === iconName ? 'btn-primary' : 'btn-secondary'" @click="editCatForm.icon = iconName" style="width: 42px; height: 42px; padding: 0; display: inline-flex; align-items: center; justify-content: center;">
                <span v-html="getCatIconHtml(iconName)" style="width:20px;height:20px;color:var(--foreground);"></span>
              </button>
            </div>
          </div>
          <div class="input-group"><label>颜色</label>
            <div style="display: flex; flex-wrap: wrap; gap: 6px;">
              <button v-for="c in colorOptions" :key="c" class="btn btn-sm" :style="{ background: c, width: 36, height: 36, padding: 0, border: editCatForm.color === c ? '3px solid var(--foreground)' : '3px solid transparent' }" @click="editCatForm.color = c"></button>
            </div>
          </div>
          <div style="display: flex; gap: 8px; margin-top: 8px;">
            <button class="btn btn-danger" @click="deleteCategory(editCatForm.id)">删除分类</button>
            <div style="flex:1; display: flex; gap: 8px;">
              <button class="btn btn-secondary" style="flex:1" @click="showEditCatModal = false">取消</button>
              <button class="btn btn-primary" style="flex:1" :disabled="!editCatForm.name.trim() || catLoading" @click="updateCategory">{{ catLoading ? '保存中...' : '保存' }}</button>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>
