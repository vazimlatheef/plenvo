<template>
  <div class="app-page calendar-page">
    <div class="calendar-top">
      <div class="app-page-header">
        <h1>Calendar</h1>
      </div>
      <div class="mode-toggle" role="tablist" aria-label="Calendar view mode">
        <button
          type="button"
          role="tab"
          :aria-selected="mode === 'list'"
          class="mode-btn"
          :class="{ 'mode-btn--active': mode === 'list' }"
          @click="mode = 'list'"
        >
          <List :size="16" :stroke-width="1.75" />
          List
        </button>
        <button
          type="button"
          role="tab"
          :aria-selected="mode === 'calendar'"
          class="mode-btn"
          :class="{ 'mode-btn--active': mode === 'calendar' }"
          @click="mode = 'calendar'"
        >
          <CalendarDays :size="16" :stroke-width="1.75" />
          Calendar
        </button>
      </div>
    </div>

    <div class="month-nav">
      <button type="button" class="nav-icon-btn" aria-label="Previous month" @click="shiftMonth(-1)">
        <ChevronLeft :size="18" :stroke-width="1.75" />
      </button>
      <h2 class="month-label">{{ monthLabel }}</h2>
      <button type="button" class="nav-icon-btn" aria-label="Next month" @click="shiftMonth(1)">
        <ChevronRight :size="18" :stroke-width="1.75" />
      </button>
      <button type="button" class="btn-outline btn-today" @click="goToday">Today</button>
    </div>

    <p v-if="loading" class="muted-line">Loading tasks…</p>
    <p v-else-if="error" class="error-line">{{ error }}</p>

    <!-- List mode -->
    <div v-else-if="mode === 'list'">
      <div v-if="!dateGroups.length" class="empty-panel">
        <p>No tasks with due dates in {{ monthLabel }}.</p>
      </div>
      <section v-for="group in dateGroups" :key="group.key">
        <div class="group-label">
          <span class="date-pill" :class="{ 'date-pill--today': group.isToday, 'date-pill--overdue': group.isOverdue }">
            {{ group.label }}
          </span>
          <span class="count">({{ group.tasks.length }})</span>
        </div>
        <ul class="dense-list">
          <li
            v-for="task in group.tasks"
            :key="task.id"
            class="dense-row"
            :class="{ 'dense-row--flash': flashId === task.id }"
          >
            <span
              class="avatar"
              :class="`avatar-tone-${avatarTone(assigneeSeed(task))}`"
              :title="assigneeName(task)"
            >
              {{ getInitials(assigneeName(task)) }}
            </span>
            <div class="dense-row__meta">
              <button type="button" class="dense-row__title" @click="openEdit(task)">
                {{ task.title }}
              </button>
              <span v-if="projectLabel(task.project_id)" class="project-tag">
                {{ projectLabel(task.project_id) }}
              </span>
            </div>
            <span class="dense-row__due">{{ formatShortDate(task.due_date) }}</span>
            <div class="dense-row__actions" />
            <span class="status-pill" :data-s="task.status">{{ statusLabel(task.status) }}</span>
          </li>
        </ul>
      </section>
    </div>

    <!-- Calendar mode -->
    <div v-else class="cal-layout">
      <div class="cal-grid" role="grid" :aria-label="monthLabel">
        <div v-for="dow in weekdays" :key="dow" class="cal-dow">{{ dow }}</div>
        <button
          v-for="cell in monthCells"
          :key="cell.key"
          type="button"
          class="cal-cell"
          :class="{
            'cal-cell--outside': !cell.inMonth,
            'cal-cell--today': cell.isToday,
            'cal-cell--selected': cell.iso === selectedDate,
            'cal-cell--has': cell.tasks.length > 0,
          }"
          @click="selectDay(cell.iso)"
        >
          <span class="cal-daynum">{{ cell.day }}</span>
          <ul class="cal-task-chips">
            <li
              v-for="task in cell.tasks.slice(0, 3)"
              :key="task.id"
              class="cal-chip"
              :data-s="task.status"
              :title="task.title"
              @click.stop="openEdit(task)"
            >
              <span
                class="cal-chip-avatar avatar"
                :class="`avatar-tone-${avatarTone(assigneeSeed(task))}`"
              >
                {{ getInitials(assigneeName(task)) }}
              </span>
              <span class="cal-chip-title">{{ task.title }}</span>
            </li>
            <li v-if="cell.tasks.length > 3" class="cal-more">+{{ cell.tasks.length - 3 }} more</li>
          </ul>
        </button>
      </div>

      <aside v-if="selectedDate" class="day-panel">
        <div class="day-panel-header">
          <div>
            <h3>{{ selectedDayLabel }}</h3>
            <p class="muted-line">{{ selectedDayTasks.length }} task{{ selectedDayTasks.length === 1 ? '' : 's' }}</p>
          </div>
          <button type="button" class="btn-primary btn-compact" @click="openCreate(selectedDate)">
            <Plus :size="15" :stroke-width="2" />
            Add task
          </button>
        </div>

        <div v-if="!selectedDayTasks.length" class="empty-panel day-empty">
          <p>No tasks on this day.</p>
        </div>
        <ul v-else class="dense-list">
          <li
            v-for="task in selectedDayTasks"
            :key="task.id"
            class="dense-row"
            :class="{ 'dense-row--flash': flashId === task.id }"
          >
            <span
              class="avatar"
              :class="`avatar-tone-${avatarTone(assigneeSeed(task))}`"
              :title="assigneeName(task)"
            >
              {{ getInitials(assigneeName(task)) }}
            </span>
            <div class="dense-row__meta">
              <button type="button" class="dense-row__title" @click="openEdit(task)">
                {{ task.title }}
              </button>
              <span v-if="projectLabel(task.project_id)" class="project-tag">
                {{ projectLabel(task.project_id) }}
              </span>
            </div>
            <div class="dense-row__actions" />
            <span class="status-pill" :data-s="task.status">{{ statusLabel(task.status) }}</span>
          </li>
        </ul>
      </aside>
    </div>

    <TaskEditModal
      :open="showModal"
      :mode="modalMode"
      :saving="saving"
      :error="formError"
      :assignee-options="assigneeOptions"
      :projects="projects"
      :show-project="true"
      :initial="modalInitial"
      @close="closeModal"
      @save="saveFromModal"
    />
  </div>
