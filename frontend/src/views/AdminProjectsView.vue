<template>
  <div class="app-page">
    <div class="app-page-header">
      <h1>Projects</h1>
      <button
        type="button"
        class="btn-primary btn-with-icon"
        :disabled="writeRestricted"
        :title="writeDisabledTitle"
        @click="openCreateModal"
      >
        <Plus :size="16" :stroke-width="2" />
        New project
      </button>
    </div>

    <p v-if="loading" class="muted-line">Loading projects…</p>
    <p v-else-if="error" class="error-line">{{ error }}</p>

    <div v-else-if="projects.length === 0" class="empty-panel">
      <p>No projects yet — create the first one</p>
      <button
        type="button"
        class="btn-primary btn-with-icon"
        :disabled="writeRestricted"
        :title="writeDisabledTitle"
        @click="openCreateModal"
      >
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
          <LinksList v-if="project.links?.length" :links="project.links" compact class="project-row-links" />
        </div>
        <span class="dense-row__due">{{ formatDate(project.created_at) }}</span>
        <div class="project-row-actions">
          <button
            type="button"
            class="row-icon-btn"
            aria-label="Edit project"
            :disabled="writeRestricted"
            :title="writeRestricted ? writeDisabledTitle : 'Edit project'"
            @click="openEditModal(project)"
          >
            <Pencil :size="15" :stroke-width="1.75" />
          </button>
          <RouterLink :to="`/app/projects/${project.id}/tasks`" class="btn-outline link-btn btn-with-icon">
            View tasks
            <ArrowRight :size="14" :stroke-width="1.75" />
          </RouterLink>
        </div>
      </li>
    </ul>

    <div v-if="showEditModal" class="modal-overlay" @click.self="cancelEdit">
      <div class="modal-panel">
        <button type="button" class="modal-close" aria-label="Close" @click="cancelEdit">
          <X :size="18" :stroke-width="1.75" />
        </button>
        <h2>Edit project</h2>
        <form class="field-stack" @submit.prevent="saveProject">
          <label>
            Project name *
            <input
              v-model="editProject.title"
              type="text"
              required
              maxlength="100"
              :disabled="savingEdit"
            />
          </label>
          <label>
            Description
            <textarea
              v-model="editProject.description"
              rows="3"
              maxlength="500"
              :disabled="savingEdit"
            />
          </label>
          <LinksEditor v-model="editProject.links" :disabled="savingEdit" />
          <p v-if="editError" class="error-line">{{ editError }}</p>
          <div class="modal-actions">
            <button type="button" class="btn-outline" :disabled="savingEdit" @click="cancelEdit">Cancel</button>
            <button type="submit" class="btn-primary" :disabled="savingEdit">
              {{ savingEdit ? 'Saving…' : 'Save changes' }}
            </button>
          </div>
        </form>
      </div>
    </div>

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
          <LinksEditor v-model="newProject.links" :disabled="creating" />
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
import { ArrowRight, Pencil, Plus, X } from '@lucide/vue'
import { onMounted, ref } from 'vue'

import { apiJson } from '@/api/client'
import LinksEditor from '@/components/LinksEditor.vue'
import LinksList from '@/components/LinksList.vue'
import { linksForApi } from '@/utils/links'
import { useWriteAccess } from '@/composables/useWriteAccess'
import { avatarTone, getInitials } from '@/utils/ui'

const { writeRestricted, writeDisabledTitle } = useWriteAccess()

const projects = ref([])
const loading = ref(true)
const error = ref('')

const showCreateModal = ref(false)
const showEditModal = ref(false)
const editingProjectId = ref(null)
const newProject = ref({ title: '', description: '', links: [] })
const editProject = ref({ title: '', description: '', links: [] })
const creating = ref(false)
const savingEdit = ref(false)
const createError = ref('')
const editError = ref('')

function openCreateModal() {
  if (writeRestricted.value) return
  showCreateModal.value = true
}

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
        links: linksForApi(newProject.value.links),
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

function openEditModal(project) {
  if (writeRestricted.value) return
  editingProjectId.value = project.id
  editProject.value = {
    title: project.title || '',
    description: project.description || '',
    links: Array.isArray(project.links) ? project.links.map((l) => ({ ...l })) : [],
  }
  editError.value = ''
  showEditModal.value = true
}

function cancelEdit() {
  showEditModal.value = false
  editingProjectId.value = null
  editProject.value = { title: '', description: '', links: [] }
  editError.value = ''
}

async function saveProject() {
  if (!editProject.value.title.trim() || !editingProjectId.value) return
  savingEdit.value = true
  editError.value = ''
  try {
    const updated = await apiJson(`/api/v1/projects/${editingProjectId.value}`, {
      method: 'PATCH',
      body: JSON.stringify({
        title: editProject.value.title.trim(),
        description: editProject.value.description.trim() || null,
        links: linksForApi(editProject.value.links),
      }),
    })
    const idx = projects.value.findIndex((p) => p.id === updated.id)
    if (idx !== -1) projects.value[idx] = { ...projects.value[idx], ...updated }
    cancelEdit()
  } catch (err) {
    console.error('[AdminProjects] edit failed', err)
    editError.value = err.message || 'Failed to save project'
  } finally {
    savingEdit.value = false
  }
}

function cancelCreate() {
  showCreateModal.value = false
  newProject.value = { title: '', description: '', links: [] }
  createError.value = ''
}

onMounted(fetchProjects)
</script>

<style scoped>
.project-row {
  grid-template-columns: 36px minmax(0, 1fr) auto auto;
}

.project-row-actions {
  display: flex;
  align-items: center;
  gap: 0.4rem;
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

.project-row-links {
  width: 100%;
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
