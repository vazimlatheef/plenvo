<template>
  <div class="app-page">
    <div class="app-page-header">
      <h1>Projects</h1>
      <button type="button" class="btn-primary btn-with-icon" @click="showCreateModal = true">
        <Plus :size="16" :stroke-width="2" />
        New project
      </button>
    </div>

    <p v-if="loading" class="muted-line">Loading projects…</p>
    <p v-else-if="error" class="error-line">{{ error }}</p>

    <div v-else-if="projects.length === 0" class="empty-panel">
      <p>No projects yet — create the first one</p>
      <button type="button" class="btn-primary btn-with-icon" @click="showCreateModal = true">
        <Plus :size="16" :stroke-width="2" />
        Create project
      </button>
    </div>

    <ul v-else class="dense-list">
      <li v-for="project in projects" :key="project.id" class="dense-row project-row">
        <span
          class="avatar avatar--lg"
          :class="`avatar-tone-${avatarTone(project.id || project.title)}`"
        >
          {{ getInitials(project.title) }}
        </span>
        <div class="dense-row__meta project-meta">
          <span class="dense-row__title">{{ project.title }}</span>
          <span class="project-desc">{{ project.description || 'No description' }}</span>
        </div>
        <span class="dense-row__due">{{ formatDate(project.created_at) }}</span>
        <RouterLink :to="`/app/projects/${project.id}/tasks`" class="btn-outline link-btn btn-with-icon">
          View tasks
          <ArrowRight :size="14" :stroke-width="1.75" />
        </RouterLink>
      </li>
    </ul>

    <div v-if="showCreateModal" class="modal-overlay" @click.self="cancelCreate">
      <div class="modal-panel">
        <button type="button" class="modal-close" aria-label="Close" @click="cancelCreate">
          <X :size="18" :stroke-width="1.75" />
        </button>
        <h2>Create new project</h2>
        <form class="field-stack" @submit.prevent="createProject">
          <label>
            Project name *
            <input
              v-model="newProject.title"
              type="text"
              placeholder="e.g., Website Redesign"
              required
              maxlength="100"
              :disabled="creating"
            />
          </label>
          <label>
            Description
            <textarea
              v-model="newProject.description"
              placeholder="Brief description (optional)"
              rows="3"
              maxlength="500"
              :disabled="creating"
            />
          </label>
          <p v-if="createError" class="error-line">{{ createError }}</p>
          <div class="modal-actions">
            <button type="button" class="btn-outline" :disabled="creating" @click="cancelCreate">Cancel</button>
            <button type="submit" class="btn-primary" :disabled="creating">
              {{ creating ? 'Creating…' : 'Create project' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ArrowRight, Plus, X } from '@lucide/vue'
import { onMounted, ref } from 'vue'

import { apiJson } from '@/api/client'
import { avatarTone, getInitials } from '@/utils/ui'

const projects = ref([])
const loading = ref(true)
const error = ref('')

const showCreateModal = ref(false)
const newProject = ref({ title: '', description: '' })
const creating = ref(false)
const createError = ref('')

function formatDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

async function fetchProjects() {
  try {
    loading.value = true
    error.value = ''
    projects.value = await apiJson('/api/v1/projects')
  } catch (err) {
    console.error('[AdminProjects] load failed', err)
    error.value = err.message || 'Failed to load projects'
  } finally {
    loading.value = false
  }
}

async function createProject() {
  if (!newProject.value.title.trim()) return

  try {
    creating.value = true
    createError.value = ''
    const created = await apiJson('/api/v1/projects', {
      method: 'POST',
      body: JSON.stringify({
        title: newProject.value.title.trim(),
        description: newProject.value.description.trim() || null,
      }),
    })
    projects.value.unshift(created)
    cancelCreate()
  } catch (err) {
    console.error('[AdminProjects] create failed', err)
    createError.value = err.message || 'Failed to create project'
  } finally {
    creating.value = false
  }
}

function cancelCreate() {
  showCreateModal.value = false
  newProject.value = { title: '', description: '' }
  createError.value = ''
}

onMounted(fetchProjects)
</script>

<style scoped>
.project-row {
  grid-template-columns: 36px minmax(0, 1fr) auto auto;
}

.project-meta {
  flex-direction: column;
  align-items: flex-start;
  gap: 0.15rem;
}

.project-desc {
  font-size: 0.78rem;
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.link-btn {
  text-decoration: none;
  display: inline-flex;
  align-items: center;
}

.link-btn:hover {
  text-decoration: none;
}

.btn-with-icon {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}
</style>