</template>

<script setup>
import { CalendarDays, ChevronLeft, ChevronRight, List, Plus } from '@lucide/vue'
import { computed, ref, watch } from 'vue'

import { apiJson } from '@/api/client'
import TaskEditModal from '@/components/TaskEditModal.vue'
import { user } from '@/composables/session'
import {
  buildAssigneeOptions,
  parseAssigneeKey,
  resolveAssigneeName,
  taskAssigneeKey,
} from '@/utils/assignee'
import {
  avatarTone,
  formatShortDate,
  getInitials,
  statusLabel,
} from '@/utils/ui'

const mode = ref('calendar')
const loading = ref(true)
const error = ref('')
const tasks = ref([])
const projects = ref([])
const projectsById = ref({})
const team = ref([])
const contacts = ref([])
const usersById = ref({})
const contactsById = ref({})

const cursor = ref(startOfMonth(new Date()))
const selectedDate = ref(toIsoDate(new Date()))
const flashId = ref(null)
let flashTimer = null

const showModal = ref(false)
const modalMode = ref('edit')
const editingTaskId = ref(null)
const saving = ref(false)
const formError = ref('')
const modalInitial = ref({
  title: '',
  assignee_key: null,
  due_date: '',
  status: 'pending',
  project_id: null,
})

const weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

const monthLabel = computed(() =>
  cursor.value.toLocaleDateString('en-GB', { month: 'long', year: 'numeric' }),
)

const range = computed(() => monthQueryRange(cursor.value))

const assigneeOptions = computed(() =>
  buildAssigneeOptions({
    users: team.value,
    contacts: contacts.value,
    currentUser: user.value,
  }),
)

const tasksByDate = computed(() => {
  const map = new Map()
  for (const task of tasks.value) {
    if (!task.due_date) continue
    const key = String(task.due_date).slice(0, 10)
    if (!map.has(key)) map.set(key, [])
    map.get(key).push(task)
  }
  for (const list of map.values()) {
    list.sort((a, b) => String(a.title).localeCompare(String(b.title)))
  }
  return map
})

const dateGroups = computed(() => {
  const today = toIsoDate(new Date())
  const keys = [...tasksByDate.value.keys()].sort()
  return keys.map((key) => {
    const d = parseIsoDate(key)
    const label = d.toLocaleDateString('en-GB', {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
    })
    return {
      key,
      label,
      isToday: key === today,
      isOverdue: key < today,
      tasks: tasksByDate.value.get(key) || [],
    }
  })
})

