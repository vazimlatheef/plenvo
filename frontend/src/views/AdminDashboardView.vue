<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1>Dashboard</h1>
      <p class="subtitle">{{ greeting }}, {{ userName }}</p>
    </div>

    <section class="ai-hero">
      <div class="ai-hero__icon">
        <Sparkles :size="22" :stroke-width="1.75" />
      </div>
      <div class="ai-hero__body">
        <p class="ai-hero__eyebrow">Plenvo AI</p>
        <h2 class="ai-hero__title">Capture anything. Ask anything.</h2>
        <p class="ai-hero__lede">
          Paste notes to create tasks, or ask a question about your workload — Brief reads your live board.
        </p>
        <div class="ai-hero__input-row">
          <input
            v-model="aiQuery"
            type="text"
            class="ai-hero__input"
            placeholder="Ask or paste a note…"
            @keydown.enter.prevent="submitAiQuery"
          />
          <button type="button" class="btn-primary ai-hero__submit" @click="submitAiQuery">
            <Sparkles :size="15" :stroke-width="1.75" />
            Open Brief
          </button>
        </div>
        <div class="ai-hero__chips">
          <button
            v-for="chip in aiPromptChips"
            :key="chip"
            type="button"
            class="ai-hero__chip"
            @click="openAiWithQuery(chip)"
          >
            {{ chip }}
          </button>
        </div>
      </div>
    </section>

    <div class="stats-grid">
      <RouterLink
        v-for="stat in statCards"
        :key="stat.label"
        :to="stat.to"
        class="stat-card stat-card--link"
        :class="{ alert: stat.alert }"
      >
        <div class="stat-icon" :class="{ 'stat-icon--alert': stat.alert }">
          <component :is="stat.icon" :size="20" :stroke-width="1.75" />
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
      </RouterLink>
    </div>

    <section class="section">
      <div class="section-header">
        <h2>Recommended focus</h2>
        <RouterLink to="/app/tasks" class="link-button">
          View all tasks
          <ArrowRight :size="14" :stroke-width="1.75" />
        </RouterLink>
      </div>
      <div v-if="loadingFocus" class="loading-state">Loading tasks…</div>
      <div v-else-if="focusTasks.length === 0" class="empty-state">
        <p>No open tasks assigned to you. <RouterLink to="/app/tasks">Browse tasks</RouterLink></p>
      </div>
      <div v-else class="tasks-list">
        <button
          v-for="task in focusTasks"
          :key="task.id"
          type="button"
          class="task-item task-item--clickable"
          :class="{ overdue: isFocusOverdue(task) }"
          @click="openEditTask(task)"
        >
          <div class="task-info">
            <h4>{{ task.title }}</h4>
            <div class="task-meta">
              <span v-if="hasTeamContext && (task.assignee_id || task.assignee_contact_id)" class="meta-text">
                <UserRound :size="13" :stroke-width="1.75" />
                {{ assigneeLabel(task) }}
              </span>
              <span v-if="task.due_date" class="meta-text">
                <Calendar :size="13" :stroke-width="1.75" />
                Due {{ formatTaskDue(task) }}
              </span>
              <span v-else class="meta-text">No due date</span>
            </div>
          </div>
          <div class="task-side">
            <span class="priority-badge" :class="task.priority">
              <component :is="priorityIcon(task.priority)" :size="12" :stroke-width="2" />
              {{ task.priority }}
            </span>
          </div>
        </button>
      </div>
    </section>

    <section class="section">
      <div class="section-header">
        <h2>Recent Projects</h2>
        <RouterLink to="/app/projects" class="link-button">
          View all
          <ArrowRight :size="14" :stroke-width="1.75" />
        </RouterLink>
      </div>
      <div v-if="loadingProjects" class="loading-state">Loading projects…</div>
      <div v-else-if="recentProjects.length === 0" class="empty-state">
        <p>No projects yet. <RouterLink to="/app/projects">Create your first project</RouterLink></p>
      </div>
      <div v-else class="projects-preview">
        <div v-for="project in recentProjects" :key="project.id" class="project-preview-card">
          <h3>{{ project.title }}</h3>
          <p v-if="project.description" class="project-desc">{{ project.description }}</p>
          <RouterLink :to="`/app/projects/${project.id}/tasks`" class="view-link">
            View tasks
            <ArrowRight :size="13" :stroke-width="1.75" />
          </RouterLink>
        </div>
      </div>
    </section>

    <section v-if="overdueTasks.length > 0" class="section">
      <div class="section-header">
        <h2>
          <AlertTriangle class="section-icon section-icon--alert" :size="18" :stroke-width="1.75" />
          Overdue Tasks
        </h2>
        <span class="badge-alert">{{ overdueTasks.length }}</span>
      </div>
      <div class="tasks-list">
        <div
          v-for="task in overdueTasks"
          :key="task.id"
          class="task-item overdue task-item--clickable"
          role="button"
          tabindex="0"
          @click="openEditTask(task)"
          @keydown.enter="openEditTask(task)"
        >
          <div class="task-info">
            <h4>{{ task.title }}</h4>
            <div class="task-meta">
              <span v-if="task.assignee_id || task.assignee_contact_id" class="meta-text">
                <UserRound :size="13" :stroke-width="1.75" />
                {{ assigneeLabel(task) }}
              </span>
              <span class="meta-text">
                <Calendar :size="13" :stroke-width="1.75" />
                Due {{ formatTaskDue(task) }}
              </span>
            </div>
          </div>
          <div class="task-side" @click.stop>
            <button
              type="button"
              class="row-icon-btn row-icon-btn--danger"
              title="Delete task"
              aria-label="Delete task"
              :disabled="busyTaskId === task.id"
              @click="deleteOverdueTask(task)"
            >
              <Trash2 :size="15" :stroke-width="1.75" />
            </button>
            <span class="priority-badge" :class="task.priority">
              <component :is="priorityIcon(task.priority)" :size="12" :stroke-width="2" />
              {{ task.priority }}
            </span>
          </div>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="section-header">
        <h2>Team</h2>
        <RouterLink to="/app/team" class="link-button">
          Manage team
          <ArrowRight :size="14" :stroke-width="1.75" />
        </RouterLink>
      </div>
      <div v-if="loadingTeam" class="loading-state">Loading team…</div>
      <div v-else-if="recentEmployees.length === 0" class="empty-state">
        <p>No team members yet. <RouterLink to="/app/team">Add your first team member</RouterLink></p>
      </div>
      <div v-else class="team-preview">
        <div v-for="emp in recentEmployees" :key="emp.key" class="team-member">
          <div class="member-avatar">{{ getInitials(emp.full_name) }}</div>
          <div class="member-info">
            <div class="member-name">{{ emp.full_name }}</div>
            <div class="member-meta">{{ emp.role }}{{ emp.company ? ` · ${emp.company}` : '' }}</div>
          </div>
        </div>
      </div>
    </section>

    <TaskEditModal
      :open="showTaskModal"
      :mode="taskModalMode"
      :saving="savingTask"
      :error="taskFormError"
      :assignee-options="assigneeOptions"
      :show-project="true"
      :projects="dashboardProjects"
      :initial="taskModalInitial"
      @close="closeTaskModal"
      @save="saveTaskFromModal"
    />
  </div>
