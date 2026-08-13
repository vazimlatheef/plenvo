<template>
  <div class="projects-page">
    <div class="page-header">
      <h1>Projects</h1>
      <button @click="showCreateModal = true" class="btn-primary">+ New Project</button>
    </div>

    <div v-if="loading" class="loading">Loading projects...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    
    <div v-else-if="projects.length === 0" class="empty-state">
      <p>No projects yet. Create your first project to get started.</p>
    </div>

    <div v-else class="projects-grid">
      <div v-for="project in projects" :key="project.id" class="project-card">
        <div class="project-header">
          <h3>{{ project.title }}</h3>
          <span class="project-date">{{ formatDate(project.created_at) }}</span>
        </div>
        <p v-if="project.description" class="project-desc">{{ project.description }}</p>
        <p v-else class="project-desc empty">No description</p>
        <div class="project-actions">
          <router-link :to="`/app/projects/${project.id}/tasks`" class="btn-outline-sm">
            View Tasks →
          </router-link>
        </div>
      </div>
    </div>

    <!-- Create Project Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal">
        <h2>Create New Project</h2>
        <form @submit.prevent="createProject">
          <div class="form-group">
            <label for="title">Project name *</label>
            <input
              id="title"
              v-model="newProject.title"
              type="text"
              placeholder="e.g., Website Redesign"
              required
              maxlength="100"
            />
          </div>
          <div class="form-group">
            <label for="description">Description</label>
            <textarea
              id="description"
              v-model="newProject.description"
              placeholder="Brief description of the project (optional)"
              rows="3"
              maxlength="500"
            />
          </div>
          <div v-if="createError" class="error-msg">{{ createError }}</div>
          <div class="modal-actions">
            <button type="button" @click="cancelCreate" class="btn-outline">Cancel</button>
            <button type="submit" :disabled="creating" class="btn-primary">
              {{ creating ? 'Creating...' : 'Create Project' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { getToken } from '@/services/auth'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const projects = ref([])
const loading = ref(true)
const error = ref(null)

const showCreateModal = ref(false)
const newProject = ref({ title: '', description: '' })
const creating = ref(false)
const createError = ref(null)

async function fetchProjects() {
  try {
    loading.value = true
    error.value = null
    const token = getToken()
    const response = await axios.get(`${API_URL}/api/v1/projects`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    projects.value = response.data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to load projects'
  } finally {
    loading.value = false
  }
}

async function createProject() {
  if (!newProject.value.title.trim()) return

  try {
    creating.value = true
    createError.value = null
    const token = getToken()
    const response = await axios.post(
      `${API_URL}/api/v1/projects`,
      {
        title: newProject.value.title.trim(),
        description: newProject.value.description.trim() || null,
      },
      { headers: { Authorization: `Bearer ${token}` } }
    )
    projects.value.unshift(response.data)
    showCreateModal.value = false
    newProject.value = { title: '', description: '' }
  } catch (err) {
    createError.value = err.response?.data?.detail || 'Failed to create project'
  } finally {
    creating.value = false
  }
}

function cancelCreate() {
  showCreateModal.value = false
  newProject.value = { name: '', description: '' }
  createError.value = null
}

function formatDate(dateString) {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

onMounted(() => {
  fetchProjects()
})
</script>

<style scoped>
.projects-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 2rem;
}

.page-header h1 {
  font-size: 1.75rem;
  font-weight: 600;
  margin: 0;
}

.loading, .error, .empty-state {
  text-align: center;
  padding: 3rem;
  color: var(--color-text-muted);
}

.error {
  color: #ef4444;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.25rem;
}

.project-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 1.5rem;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.project-card:hover {
  border-color: var(--color-accent);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.project-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.project-header h3 {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0;
  color: var(--color-text);
}

.project-date {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  white-space: nowrap;
}

.project-desc {
  font-size: 0.9rem;
  color: var(--color-text-muted);
  line-height: 1.5;
  margin: 0 0 1rem;
}

.project-desc.empty {
  font-style: italic;
  opacity: 0.6;
}

.project-actions {
  display: flex;
  gap: 0.75rem;
}

.btn-primary {
  background: var(--color-accent);
  color: #0f1210;
  border: none;
  padding: 0.6rem 1.25rem;
  border-radius: var(--radius);
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: filter 0.2s;
}

.btn-primary:hover {
  filter: brightness(1.1);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-outline-sm {
  display: inline-block;
  padding: 0.5rem 1rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--color-text);
  text-decoration: none;
  transition: border-color 0.2s, color 0.2s;
}

.btn-outline-sm:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
  text-decoration: none;
}

.btn-outline {
  background: transparent;
  border: 1px solid var(--color-border);
  color: var(--color-text);
  padding: 0.6rem 1.25rem;
  border-radius: var(--radius);
  font-weight: 500;
  font-size: 0.9rem;
  cursor: pointer;
  transition: border-color 0.2s;
}

.btn-outline:hover {
  border-color: var(--color-accent);
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 1rem;
}

.modal {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 2rem;
  max-width: 500px;
  width: 100%;
}

.modal h2 {
  font-size: 1.4rem;
  font-weight: 600;
  margin: 0 0 1.5rem;
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  font-size: 0.9rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: var(--color-text);
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 0.65rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-bg);
  color: var(--color-text);
  font-family: inherit;
  font-size: 0.9rem;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--color-accent);
}

.error-msg {
  color: #ef4444;
  font-size: 0.85rem;
  margin-bottom: 1rem;
}

.modal-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}
</style>