const monthCells = computed(() => {
  const { year, month } = ymd(cursor.value)
  const first = new Date(year, month, 1)
  // Monday-based index: Mon=0 … Sun=6
  const startPad = (first.getDay() + 6) % 7
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const cells = []
  const todayIso = toIsoDate(new Date())

  for (let i = 0; i < startPad; i += 1) {
    const d = new Date(year, month, 1 - (startPad - i))
    const iso = toIsoDate(d)
    cells.push({
      key: `o-${iso}`,
      iso,
      day: d.getDate(),
      inMonth: false,
      isToday: iso === todayIso,
      tasks: tasksByDate.value.get(iso) || [],
    })
  }
  for (let day = 1; day <= daysInMonth; day += 1) {
    const d = new Date(year, month, day)
    const iso = toIsoDate(d)
    cells.push({
      key: iso,
      iso,
      day,
      inMonth: true,
      isToday: iso === todayIso,
      tasks: tasksByDate.value.get(iso) || [],
    })
  }
  while (cells.length % 7 !== 0) {
    const last = cells[cells.length - 1]
    const d = parseIsoDate(last.iso)
    d.setDate(d.getDate() + 1)
    const iso = toIsoDate(d)
    cells.push({
      key: `o-${iso}`,
      iso,
      day: d.getDate(),
      inMonth: false,
      isToday: iso === todayIso,
      tasks: tasksByDate.value.get(iso) || [],
    })
  }
  return cells
})

const selectedDayTasks = computed(() => tasksByDate.value.get(selectedDate.value) || [])

const selectedDayLabel = computed(() => {
  if (!selectedDate.value) return ''
  return parseIsoDate(selectedDate.value).toLocaleDateString('en-GB', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  })
})

function startOfMonth(d) {
  return new Date(d.getFullYear(), d.getMonth(), 1)
}

function ymd(d) {
  return { year: d.getFullYear(), month: d.getMonth() }
}

function toIsoDate(d) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function parseIsoDate(iso) {
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, m - 1, d)
}

function monthQueryRange(monthStart) {
  const { year, month } = ymd(monthStart)
  const first = new Date(year, month, 1)
  const startPad = (first.getDay() + 6) % 7
  const gridStart = new Date(year, month, 1 - startPad)
  const last = new Date(year, month + 1, 0)
  const endPad = 6 - ((last.getDay() + 6) % 7)
  const gridEnd = new Date(last)
  gridEnd.setDate(last.getDate() + endPad)
  return { due_from: toIsoDate(gridStart), due_to: toIsoDate(gridEnd) }
}

function projectLabel(projectId) {
  if (!projectId) return ''
  return projectsById.value[projectId]?.title || `Project #${projectId}`
}

function assigneeName(task) {
  return resolveAssigneeName(task, {
    usersById: usersById.value,
    contactsById: contactsById.value,
    fallback: 'Unassigned',
  })
}

function assigneeSeed(task) {
  return task.assignee_id || task.assignee_contact_id || task.title
}

function triggerFlash(taskId) {
  flashId.value = taskId
  if (flashTimer) clearTimeout(flashTimer)
  flashTimer = setTimeout(() => {
    flashId.value = null
  }, 700)
}

function shiftMonth(delta) {
  const { year, month } = ymd(cursor.value)
  cursor.value = new Date(year, month + delta, 1)
  // Keep selection inside new month when possible
  const sel = selectedDate.value ? parseIsoDate(selectedDate.value) : null
  if (!sel || sel.getMonth() !== cursor.value.getMonth() || sel.getFullYear() !== cursor.value.getFullYear()) {
    selectedDate.value = toIsoDate(cursor.value)
  }
}

function goToday() {
  const now = new Date()
  cursor.value = startOfMonth(now)
  selectedDate.value = toIsoDate(now)
}

function selectDay(iso) {
  selectedDate.value = iso
  const d = parseIsoDate(iso)
  if (d.getMonth() !== cursor.value.getMonth() || d.getFullYear() !== cursor.value.getFullYear()) {
    cursor.value = startOfMonth(d)
  }
}