</template>

<script setup>
import {
  AlertTriangle,
  ArrowDown,
  ArrowRight,
  ArrowUp,
  Calendar,
  CheckSquare,
  FolderKanban,
  Minus,
  Sparkles,
  Trash2,
  UserRound,
  Users,
} from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { apiJson } from '@/api/client'
import TaskEditModal from '@/components/TaskEditModal.vue'
import { getToken } from '@/services/auth'
import { user } from '@/composables/session'
import { useWriteAccess } from '@/composables/useWriteAccess'
import {
  buildAssigneeOptions,
  parseAssigneeKey,
  taskAssigneeKey,
} from '@/utils/assignee'
import { focusTasksForUser, isTaskOverdue } from '@/utils/taskInsights'
import { formatTaskDue, normalizeDueTime } from '@/utils/taskDue'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const router = useRouter()
const route = useRoute()
const { writeRestricted, writeDisabledTitle } = useWriteAccess()
const aiQuery = ref('')
const busyTaskId = ref(null)
const showTaskModal = ref(false)
const taskModalMode = ref('edit')
const editingTaskId = ref(null)
const savingTask = ref(false)
const taskFormError = ref('')
const taskModalInitial = ref({
  title: '',
  description: '',
  links: [],
  assignee_key: null,
  due_date: '',
  due_time: '',
  status: 'pending',
  project_id: null,
})

