<template>
  <div class="app-page tasks-page">
    <div class="app-page-header">
      <div>
        <h1>My tasks</h1>
        <p class="app-lede">
          {{ viewMode === 'kanban' ? 'Drag cards between columns to update status.' : 'Track what you owe — grouped by status.' }}
        </p>
      </div>
      <div v-if="tasks.length" class="header-actions">
        <label v-if="showProjectFilter" class="project-filter">
          <span class="sr-only">Filter by project</span>
          <select v-model="projectFilter" aria-label="Filter by project">
            <option value="all">All projects</option>
            <option v-if="hasUnassignedTasks" value="none">No project</option>
            <option v-for="p in filterProjects" :key="p.id" :value="String(p.id)">
              {{ p.title }}
            </option>
          </select>
        </label>
        <TaskViewModeToggle v-model="viewMode" />
      </div>
    </div>

    <p v-if="loading" class="muted-line">Loading tasks…</p>
    <p v-else-if="error" class="error-line">{{ error }}</p>

    <div v-else-if="!tasks.length" class="empty-panel">
      <ClipboardList class="empty-icon" :size="28" :stroke-width="1.5" />
      <p>No tasks assigned to you yet.</p>
    </div>

    <div v-else-if="!visibleTasks.length" class="empty-panel">
      <ClipboardList class="empty-icon" :size="28" :stroke-width="1.5" />
      <p>No tasks in this project.</p>
    </div>

    <TaskKanbanBoard
      v-else-if="viewMode === 'kanban'"
      :tasks="visibleTasks"
      :busy-id="busyId"
      :flash-id="flashId"
      :write-restricted="writeRestricted"
      :write-disabled-title="writeDisabledTitle"
      :can-edit="canManageTasks"
      :can-manage-actions="canManageTasks"
      :assignee-name="assigneeName"
      :assignee-seed="assigneeSeed"
      :project-label="projectLabel"
      @status-change="onStatusChange"
      @edit="openEdit"
      @delete="confirmDelete"
    />

    <TaskListView
      v-else
      :status-groups="statusGroups"
      :busy-id="busyId"
      :flash-id="flashId"
      :write-restricted="writeRestricted"
      :write-disabled-title="writeDisabledTitle"
      :can-edit="canManageTasks"
      :can-manage-actions="canManageTasks"
      :assignee-name="assigneeName"
      :assignee-seed="assigneeSeed"
      :project-label="projectLabel"
      @status-change="onStatusChange"
      @edit="openEdit"
      @delete="confirmDelete"
    />

    <TaskEditModal
      :open="showModal"
      mode="edit"
      :saving="saving"
      :error="formError"
      :assignee-options="assigneeOptions"
      :show-project="true"
      :projects="projects"
      :allow-delete="canManageTasks && !writeRestricted"
      :initial="modalInitial"
      @close="closeModal"
      @save="saveFromModal"
      @delete="deleteFromModal"
    />
  </div>
</template>

<script setup>
import { ClipboardList } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'

import { apiJson } from '@/api/client'
import { normalizeDueTime, sortStatusTasksByDue } from '@/utils/taskDue'
import TaskEditModal from '@/components/TaskEditModal.vue'
import TaskKanbanBoard from '@/components/TaskKanbanBoard.vue'
import TaskListView from '@/components/TaskListView.vue'
import TaskViewModeToggle from '@/components/TaskViewModeToggle.vue'
import { user } from '@/composables/session'
import { useTaskViewMode } from '@/composables/useTaskViewMode'
import { useWriteAccess } from '@/composables/useWriteAccess'
import {
  buildAssigneeOptions,
  parseAssigneeKey,
  resolveAssigneeName,
  taskAssigneeKey,
} from '@/utils/assignee'
import { STATUS_GROUPS } from '@/utils/ui'
import { confirmDeleteTask, removeDeletedTask } from '@/utils/recurrence'

const loading = ref(true)
const error = ref('')
const tasks = ref([])
const projects = ref([])
const projectsById = ref({})
const usersById = ref({})
const contactsById = ref({})
const team = ref([])
const contacts = ref([])
const busyId = ref(null)
const flashId = ref(null)
let flashTimer = null

const showModal = ref(false)
const editingTaskId = ref(null)
const saving = ref(false)
const formError = ref('')
const modalInitial = ref({
  title: '',
  description: '',
  links: [],
  assignee_key: null,
  due_date: '',
  due_time: '',
  status: 'pending',
  priority: 'medium',
  project_id: null,
})

const { viewMode } = useTaskViewMode('kanban')
const canManageTasks = computed(() => user.value?.role === 'admin')
const { writeRestricted, writeDisabledTitle } = useWriteAccess()
const projectFilter = ref('all')

const hasUnassignedTasks = computed(() => tasks.value.some((t) => !t.project_id))

const filterProjects = computed(() => {
  const ids = new Set()
  for (const t of tasks.value) {
    if (t.project_id) ids.add(t.project_id)
  }
  return [...ids]
    .map((id) => projectsById.value[id] || { id, title: `Project #${id}` })
    .sort((a, b) => String(a.title).localeCompare(String(b.title)))
})

const showProjectFilter = computed(() => {
  const projectCount = filterProjects.value.length
  return projectCount > 1 || (projectCount === 1 && hasUnassignedTasks.value)
})

const visibleTasks = computed(() => {
  if (projectFilter.value === 'all') return tasks.value
  if (projectFilter.value === 'none') return tasks.value.filter((t) => !t.project_id)
  const id = Number(projectFilter.value)
  return tasks.value.filter((t) => t.project_id === id)
})

const statusGroups = computed(() =>
  STATUS_GROUPS.map((group) => ({
    ...group,
    tasks: sortStatusTasksByDue(visibleTasks.value.filter((t) => t.status === group.key), group.key),
  })),
)

