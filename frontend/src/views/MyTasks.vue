<template>
  <div class="app-page tasks-page">
    <div class="app-page-header">
      <div>
        <h1>My tasks</h1>
        <p class="app-lede">
          {{ viewMode === 'kanban' ? 'Drag cards between columns to update status.' : 'Track what you owe — grouped by status.' }}
        </p>
      </div>
      <TaskViewModeToggle v-if="tasks.length" v-model="viewMode" />
    </div>

    <p v-if="loading" class="muted-line">Loading tasks…</p>
    <p v-else-if="error" class="error-line">{{ error }}</p>

    <div v-else-if="!tasks.length" class="empty-panel">
      <ClipboardList class="empty-icon" :size="28" :stroke-width="1.5" />
      <p>No tasks assigned to you yet.</p>
    </div>

    <TaskKanbanBoard
      v-else-if="viewMode === 'kanban'"
      :tasks="tasks"
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
      :initial="modalInitial"
      @close="closeModal"
      @save="saveFromModal"
    />
  </div>
</template>

<script setup>
import { ClipboardList } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import { normalizeDueTime } from '@/utils/taskDue'
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

const loading = ref(true)
const error = ref('')
const tasks = ref([])
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
})

const { viewMode } = useTaskViewMode('kanban')
const canManageTasks = computed(() => user.value?.role === 'admin')
const { writeRestricted, writeDisabledTitle } = useWriteAccess()

const statusGroups = computed(() =>
  STATUS_GROUPS.map((group) => ({
    ...group,
    tasks: tasks.value.filter((t) => t.status === group.key),
  })),
)

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
    status: task.status || 'pending',
  }
  formError.value = ''
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editingTaskId.value = null
  modalInitial.value = { title: '', description: '', links: [], assignee_key: null, due_date: '', due_time: '', status: 'pending' }
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
    const pMap = {}
    for (const p of Array.isArray(projectList) ? projectList : []) pMap[p.id] = p
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
      due_date: payload.due_date || null,
      due_time: payload.due_date && payload.due_time ? payload.due_time : null,
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
  if (!window.confirm('Delete this task?')) return

  busyId.value = task.id
  error.value = ''
  try {
    await apiJson(`/api/v1/tasks/${task.id}`, { method: 'DELETE' })
    tasks.value = tasks.value.filter((t) => t.id !== task.id)
  } catch (err) {
    console.error('[MyTasks] delete failed', err)
    error.value = err.message || 'Failed to delete task'
  } finally {
    busyId.value = null
  }
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
</style>
