<template>
  <div class="app-page">
    <div class="app-page-header">
      <div>
        <RouterLink to="/app/projects" class="app-back">← Projects</RouterLink>
        <h1>{{ project?.title || 'Project tasks' }}</h1>
        <p v-if="project?.description" class="app-lede">{{ project.description }}</p>
      </div>
      <button type="button" class="btn-primary" @click="showCreate = true">+ New task</button>
    </div>

    <p v-if="loading" class="muted-line">Loading tasks…</p>
    <p v-else-if="error" class="error-line">{{ error }}</p>

    <div v-else-if="!tasks.length" class="empty-panel">
      <p>No tasks yet — create the first one</p>
      <button type="button" class="btn-primary" @click="showCreate = true">Create task</button>
    </div>

    <div v-else>
      <section v-for="group in statusGroups" :key="group.key">
        <div class="group-label">
          <span class="status-pill" :data-s="group.key">{{ group.label }}</span>
          <span class="count">({{ group.tasks.length }})</span>
        </div>
        <ul v-if="group.tasks.length" class="dense-list">
          <li
            v-for="task in group.tasks"
            :key="task.id"
            class="dense-row"
            :class="{ 'dense-row--flash': flashId === task.id }"
          >
            <span
              class="avatar"
              :class="`avatar-tone-${avatarTone(assigneeSeed(task))}`"
              :title="assigneeName(task.assignee_id)"
            >
              {{ getInitials(assigneeName(task.assignee_id)) }}
            </span>
            <div class="dense-row__meta">
              <span class="dense-row__title">{{ task.title }}</span>
              <span v-if="project?.title" class="project-tag">{{ project.title }}</span>
            </div>
            <span class="dense-row__due">
              {{ task.due_date ? formatShortDate(task.due_date) : '—' }}
            </span>
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
        <p v-else class="muted-line" style="margin: 0.35rem 0 0; font-size: 0.85rem">None</p>
      </section>
    </div>

    <div v-if="showCreate" class="modal-overlay" @click.self="closeCreate">
      <div class="modal-panel">
        <h2>New task</h2>
        <form class="field-stack" @submit.prevent="createTask">
          <label>
            Title *
            <input v-model="newTask.title" type="text" required maxlength="200" :disabled="creating" />
          </label>
          <label>
            Assignee
            <select v-model="newTask.assignee_id" :disabled="creating">
              <option :value="null">Unassigned</option>
              <option v-for="u in team" :key="u.id" :value="u.id">
                {{ u.full_name || u.email }}
              </option>
            </select>
          </label>
          <label>
            Due date
            <input v-model="newTask.due_date" type="date" :disabled="creating" />
          </label>
          <label>
            Status
            <select v-model="newTask.status" :disabled="creating">
              <option v-for="opt in STATUS_OPTIONS" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </option>
            </select>
          </label>
          <p v-if="createError" class="error-line">{{ createError }}</p>
          <div class="modal-actions">
            <button type="button" class="btn-outline" :disabled="creating" @click="closeCreate">Cancel</button>
            <button type="submit" class="btn-primary" :disabled="creating || !newTask.title.trim()">
              {{ creating ? 'Creating…' : 'Create task' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import { apiJson } from '@/api/client'
import {
  STATUS_GROUPS,
  STATUS_OPTIONS,
  avatarTone,
  formatShortDate,
  getInitials,
} from '@/utils/ui'

const route = useRoute()

const project = ref(null)
const tasks = ref([])
const team = ref([])
const usersById = ref({})
const loading = ref(true)
const error = ref('')
const busyId = ref(null)
const flashId = ref(null)
let flashTimer = null

const showCreate = ref(false)
const creating = ref(false)
const createError = ref('')
const newTask = ref({
  title: '',
  assignee_id: null,
  due_date: '',
  status: 'pending',
})

const projectId = computed(() => {
  const id = Number(route.params.projectId)
  return Number.isFinite(id) && id > 0 ? id : null
})

const statusGroups = computed(() =>
  STATUS_GROUPS.map((group) => ({
    ...group,
    tasks: tasks.value.filter((t) => t.status === group.key),
  })),
)

function assigneeName(assigneeId) {
  if (!assigneeId) return 'Unassigned'
  const u = usersById.value[assigneeId]
  return u?.full_name || u?.email || `User #${assigneeId}`
}

function assigneeSeed(task) {
  return task.assignee_id || task.title
}

function triggerFlash(taskId) {
  flashId.value = taskId
  if (flashTimer) clearTimeout(flashTimer)
  flashTimer = setTimeout(() => {
    flashId.value = null
  }, 700)
}

function resetCreateForm() {
  newTask.value = { title: '', assignee_id: null, due_date: '', status: 'pending' }
  createError.value = ''
}

function closeCreate() {
  showCreate.value = false
  resetCreateForm()
}

async function loadPage() {
  if (!projectId.value) {
    error.value = 'Invalid project id'
    loading.value = false
    console.error('[AdminProjectTasks] missing/invalid projectId', route.params.projectId)
    return
  }

  loading.value = true
  error.value = ''
  try {
    const [proj, taskList, users] = await Promise.all([
      apiJson(`/api/v1/projects/${projectId.value}`),
      apiJson(`/api/v1/tasks?project_id=${projectId.value}`),
      apiJson('/api/v1/users').catch((err) => {
        console.error('[AdminProjectTasks] failed to load users', err)
        return []
      }),
    ])

    project.value = proj
    tasks.value = Array.isArray(taskList) ? taskList : []
    team.value = Array.isArray(users) ? users : []
    const map = {}
    for (const u of team.value) map[u.id] = u
    usersById.value = map
  } catch (err) {
    console.error('[AdminProjectTasks] load failed', err)
    error.value = err.message || 'Failed to load project tasks'
    project.value = null
    tasks.value = []
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
    console.error('[AdminProjectTasks] status update failed', err)
    task.status = previous
    event.target.value = previous
    error.value = err.message || 'Failed to update status'
  } finally {
    busyId.value = null
  }
}

async function createTask() {
  if (!newTask.value.title.trim() || !projectId.value) return

  creating.value = true
  createError.value = ''
  try {
    const created = await apiJson('/api/v1/tasks', {
      method: 'POST',
      body: JSON.stringify({
        title: newTask.value.title.trim(),
        project_id: projectId.value,
        status: newTask.value.status || 'pending',
        assignee_id: newTask.value.assignee_id ? Number(newTask.value.assignee_id) : null,
        due_date: newTask.value.due_date || null,
      }),
    })
    tasks.value = [created, ...tasks.value]
    closeCreate()
  } catch (err) {
    console.error('[AdminProjectTasks] create task failed', err)
    createError.value = err.message || 'Failed to create task'
  } finally {
    creating.value = false
  }
}

onMounted(loadPage)
watch(projectId, (id, prev) => {
  if (id && id !== prev) loadPage()
})
</script>
