<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <div>
        <h1>Dashboard</h1>
        <p class="subtitle">{{ greeting }}, {{ userName }}</p>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="quick-actions">
      <router-link to="/app/projects" class="action-card">
        <span class="action-icon">📋</span>
        <span class="action-text">New Project</span>
      </router-link>
      <router-link to="/app/team" class="action-card">
        <span class="action-icon">👥</span>
        <span class="action-text">Invite Employee</span>
      </router-link>
      <router-link to="/app/admin/ai-terminal" class="action-card highlight">
        <span class="action-icon">⚡</span>
        <span class="action-text">AI Terminal</span>
      </router-link>
    </div>

    <!-- Stats Grid -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.projects }}</div>
          <div class="stat-label">Active Projects</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.tasks }}</div>
          <div class="stat-label">Total Tasks</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">👨‍💼</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.employees }}</div>
          <div class="stat-label">Team Members</div>
        </div>
      </div>
      <div class="stat-card" :class="{ alert: stats.overdue > 0 }">
        <div class="stat-icon">⚠️</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.overdue }}</div>
          <div class="stat-label">Overdue Tasks</div>
        </div>
      </div>
    </div>

    <!-- Recent Projects -->
    <section class="section">
      <div class="section-header">
        <h2>Recent Projects</h2>
        <router-link to="/app/projects" class="link-button">View all →</router-link>
      </div>
      <div v-if="loadingProjects" class="loading-state">Loading projects...</div>
      <div v-else-if="recentProjects.length === 0" class="empty-state">
        <p>No projects yet. <router-link to="/app/projects">Create your first project</router-link></p>
      </div>
      <div v-else class="projects-preview">
        <div v-for="project in recentProjects" :key="project.id" class="project-preview-card">
          <h3>{{ project.title }}</h3>
          <p v-if="project.description" class="project-desc">{{ project.description }}</p>
          <router-link :to="`/app/projects/${project.id}/tasks`" class="view-link">View tasks →</router-link>
        </div>
      </div>
    </section>

    <!-- Overdue Tasks -->
    <section class="section" v-if="overdueTasks.length > 0">
      <div class="section-header">
        <h2>⚠️ Overdue Tasks</h2>
        <span class="badge-alert">{{ overdueTasks.length }}</span>
      </div>
      <div class="tasks-list">
        <div v-for="task in overdueTasks" :key="task.id" class="task-item overdue">
          <div class="task-info">
            <h4>{{ task.title }}</h4>
            <div class="task-meta">
              <span v-if="task.assignee_id || task.assignee_contact_id" class="meta-text">👤 {{ assigneeLabel(task) }}</span>
              <span class="meta-text">📅 Due {{ formatDate(task.due_date) }}</span>
            </div>
          </div>
          <span class="priority-badge" :class="task.priority">{{ task.priority }}</span>
        </div>
      </div>
    </section>

    <!-- Recent Team Activity -->
    <section class="section">
      <div class="section-header">
        <h2>Team</h2>
        <router-link to="/app/team" class="link-button">Manage team →</router-link>
      </div>
      <div v-if="loadingTeam" class="loading-state">Loading team...</div>
      <div v-else-if="recentEmployees.length === 0" class="empty-state">
        <p>No team members yet. <router-link to="/app/team">Add your first member</router-link></p>
      </div>
      <div v-else class="team-preview">
        <div v-for="emp in recentEmployees" :key="emp.key" class="team-member">
          <div class="member-avatar">{{ getInitials(emp.full_name) }}</div>
          <div class="member-info">
            <div class="member-name">{{ emp.full_name }}</div>
            <div class="member-position">{{ emp.position || 'Member' }}</div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { getToken } from '@/services/auth'
import { user } from '@/composables/session'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

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

const userName = computed(() => user.value?.full_name || 'there')
const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 18) return 'Good afternoon'
  return 'Good evening'
})