function openEdit(task) {
  modalMode.value = 'edit'
  editingTaskId.value = task.id
  modalInitial.value = {
    title: task.title || '',
    assignee_key: taskAssigneeKey(task),
    due_date: task.due_date ? String(task.due_date).slice(0, 10) : '',
    status: task.status || 'pending',
    project_id: task.project_id ?? null,
  }
  formError.value = ''
  showModal.value = true
}

function openCreate(isoDate) {
  modalMode.value = 'create'
  editingTaskId.value = null
  modalInitial.value = {
    title: '',
    assignee_key: null,
    due_date: isoDate || selectedDate.value || '',
    status: 'pending',
    project_id: null,
  }
  formError.value = ''
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editingTaskId.value = null
  formError.value = ''
}

async function saveFromModal(payload) {
  saving.value = true
  formError.value = ''
  try {
    const { assignee_id, assignee_contact_id } = parseAssigneeKey(payload.assignee_key)
    if (modalMode.value === 'create') {
      const body = {
        title: payload.title,
        status: payload.status,
        due_date: payload.due_date,
        project_id: payload.project_id,
      }
      if (assignee_id) body.assignee_id = assignee_id
      if (assignee_contact_id) body.assignee_contact_id = assignee_contact_id
      const created = await apiJson('/api/v1/tasks', {
        method: 'POST',
        body: JSON.stringify(body),
      })
      upsertTask(created)
      if (created.due_date) selectedDate.value = String(created.due_date).slice(0, 10)
      triggerFlash(created.id)
    } else {
      const body = {
        title: payload.title,
        status: payload.status,
        due_date: payload.due_date,
      }
      if (!assignee_id && !assignee_contact_id) {
        body.clear_assignee = true
      } else {
        body.assignee_id = assignee_id
        body.assignee_contact_id = assignee_contact_id
      }
      const updated = await apiJson(`/api/v1/tasks/${editingTaskId.value}`, {
        method: 'PATCH',
        body: JSON.stringify(body),
      })
      upsertTask(updated)
      triggerFlash(updated.id)
    }
    closeModal()
  } catch (err) {
    console.error('[Calendar] save failed', err)
    formError.value = err.message || 'Failed to save task'
  } finally {
    saving.value = false
  }
}

function upsertTask(task) {
  const { due_from, due_to } = range.value
  const due = task.due_date ? String(task.due_date).slice(0, 10) : null
  const inRange = due && due >= due_from && due <= due_to
  const idx = tasks.value.findIndex((t) => t.id === task.id)
  if (!inRange) {
    if (idx !== -1) tasks.value = tasks.value.filter((t) => t.id !== task.id)
    return
  }
  if (idx === -1) tasks.value = [...tasks.value, task]
  else {
    const next = [...tasks.value]
    next[idx] = { ...next[idx], ...task }
    tasks.value = next
  }
}

async function loadMonth() {
  loading.value = true
  error.value = ''
  try {
    const { due_from, due_to } = range.value
    const [taskList, projectList, users, contactList] = await Promise.all([
      apiJson(`/api/v1/tasks?due_from=${due_from}&due_to=${due_to}`),
      apiJson('/api/v1/projects').catch(() => []),
      apiJson('/api/v1/users').catch(() => []),
      apiJson('/api/v1/contacts').catch(() => []),
    ])
    tasks.value = Array.isArray(taskList) ? taskList : []
    projects.value = Array.isArray(projectList) ? projectList : []
    const pMap = {}
    for (const p of projects.value) pMap[p.id] = p
    projectsById.value = pMap
    team.value = Array.isArray(users) ? users : []
    contacts.value = Array.isArray(contactList) ? contactList : []
    const uMap = {}
    for (const u of team.value) uMap[u.id] = u
    usersById.value = uMap
    const cMap = {}
    for (const c of contacts.value) cMap[c.id] = c
    contactsById.value = cMap
  } catch (err) {
    console.error('[Calendar] load failed', err)
    error.value = err.message || 'Failed to load calendar'
  } finally {
    loading.value = false
  }
}

watch(
  () => [range.value.due_from, range.value.due_to],
  () => {
    loadMonth()
  },
  { immediate: true },
)
</script>

<style scoped>
.calendar-page {
  max-width: 1100px;
}

.calendar-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 0.35rem;
}

.calendar-top .app-page-header {
  margin-bottom: 0;
}