const stats = ref({
  projects: 0,
  tasks: 0,
  employees: 0,
  overdue: 0,
})

const recentProjects = ref([])
const dashboardProjects = ref([])
const allTasks = ref([])
const overdueTasks = ref([])
const recentEmployees = ref([])
const employees = ref([])
const contacts = ref([])

const loadingProjects = ref(true)
const loadingFocus = ref(true)
const loadingTeam = ref(true)

const userName = computed(() => user.value?.first_name || 'there')
const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 18) return 'Good afternoon'
  return 'Good evening'
})

const statCards = computed(() => [
  { label: 'Active Projects', value: stats.value.projects, icon: FolderKanban, alert: false, to: '/app/projects' },
  { label: 'Total Tasks', value: stats.value.tasks, icon: CheckSquare, alert: false, to: '/app/tasks' },
  { label: 'Team Members', value: stats.value.employees, icon: Users, alert: false, to: '/app/team' },
  {
    label: stats.value.overdue > 0 ? 'Overdue Tasks' : 'On schedule',
    value: stats.value.overdue,
    icon: AlertTriangle,
    alert: stats.value.overdue > 0,
    to: '/app/tasks',
  },
])

const focusTasks = computed(() => {
  const myContact = contacts.value.find((c) => c.user_id === user.value?.id)
  return focusTasksForUser(allTasks.value, user.value?.id, myContact?.id ?? null, 3)
})

const assigneeOptions = computed(() =>
  buildAssigneeOptions({
    users: employees.value,
    contacts: contacts.value,
    currentUser: user.value,
  }),
)

const hasTeamContext = computed(() => stats.value.employees > 1)

const aiPromptChips = computed(() =>
  hasTeamContext.value
    ? ['How is my team performing?', "What's overdue this week?", 'What should I focus on today?']
    : ['What should I focus on today?', "What's coming up this week?"],
)

function openAiWithQuery(text) {
  router.push({
    path: '/app/admin/ai-terminal',
    query: { q: text, submit: '1' },
  })
}

function submitAiQuery() {
  const text = aiQuery.value.trim()
  if (!text) {
    router.push('/app/admin/ai-terminal')
    return
  }
  openAiWithQuery(text)
}

function priorityIcon(priority) {
  if (priority === 'high') return ArrowUp
  if (priority === 'low') return ArrowDown
  return Minus
}