watch([filterProjects, hasUnassignedTasks], () => {
  if (projectFilter.value === 'all') return
  if (projectFilter.value === 'none') {
    if (!hasUnassignedTasks.value) projectFilter.value = 'all'
    return
  }
  if (!filterProjects.value.some((p) => String(p.id) === projectFilter.value)) {
    projectFilter.value = 'all'
  }
})

const assigneeOptions = computed(() =>
  buildAssigneeOptions({
    users: team.value,
    contacts: contacts.value,
    currentUser: user.value,
  }),
)

function projectLabel(projectId) {
  if (!projectId) return ''
  return projectsById.value[projectId]?.title || `Project #${projectId}`
}

function assigneeName(task) {
  return resolveAssigneeName(task, {
    usersById: usersById.value,
    contactsById: contactsById.value,
    fallback: user.value?.full_name || user.value?.email || 'You',
  })
}

function assigneeSeed(task) {
  return task.assignee_id || task.assignee_contact_id || user.value?.id || task.title
}

function triggerFlash(taskId) {
  flashId.value = taskId
  if (flashTimer) clearTimeout(flashTimer)
  flashTimer = setTimeout(() => {
    flashId.value = null
  }, 700)
}

function openEdit(task) {
  if (writeRestricted.value) return
  if (!canManageTasks.value) return
  editingTaskId.value = task.id
  modalInitial.value = {
    title: task.title || '',
    description: task.description || '',
    links: task.links || [],
    assignee_key: taskAssigneeKey(task),
    due_date: task.due_date ? String(task.due_date).slice(0, 10) : '',
    due_time: normalizeDueTime(task.due_time),
    recurrence: task.recurrence || 'none',
    series_id: task.series_id || null,
    status: task.status || 'pending',
    priority: task.priority || 'medium',
    project_id: task.project_id ?? null,
  }
  formError.value = ''
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editingTaskId.value = null
  modalInitial.value = { title: '', description: '', links: [], assignee_key: null, due_date: '', due_time: '', status: 'pending', priority: 'medium', project_id: null }
  formError.value = ''
}

async function loadTasks() {
  if (!user.value?.id) {
    error.value = 'Not signed in'
    loading.value = false
    return
  }

  try {
    loading.value = true
    error.value = ''
    const [taskList, projectList, users, contactList] = await Promise.all([
      apiJson(`/api/v1/tasks?assignee_id=${user.value.id}`),
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
    console.error('[MyTasks] load failed', err)
    error.value = err.message || 'Failed to load tasks'
  } finally {
    loading.value = false
  }
}

async function onStatusChange({ task, status: next }) {
  if (writeRestricted.value) return
  if (next === task.status) return

  const previous = task.status
  task.status = next
  busyId.value = task.id
  triggerFlash(task.id)

  try {
    const updated = await apiJson(`/api/v1/tasks/${task.id}`, {
      method: 'PATCH',
      body: JSON.stringify({ status: next }),
    })
    const idx = tasks.value.findIndex((t) => t.id === task.id)
    if (idx !== -1) tasks.value[idx] = { ...tasks.value[idx], ...updated }
  } catch (err) {
    console.error('[MyTasks] status update failed', err)
    task.status = previous
    error.value = err.message || 'Failed to update status'
  } finally {
    busyId.value = null
  }
}

async function saveFromModal(payload) {
  if (!payload.title.trim() || !editingTaskId.value) return

  saving.value = true
  formError.value = ''
  try {
    const { assignee_id, assignee_contact_id } = parseAssigneeKey(payload.assignee_key)
    const body = {
      title: payload.title.trim(),
      description: payload.description,
      links: payload.links,
      status: payload.status || 'pending',
      priority: payload.priority || 'medium',
      due_date: payload.due_date || null,
      due_time: payload.due_date && payload.due_time ? payload.due_time : null,
      project_id: payload.project_id ?? null,
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
    const idx = tasks.value.findIndex((t) => t.id === editingTaskId.value)
    if (idx !== -1) {
      if (updated.assignee_id !== user.value?.id) {
        tasks.value = tasks.value.filter((t) => t.id !== updated.id)
      } else {
        tasks.value[idx] = { ...tasks.value[idx], ...updated }
        triggerFlash(updated.id)
      }
    }
    closeModal()
  } catch (err) {
    console.error('[MyTasks] save failed', err)
    formError.value = err.message || 'Failed to save task'
  } finally {
    saving.value = false
  }
}

async function confirmDelete(task) {
  if (writeRestricted.value) return
  if (!canManageTasks.value) return
  if (!confirmDeleteTask(task)) return

  busyId.value = task.id
  error.value = ''
  try {
    await apiJson(`/api/v1/tasks/${task.id}`, { method: 'DELETE' })
    const remaining = removeDeletedTask(tasks.value, task)
    tasks.value = remaining
    if (editingTaskId.value && !remaining.some((t) => t.id === editingTaskId.value)) {
      closeModal()
    }
  } catch (err) {
    console.error('[MyTasks] delete failed', err)
    error.value = err.message || 'Failed to delete task'
  } finally {
    busyId.value = null
  }
}

async function deleteFromModal() {
  const task = tasks.value.find((t) => t.id === editingTaskId.value)
  if (!task) return
  await confirmDelete(task)
}

onMounted(loadTasks)
</script>

<style scoped>
.tasks-page .empty-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.65rem;
  text-align: center;
}

.empty-icon {
  color: var(--color-accent);
  opacity: 0.85;
}

.tasks-page .app-page-header {
  align-items: flex-start;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.project-filter select {
  min-width: 11rem;
  max-width: 16rem;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>
