<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1>Dashboard</h1>
      <p class="subtitle">{{ greeting }}, {{ userName }}</p>
    </div>

    <div class="stats-grid">
      <div v-for="stat in statCards" :key="stat.label" class="stat-card" :class="{ alert: stat.alert }">
        <div class="stat-icon" :class="{ 'stat-icon--alert': stat.alert }">
          <component :is="stat.icon" :size="20" :stroke-width="1.75" />
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
      </div>
    </div>

    <section class="section">
      <div class="section-header">
        <h2>Recent Projects</h2>
        <RouterLink to="/app/projects" class="link-button">View all →</RouterLink>
      </div>
      <div v-if="loadingProjects" class="loading-state">Loading projects…</div>
      <div v-else-if="recentProjects.length === 0" class="empty-state">
        <p>No projects yet. <RouterLink to="/app/projects">Create your first project</RouterLink></p>
      </div>
      <div v-else class="projects-preview">
        <div v-for="project in recentProjects" :key="project.id" class="project-preview-card">
          <h3>{{ project.title }}</h3>
          <p v-if="project.description" class="project-desc">{{ project.description }}</p>
          <RouterLink :to="`/app/projects/${project.id}/tasks`" class="view-link">View tasks →</RouterLink>
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
        <div v-for="task in overdueTasks" :key="task.id" class="task-item overdue">
          <div class="task-info">
            <h4>{{ task.title }}</h4>
            <div class="task-meta">
              <span v-if="task.assignee_id || task.assignee_contact_id" class="meta-text">
                <UserRound :size="13" :stroke-width="1.75" />
                {{ assigneeLabel(task) }}
              </span>
              <span class="meta-text">
                <Calendar :size="13" :stroke-width="1.75" />
                Due {{ formatDate(task.due_date) }}
              </span>
            </div>
          </div>
          <div class="task-side">
            <button
              type="button"
              class="row-icon-btn"
              title="Edit task"
              aria-label="Edit task"
              :disabled="busyTaskId === task.id"
              @click="goEditTask(task)"
            >
              <Pencil :size="15" :stroke-width="1.75" />
            </button>
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
        <RouterLink to="/app/team" class="link-button">Manage team →</RouterLink>
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
  </div>
</template>

<script setup>
import {
  AlertTriangle,
  ArrowDown,
  ArrowUp,
  Calendar,
  CheckSquare,
  FolderKanban,
  Minus,
  Pencil,
  Trash2,
  UserRound,
  Users,
} from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { apiJson } from '@/api/client'
import { getToken } from '@/services/auth'
import { user } from '@/composables/session'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const router = useRouter()
const busyTaskId = ref(null)

const stats = ref({
  projects: 0,
  tasks: 0,
  employees: 0,
  overdue: 0,
})

const recentProjects = ref([])
const overdueTasks = ref([])
const recentEmployees = ref([])
const employees = ref([])
const contacts = ref([])

const loadingProjects = ref(true)
const loadingTeam = ref(true)

const userName = computed(() => user.value?.first_name || 'there')
const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 18) return 'Good afternoon'
  return 'Good evening'
})

const statCards = computed(() => [
  { label: 'Active Projects', value: stats.value.projects, icon: FolderKanban, alert: false },
  { label: 'Total Tasks', value: stats.value.tasks, icon: CheckSquare, alert: false },
  { label: 'Team Members', value: stats.value.employees, icon: Users, alert: false },
  { label: 'Overdue Tasks', value: stats.value.overdue, icon: AlertTriangle, alert: stats.value.overdue > 0 },
])

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
    stats.value.tasks = tasks.length
    const now = new Date()
    overdueTasks.value = tasks
      .filter((t) => t.due_date && new Date(t.due_date) < now && t.status !== 'completed')
      .slice(0, 5)
    stats.value.overdue = overdueTasks.value.length
  } catch (err) {
    console.error('Failed to load tasks:', err)
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

function goEditTask(task) {
  if (task.project_id) {
    router.push(`/app/projects/${task.project_id}/tasks`)
    return
  }
  router.push('/app/tasks')
}

async function deleteOverdueTask(task) {
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

onMounted(fetchDashboardData)
</script>

<style scoped>
.dashboard {
  max-width: 100%;
}

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

.section {
  margin-bottom: 2.25rem;
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