async function fetchDashboardData() {
  const token = getToken()

  try {
    const projectsRes = await axios.get(`${API_URL}/api/v1/projects`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    const projects = projectsRes.data
    stats.value.projects = projects.length
    recentProjects.value = projects.slice(0, 3)
    dashboardProjects.value = projects
  } catch (err) {
    console.error('Failed to load projects:', err)
  } finally {
    loadingProjects.value = false
  }

  try {
    const tasksRes = await axios.get(`${API_URL}/api/v1/tasks`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    const tasks = tasksRes.data
    allTasks.value = tasks
    stats.value.tasks = tasks.length
    const now = new Date()
    overdueTasks.value = tasks
      .filter((t) => isTaskOverdue(t))
      .slice(0, 5)
    stats.value.overdue = tasks.filter(
      (t) => isTaskOverdue(t),
    ).length
  } catch (err) {
    console.error('Failed to load tasks:', err)
  } finally {
    loadingFocus.value = false
  }

  try {
    const [employeesRes, contactsRes] = await Promise.all([
      axios.get(`${API_URL}/api/v1/users?role=employee`, {
        headers: { Authorization: `Bearer ${token}` },
      }),
      axios
        .get(`${API_URL}/api/v1/contacts`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        .catch(() => ({ data: [] })),
    ])
    employees.value = employeesRes.data
    contacts.value = Array.isArray(contactsRes.data) ? contactsRes.data : []
    const contactEmails = new Set(contacts.value.map((c) => (c.email || '').toLowerCase()))
    const preview = [
      ...contacts.value.map((c) => ({
        key: `c-${c.id}`,
        full_name: c.name,
        role: c.role || 'Member',
        company: c.company || '',
      })),
      ...employees.value
        .filter((e) => !contactEmails.has((e.email || '').toLowerCase()))
        .map((e) => ({
          key: `u-${e.id}`,
          full_name: e.full_name,
          role: e.job_title || e.position || 'Employee',
          company: e.company_name || '',
        })),
    ]
    stats.value.employees = preview.length
    recentEmployees.value = preview.slice(0, 4)
  } catch (err) {
    console.error('Failed to load team:', err)
  } finally {
    loadingTeam.value = false
  }
}

function assigneeLabel(task) {
  if (task.assignee_id) {
    const emp = employees.value.find((e) => e.id === task.assignee_id)
    return emp ? emp.full_name : 'Unknown'
  }
  if (task.assignee_contact_id) {
    const c = contacts.value.find((x) => x.id === task.assignee_contact_id)
    return c ? c.name : 'Contact'
  }
  return 'Unassigned'
}

function openCreateTask() {
  if (writeRestricted.value) return
  editingTaskId.value = null
  taskModalMode.value = 'create'
  taskModalInitial.value = {
    title: '',
    description: '',
    links: [],
    assignee_key: user.value?.id ? `user:${user.value.id}` : null,
    due_date: '',
  due_time: '',
    status: 'pending',
    project_id: null,
  }
  taskFormError.value = ''
  showTaskModal.value = true
}

function openEditTask(task) {
  if (writeRestricted.value) return
  editingTaskId.value = task.id
  taskModalMode.value = 'edit'
  taskModalInitial.value = {
    title: task.title || '',
    description: task.description || '',
    links: task.links || [],
    assignee_key: taskAssigneeKey(task),
    due_date: task.due_date ? String(task.due_date).slice(0, 10) : '',
    due_time: normalizeDueTime(task.due_time),
    status: task.status || 'pending',
    project_id: task.project_id ?? null,
  }
  taskFormError.value = ''
  showTaskModal.value = true
}

function closeTaskModal() {
  showTaskModal.value = false
  editingTaskId.value = null
  taskFormError.value = ''
}

function refreshOverdueList(tasks) {
  const now = new Date()
  overdueTasks.value = tasks
    .filter((t) => isTaskOverdue(t))
    .slice(0, 5)
  stats.value.overdue = tasks.filter(
    (t) => isTaskOverdue(t),
  ).length
}

async function saveTaskFromModal(payload) {
  if (!payload.title.trim()) return
  savingTask.value = true
  taskFormError.value = ''
  try {
    const { assignee_id, assignee_contact_id } = parseAssigneeKey(payload.assignee_key)
    const body = {
      title: payload.title.trim(),
      description: payload.description,
      links: payload.links,
      status: payload.status || 'pending',
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
    if (taskModalMode.value === 'create') {
      const created = await apiJson('/api/v1/tasks', {
        method: 'POST',
        body: JSON.stringify(body),
      })
      allTasks.value = [created, ...allTasks.value]
      stats.value.tasks = (stats.value.tasks || 0) + 1
      refreshOverdueList(allTasks.value)
      closeTaskModal()
      return
    }
    if (!editingTaskId.value) return
    const updated = await apiJson(`/api/v1/tasks/${editingTaskId.value}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    })
    allTasks.value = allTasks.value.map((t) => (t.id === updated.id ? { ...t, ...updated } : t))
    refreshOverdueList(allTasks.value)
    closeTaskModal()
  } catch (err) {
    console.error('Failed to save task:', err)
    taskFormError.value = err.message || 'Failed to save task'
  } finally {
    savingTask.value = false
  }
}

async function deleteOverdueTask(task) {
  if (writeRestricted.value) return
  if (!window.confirm('Delete this task?')) return
  busyTaskId.value = task.id
  try {
    await apiJson(`/api/v1/tasks/${task.id}`, { method: 'DELETE' })
    overdueTasks.value = overdueTasks.value.filter((t) => t.id !== task.id)
    stats.value.overdue = overdueTasks.value.length
    stats.value.tasks = Math.max(0, (stats.value.tasks || 1) - 1)
  } catch (err) {
    console.error('Failed to delete task:', err)
  } finally {
    busyTaskId.value = null
  }
}

function getInitials(name) {
  return (name || '')
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

function formatDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  const now = new Date()
  const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24))
  if (diffDays === 0) return 'today'
  if (diffDays === 1) return 'yesterday'
  return `${diffDays} days ago`
}

function formatDueDate(dateString) {
  if (!dateString) return ''
  return new Date(dateString).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
}

function isFocusOverdue(task) {
  return isTaskOverdue(task)
}

onMounted(() => {
  fetchDashboardData()
  if (route.query.newTask === '1') {
    openCreateTask()
    router.replace({ path: route.path, query: {} })
  }
})
</script>

<style scoped>
.dashboard {
  max-width: 100%;
  animation: appContentIn 0.55s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.ai-hero {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  margin-bottom: 2rem;
  padding: 1.25rem 1.35rem;
  border: 1px solid rgba(196, 163, 90, 0.28);
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, rgba(196, 163, 90, 0.1), rgba(0, 0, 0, 0.12));
  animation: appContentIn 0.55s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.ai-hero__icon {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: var(--radius-sm);
  background: var(--color-accent-soft);
  color: var(--color-accent);
}

.ai-hero__body {
  flex: 1;
  min-width: 0;
}

.ai-hero__eyebrow {
  margin: 0 0 0.25rem;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-accent);
}

.ai-hero__title {
  margin: 0 0 0.35rem;
  font-family: var(--font-display);
  font-size: 1.45rem;
  font-weight: 400;
}

.ai-hero__lede {
  margin: 0 0 0.85rem;
  font-size: 0.88rem;
  color: var(--color-text-muted);
  line-height: 1.5;
}

.ai-hero__input-row {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.65rem;
}

.ai-hero__input {
  flex: 1;
  min-width: 0;
  font-family: var(--font-body);
  font-size: 0.9rem;
  padding: 0.55rem 0.7rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
}

.ai-hero__submit {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  white-space: nowrap;
}

.ai-hero__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.ai-hero__chip {
  font-family: var(--font-body);
  font-size: 0.78rem;
  padding: 0.32rem 0.65rem;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  background: rgba(0, 0, 0, 0.15);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}

.ai-hero__chip:hover {
  border-color: rgba(196, 163, 90, 0.45);
  color: var(--color-text);
}

@media (max-width: 640px) {
  .ai-hero {
    flex-direction: column;
  }

  .ai-hero__input-row {
    flex-direction: column;
  }
}

.section {
  margin-bottom: 2.25rem;
  animation: appContentIn 0.55s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.section:nth-child(2) { animation-delay: 0.05s; }
.section:nth-child(3) { animation-delay: 0.1s; }
.section:nth-child(4) { animation-delay: 0.15s; }
.section:nth-child(5) { animation-delay: 0.2s; }

.dashboard-header {
  margin-bottom: 1.75rem;
}

.dashboard-header h1 {
  font-family: var(--font-display);
  font-size: 2rem;
  font-weight: 400;
  margin: 0 0 0.25rem;
}

.subtitle {
  font-size: 1rem;
  color: var(--color-text-muted);
  margin: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.85rem;
  margin-bottom: 2.25rem;
}

.stat-card--link {
  text-decoration: none;
  color: inherit;
}

.stat-card--link:hover {
  text-decoration: none;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  padding: 1.1rem 1.15rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  transition: border-color 0.18s, background 0.18s, transform 0.18s;
}

.stat-card:hover {
  border-color: rgba(196, 163, 90, 0.45);
  background: rgba(30, 36, 32, 0.95);
  transform: translateY(-1px);
}

.stat-card.alert {
  border-color: rgba(248, 113, 113, 0.45);
  background: rgba(248, 113, 113, 0.06);
}

.stat-icon {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  background: rgba(196, 163, 90, 0.12);
  color: var(--color-accent);
}

.stat-icon--alert {
  background: rgba(248, 113, 113, 0.14);
  color: var(--color-danger);
}

.stat-value {
  font-size: 1.9rem;
  font-weight: 600;
  color: var(--color-text);
  line-height: 1;
  letter-spacing: -0.02em;
  margin-bottom: 0.3rem;
}

.stat-label {
  font-size: 0.78rem;
  color: var(--color-text-muted);
  letter-spacing: 0.02em;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
  gap: 0.75rem;
}

.section-header h2 {
  font-family: var(--font-display);
  font-size: 1.35rem;
  font-weight: 400;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

.section-icon--alert {
  color: var(--color-danger);
}

.badge-alert {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 24px;
  padding: 0 0.5rem;
  background: rgba(248, 113, 113, 0.9);
  color: #0f1210;
  font-size: 0.75rem;
  font-weight: 700;
  border-radius: 12px;
}

.link-button {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.88rem;
  color: var(--color-accent);
  text-decoration: none;
  font-weight: 500;
}

.link-button:hover {
  text-decoration: none;
  filter: brightness(1.1);
}

.loading-state,
.empty-state {
  padding: 1.5rem;
  text-align: center;
  color: var(--color-text-muted);
  font-size: 0.9rem;
  border: 1px dashed var(--color-border);
  border-radius: var(--radius);
}

.empty-state a {
  color: var(--color-accent);
}

.projects-preview {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 0.85rem;
}

.project-preview-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 1.1rem 1.15rem;
  transition: border-color 0.18s;
}

.project-preview-card:hover {
  border-color: rgba(196, 163, 90, 0.45);
}

.project-preview-card h3 {
  font-family: var(--font-body);
  font-size: 0.98rem;
  font-weight: 600;
  margin: 0 0 0.4rem;
}

.project-desc {
  font-size: 0.84rem;
  color: var(--color-text-muted);
  margin: 0 0 0.7rem;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.view-link {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.84rem;
  color: var(--color-accent);
  text-decoration: none;
  font-weight: 500;
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

.task-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.8rem 0.95rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-left: 3px solid var(--color-border);
  border-radius: var(--radius);
  width: 100%;
  text-align: left;
  font-family: inherit;
  color: inherit;
  transition:
    border-color 0.22s ease,
    background 0.22s ease,
    transform 0.2s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.22s ease;
}

.task-item--clickable {
  cursor: pointer;
}

.task-item--clickable:hover {
  border-color: rgba(196, 163, 90, 0.4);
  background: rgba(30, 36, 32, 0.95);
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.18);
}

button.task-item--clickable {
  border: 1px solid var(--color-border);
}

.task-item.overdue {
  border-left-color: var(--color-danger);
}

.task-side {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  flex-shrink: 0;
}

.task-info h4 {
  font-size: 0.92rem;
  font-weight: 600;
  margin: 0 0 0.35rem;
}

.task-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.meta-text {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.78rem;
  color: var(--color-text-muted);
}

.priority-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: 0.28rem 0.5rem;
  border-radius: 4px;
}

.priority-badge.low {
  background: rgba(148, 163, 184, 0.18);
  color: #94a3b8;
}

.priority-badge.medium {
  background: rgba(196, 163, 90, 0.18);
  color: var(--color-accent);
}

.priority-badge.high {
  background: rgba(248, 113, 113, 0.16);
  color: var(--color-danger);
}

.team-preview {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 0.75rem;
}

.team-member {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.85rem 0.95rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
}

.member-avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: var(--color-accent);
  color: #0f1210;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.82rem;
  flex-shrink: 0;
}

.member-info {
  min-width: 0;
}

.member-name {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.member-meta {
  font-size: 0.78rem;
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 0.12rem;
}

@media (max-width: 960px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 560px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