async function fetchDashboardData() {
  const token = getToken()

  try {
    // Fetch projects
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
    // Fetch all tasks
    const tasksRes = await axios.get(`${API_URL}/api/v1/tasks`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    const tasks = tasksRes.data
    stats.value.tasks = tasks.length

    // Filter overdue tasks
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
      axios.get(`${API_URL}/api/v1/contacts`, {
        headers: { Authorization: `Bearer ${token}` },
      }).catch(() => ({ data: [] })),
    ])
    employees.value = employeesRes.data
    contacts.value = Array.isArray(contactsRes.data) ? contactsRes.data : []
    const contactEmails = new Set(contacts.value.map((c) => (c.email || '').toLowerCase()))
    const preview = [
      ...contacts.value.map((c) => ({
        key: `c-${c.id}`,
        full_name: c.name,
        position: c.role || 'Member',
      })),
      ...employees.value
        .filter((e) => !contactEmails.has((e.email || '').toLowerCase()))
        .map((e) => ({
          key: `u-${e.id}`,
          full_name: e.full_name,
          position: e.position || 'Employee',
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

function getInitials(name) {
  return name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

function formatDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  const now = new Date()
  const diffTime = now - date
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) return 'today'
  if (diffDays === 1) return 'yesterday'
  return `${diffDays} days ago`
}

onMounted(() => {
  fetchDashboardData()
})
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.dashboard-header {
  margin-bottom: 2rem;
}

.dashboard-header h1 {
  font-size: 2rem;
  font-weight: 600;
  margin: 0 0 0.25rem;
}

.subtitle {
  font-size: 1rem;
  color: var(--color-text-muted);
  margin: 0;
}

/* Quick Actions */
.quick-actions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.action-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  text-decoration: none;
  transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s;
}

.action-card:hover {
  border-color: var(--color-accent);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  text-decoration: none;
}

.action-card.highlight {
  background: linear-gradient(135deg, rgba(196,163,90,0.15), rgba(196,163,90,0.05));
  border-color: rgba(196,163,90,0.4);
}

.action-icon {
  font-size: 1.5rem;
}

.action-text {
  font-weight: 600;
  font-size: 0.9rem;
  color: var(--color-text);
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2.5rem;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.25rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
}

.stat-card.alert {
  border-color: #ef4444;
  background: rgba(239, 68, 68, 0.05);
}

.stat-icon {
  font-size: 2rem;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-text);
  line-height: 1;
  margin-bottom: 0.25rem;
}

.stat-label {
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

/* Sections */
.section {
  margin-bottom: 2.5rem;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.25rem;
}

.section-header h2 {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.badge-alert {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 24px;
  padding: 0 0.5rem;
  background: #ef4444;
  color: white;
  font-size: 0.75rem;
  font-weight: 700;
  border-radius: 12px;
}

.link-button {
  font-size: 0.9rem;
  color: var(--color-accent);
  text-decoration: none;
  font-weight: 500;
  transition: opacity 0.2s;
}

.link-button:hover {
  opacity: 0.8;
  text-decoration: none;
}

.loading-state, .empty-state {
  padding: 2rem;
  text-align: center;
  color: var(--color-text-muted);
  font-size: 0.9rem;
}

.empty-state a {
  color: var(--color-accent);
  text-decoration: none;
}

.empty-state a:hover {
  text-decoration: underline;
}

/* Projects Preview */
.projects-preview {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}

.project-preview-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 1.25rem;
  transition: border-color 0.2s;
}

.project-preview-card:hover {
  border-color: var(--color-accent);
}

.project-preview-card h3 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 0.5rem;
  color: var(--color-text);
}

.project-desc {
  font-size: 0.85rem;
  color: var(--color-text-muted);
  margin: 0 0 0.75rem;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.view-link {
  font-size: 0.85rem;
  color: var(--color-accent);
  text-decoration: none;
  font-weight: 500;
}

.view-link:hover {
  text-decoration: underline;
}

/* Tasks List */
.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.task-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-left: 3px solid var(--color-border);
  border-radius: var(--radius);
}

.task-item.overdue {
  border-left-color: #ef4444;
}

.task-info h4 {
  font-size: 0.95rem;
  font-weight: 600;
  margin: 0 0 0.5rem;
  color: var(--color-text);
}

.task-meta {
  display: flex;
  gap: 1rem;
}

.meta-text {
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.priority-badge {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  padding: 0.25rem 0.6rem;
  border-radius: 4px;
}

.priority-badge.low {
  background: rgba(148, 163, 184, 0.2);
  color: #94a3b8;
}

.priority-badge.medium {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
}

.priority-badge.high {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

/* Team Preview */
.team-preview {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.team-member {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
}

.member-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--color-accent);
  color: #0f1210;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.9rem;
  flex-shrink: 0;
}

.member-name {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text);
}

.member-position {
  font-size: 0.8rem;
  color: var(--color-text-muted);
}
</style>