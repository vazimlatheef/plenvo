<template>
  <div class="app-page">
    <div class="app-page-header">
      <h1>My tasks</h1>
    </div>

    <p v-if="loading" class="muted-line">Loading tasks…</p>
    <p v-else-if="error" class="error-line">{{ error }}</p>

    <div v-else-if="!tasks.length" class="empty-panel">
      <p>No tasks assigned to you yet.</p>
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
              <span v-if="projectLabel(task.project_id)" class="project-tag">
                {{ projectLabel(task.project_id) }}
              </span>
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
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

import { apiJson } from '@/api/client'
import { user } from '@/composables/session'
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
const busyId = ref(null)
const flashId = ref(null)
let flashTimer = null

const statusGroups = computed(() =>
  STATUS_GROUPS.map((group) => ({
    ...group,
    tasks: tasks.value.filter((t) => t.status === group.key),
  })),
)

function projectLabel(projectId) {
  if (!projectId) return ''
  return projectsById.value[projectId]?.title || `Project #${projectId}`
}

function assigneeName(assigneeId) {
  if (!assigneeId) return user.value?.full_name || user.value?.email || 'You'
  const u = usersById.value[assigneeId]
  return u?.full_name || u?.email || `User #${assigneeId}`
}

function assigneeSeed(task) {
  return task.assignee_id || user.value?.id || task.title
}

function triggerFlash(taskId) {
  flashId.value = taskId
  if (flashTimer) clearTimeout(flashTimer)
  flashTimer = setTimeout(() => {
    flashId.value = null
  }, 700)
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
    const [taskList, projectList, users] = await Promise.all([
      apiJson(`/api/v1/tasks?assignee_id=${user.value.id}`),
      apiJson('/api/v1/projects').catch(() => []),
      apiJson('/api/v1/users').catch(() => []),
    ])
    tasks.value = Array.isArray(taskList) ? taskList : []
    const pMap = {}
    for (const p of Array.isArray(projectList) ? projectList : []) pMap[p.id] = p
    projectsById.value = pMap
    const uMap = {}
    for (const u of Array.isArray(users) ? users : []) uMap[u.id] = u
    usersById.value = uMap
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

onMounted(loadTasks)
</script>
