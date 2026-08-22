<template>
  <div class="app-page tasks-page">
    <div class="app-page-header">
      <div>
        <h1>My tasks</h1>
        <p class="app-lede">Track what you owe — grouped by status.</p>
      </div>
    </div>

    <p v-if="loading" class="muted-line">Loading tasks…</p>
    <p v-else-if="error" class="error-line">{{ error }}</p>

    <div v-else-if="!tasks.length" class="empty-panel">
      <ClipboardList class="empty-icon" :size="28" :stroke-width="1.5" />
      <p>No tasks assigned to you yet.</p>
    </div>

    <div v-else>
      <div class="dense-row dense-row--task dense-row--head" aria-hidden="true">
        <span />
        <span class="dense-head-label">Task</span>
        <span class="dense-head-label">Assigned to</span>
        <span class="dense-head-label">Due</span>
        <span />
        <span class="dense-head-label dense-head-label--end">Status</span>
      </div>
      <section v-for="group in statusGroups" :key="group.key" class="task-group">
        <div class="group-label">
          <span class="status-pill" :data-s="group.key">{{ group.label }}</span>
          <span class="count">{{ group.tasks.length }}</span>
        </div>
        <ul v-if="group.tasks.length" class="dense-list">
          <li
            v-for="task in group.tasks"
            :key="task.id"
            class="dense-row dense-row--task"
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
              <button
                v-if="canManageTasks"
                type="button"
                class="dense-row__title"
                @click="openEdit(task)"
              >
                {{ task.title }}
              </button>
              <span v-else class="dense-row__title">{{ task.title }}</span>
              <span v-if="projectLabel(task.project_id)" class="project-tag">
                {{ projectLabel(task.project_id) }}
              </span>
            </div>
            <div class="dense-row__assignee" :title="assigneeName(task)">
              <UserRound class="dense-row__assignee-icon" :size="13" :stroke-width="1.75" />
              <span class="dense-row__assignee-name">{{ assigneeName(task) }}</span>
            </div>
            <span class="dense-row__due">
              <Calendar class="dense-row__due-icon" :size="13" :stroke-width="1.75" />
              {{ task.due_date ? formatShortDate(task.due_date) : 'No due date' }}
            </span>
            <div class="dense-row__actions">
              <template v-if="canManageTasks">
                <button
                  type="button"
                  class="row-icon-btn"
                  title="Edit task"
                  aria-label="Edit task"
                  :disabled="busyId === task.id"
                  @click="openEdit(task)"
                >
                  <Pencil :size="15" :stroke-width="1.75" />
                </button>
                <button
                  type="button"
                  class="row-icon-btn row-icon-btn--danger"
                  title="Delete task"
                  aria-label="Delete task"
                  :disabled="busyId === task.id"
                  @click="confirmDelete(task)"
                >
                  <Trash2 :size="15" :stroke-width="1.75" />
                </button>
              </template>
            </div>
            <select
              class="status-pill"
              :data-s="task.status"
              :value="task.status"
              :disabled="busyId === task.id"
              @change="onStatusChange(task, $event)"
            >
              <option v-for="opt in STATUS_OPTIONS" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </option>
            </select>
          </li>
        </ul>
        <p v-else class="muted-line empty-group">None</p>
      </section>
    </div>

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
import { Calendar, ClipboardList, Pencil, Trash2, UserRound } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

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
  STATUS_GROUPS,
  STATUS_OPTIONS,
  avatarTone,
  formatShortDate,
  getInitials,
} from '@/utils/ui'

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
  assignee_key: null,
  due_date: '',
  status: 'pending',
})

const canManageTasks = computed(() => user.value?.role === 'admin')

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
  if (!canManageTasks.value) return
  editingTaskId.value = task.id
  modalInitial.value = {
    title: task.title || '',
    assignee_key: taskAssigneeKey(task),
    due_date: task.due_date ? String(task.due_date).slice(0, 10) : '',
    status: task.status || 'pending',
  }
  formError.value = ''
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editingTaskId.value = null
  modalInitial.value = { title: '', assignee_key: null, due_date: '', status: 'pending' }
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

async function onStatusChange(task, event) {
  const next = event.target.value
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
    event.target.value = previous
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
      status: payload.status || 'pending',
      due_date: payload.due_date || null,
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

.empty-group {
  margin: 0.35rem 0 0;
  font-size: 0.85rem;
}
</style>