.mode-toggle {
  display: inline-flex;
  padding: 0.2rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  gap: 0.15rem;
}

.mode-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  font-family: var(--font-body);
  font-size: 0.82rem;
  font-weight: 600;
  padding: 0.45rem 0.75rem;
  border-radius: 4px;
  cursor: pointer;
}

.mode-btn--active {
  background: var(--color-surface);
  color: var(--color-text);
  box-shadow: inset 0 0 0 1px var(--color-border);
}

.month-nav {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0.85rem 0 1.25rem;
}

.month-label {
  margin: 0;
  min-width: 10rem;
  text-align: center;
  font-family: var(--font-display);
  font-size: 1.35rem;
  font-weight: 400;
  color: var(--color-text);
}

.nav-icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-bg);
  color: var(--color-text-muted);
  cursor: pointer;
}

.nav-icon-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.btn-today {
  margin-left: 0.35rem;
  padding: 0.4rem 0.75rem;
  font-size: 0.8rem;
}

.group-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 1.1rem 0 0.45rem;
}

.date-pill {
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  padding: 0.28rem 0.55rem;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  color: var(--color-text);
  background: var(--color-bg);
}

.date-pill--today {
  border-color: rgba(196, 163, 90, 0.55);
  color: var(--color-accent);
}

.date-pill--overdue {
  border-color: rgba(248, 113, 113, 0.4);
  color: var(--color-danger);
}

.count {
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.cal-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(260px, 320px);
  gap: 1.1rem;
  align-items: start;
}

.cal-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 1px;
  background: var(--color-border);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  overflow: hidden;
}

.cal-dow {
  background: var(--color-surface);
  padding: 0.55rem 0.4rem;
  text-align: center;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.cal-cell {
  min-height: 104px;
  padding: 0.4rem 0.35rem 0.45rem;
  border: none;
  background: var(--color-bg);
  color: var(--color-text);
  text-align: left;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-family: inherit;
}

.cal-cell:hover {
  background: rgba(196, 163, 90, 0.06);
}

.cal-cell--outside {
  background: var(--color-bg-elevated);
  color: var(--color-text-muted);
  opacity: 0.72;
}

.cal-cell--today .cal-daynum {
  background: var(--color-accent);
  color: #0f1210;
}

.cal-cell--selected {
  box-shadow: inset 0 0 0 1.5px var(--color-accent);
}

.cal-daynum {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.55rem;
  height: 1.55rem;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 600;
}

.cal-task-chips {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  min-width: 0;
}

.cal-chip {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  min-width: 0;
  padding: 0.15rem 0.25rem;
  border-radius: 4px;
  background: rgba(232, 228, 216, 0.06);
  border-left: 2px solid var(--color-border);
  cursor: pointer;
}

.cal-chip[data-s='completed'] {
  border-left-color: var(--status-done);
  opacity: 0.75;
}

.cal-chip[data-s='in_progress'] {
  border-left-color: var(--color-accent);
}

.cal-chip[data-s='pending'] {
  border-left-color: rgba(232, 228, 216, 0.35);
}

.cal-chip:hover {
  background: rgba(196, 163, 90, 0.12);
}

.cal-chip-avatar {
  width: 16px !important;
  height: 16px !important;
  font-size: 0.55rem !important;
  flex-shrink: 0;
}

.cal-chip-title {
  font-size: 0.7rem;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.cal-more {
  font-size: 0.68rem;
  color: var(--color-text-muted);
  padding-left: 0.2rem;
}

.day-panel {
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-surface);
  padding: 1rem 1.05rem 1.15rem;
  position: sticky;
  top: 1rem;
}

.day-panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.85rem;
}

.day-panel-header h3 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 1.15rem;
  font-weight: 400;
}

.day-panel-header .muted-line {
  margin: 0.2rem 0 0;
  font-size: 0.82rem;
}

.btn-compact {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.45rem 0.75rem;
  font-size: 0.8rem;
  white-space: nowrap;
}

.day-empty {
  margin: 0;
  padding: 1rem;
}

@media (max-width: 900px) {
  .cal-layout {
    grid-template-columns: 1fr;
  }

  .day-panel {
    position: static;
  }

  .cal-cell {
    min-height: 84px;
  }
}

@media (max-width: 640px) {
  .cal-chip-title {
    display: none;
  }

  .cal-chip {
    width: fit-content;
  }
}
</style>
