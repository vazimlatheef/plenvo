<template>
  <div class="my-tasks">
    <h1>My tasks</h1>

    <p v-if="loading" class="muted">Loading tasks…</p>
    <p v-else-if="error" class="error">{{ error }}</p>
    <p v-else-if="!tasks.length" class="muted">No tasks assigned to you yet.</p>

    <div v-else class="groups">
      <section v-for="group in statusGroups" :key="group.key" class="group">
        <h2>{{ group.label }} <span class="count">({{ group.tasks.length }})</span></h2>
        <ul v-if="group.tasks.length" class="list">
          <li v-for="task in group.tasks" :key="task.id" class="row">
            <div class="main">
              <span class="title">{{ task.title }}</span>
              <span class="meta">
                {{ projectName(task.project_id) }}
                <template v-if="task.due_date"> · Due {{ formatDate(task.due_date) }}</template>
                <template v-else> · No due date</template>
              </span>
            </div>
            <select
              class="status-select"
              :value="task.status"
              :disabled="busyId === task.id"
              @change="onStatusChange(task, $event)"
            >
              <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </option>
            </select>
          </li>
        </ul>
        <p v-else class="empty">None</p>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

import { apiJson } from '@/api/client'
import { user } from '@/composables/session'

const STATUS_ORDER = [
  { key: 'pending', label: 'To Do' },
  { key: 'in_progress', label: 'In Progress' },
  { key: 'completed', label: 'Done' },
]

const statusOptions = STATUS_ORDER.map((s) => ({ value: s.key, label: s.label }))

const loading = ref(true)
const error = ref('')
const tasks = ref([])
const projectsById = ref({})
const busyId = ref(null)

const statusGroups = computed(() =>
  STATUS_ORDER.map((group) => ({
    ...group,
    tasks: tasks.value.filter((t) => t.status === group.key),
  })),
)

function projectName(projectId) {
  if (!projectId) return 'No project'
  return projectsById.value[projectId]?.title || `Project #${projectId}`
}

function formatDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
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
    const [taskList, projectList] = await Promise.all([
      apiJson(`/api/v1/tasks?assignee_id=${user.value.id}`),
      apiJson('/api/v1/projects').catch(() => []),
    ])
    tasks.value = Array.isArray(taskList) ? taskList : []
    const map = {}
    for (const p of Array.isArray(projectList) ? projectList : []) {
      map[p.id] = p
    }
    projectsById.value = map
  } catch (err) {
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

  try {
    const updated = await apiJson(`/api/v1/tasks/${task.id}`, {
      method: 'PATCH',
      body: JSON.stringify({ status: next }),
    })
    const idx = tasks.value.findIndex((t) => t.id === task.id)
    if (idx !== -1) {
      tasks.value[idx] = { ...tasks.value[idx], ...updated }
    }
  } catch (err) {
    task.status = previous
    event.target.value = previous
    error.value = err.message || 'Failed to update status'
  } finally {
    busyId.value = null
  }
}

onMounted(loadTasks)
</script>

<style scoped>
.my-tasks {
  max-width: 800px;
}

.my-tasks h1 {
  margin: 0 0 1.25rem;
  font-size: 1.5rem;
  font-weight: 600;
}

.muted {
  color: var(--color-text-muted);
}

.error {
  color: #ef4444;
}

.groups {
  display: flex;
  flex-direction: column;
  gap: 1.75rem;
}

.group h2 {
  margin: 0 0 0.75rem;
  font-size: 1rem;
  font-weight: 600;
}

.count {
  font-weight: 400;
  color: var(--color-text-muted);
}

.list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--color-border);
}

.main {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  min-width: 0;
}

.title {
  font-weight: 500;
}

.meta {
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.status-select {
  flex-shrink: 0;
  padding: 0.35rem 0.5rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-bg);
  color: var(--color-text);
  font: inherit;
  font-size: 0.85rem;
}

.status-select:disabled {
  opacity: 0.6;
}

.empty {
  margin: 0;
  font-size: 0.9rem;
  color: var(--color-text-muted);
}
</style>
