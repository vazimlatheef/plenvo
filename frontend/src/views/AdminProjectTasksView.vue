<template>
  <div class="app-page tasks-page">
    <div class="app-page-header">
      <div>
        <RouterLink to="/app/projects" class="app-back">
          <ArrowLeft :size="14" :stroke-width="1.75" />
          Projects
        </RouterLink>
        <h1>{{ project?.title || 'Project tasks' }}</h1>
        <p v-if="project?.description" class="app-lede">{{ project.description }}</p>
        <LinksList v-if="project?.links?.length" :links="project.links" class="project-links" />
      </div>
      <div class="header-actions">
        <button
          type="button"
          class="btn-outline btn-with-icon"
          :disabled="writeRestricted"
          :title="writeDisabledTitle"
          @click="openProjectEdit"
        >
          <Pencil :size="15" :stroke-width="1.75" />
          Edit details
        </button>
        <button
          type="button"
          class="btn-primary"
          :disabled="writeRestricted"
          :title="writeDisabledTitle"
          @click="openCreate"
        >
        <Plus :size="16" :stroke-width="2" />
        New task
      </button>
      </div>
    </div>

    <p v-if="loading" class="muted-line">Loading tasks…</p>
    <p v-else-if="error" class="error-line">{{ error }}</p>

    <div v-else-if="!tasks.length" class="empty-panel">
      <ClipboardList class="empty-icon" :size="28" :stroke-width="1.5" />
      <p>No tasks yet — create the first one</p>
      <button
        type="button"
        class="btn-primary"
        :disabled="writeRestricted"
        :title="writeDisabledTitle"
        @click="openCreate"
      >
        <Plus :size="16" :stroke-width="2" />
        Create task
      </button>
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
              <button type="button" class="dense-row__title" @click="openEdit(task)">
                {{ task.title }}
              </button>
              <p v-if="task.description" class="task-notes">{{ task.description }}</p>
              <LinksList :links="task.links" compact class="task-links" />
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
      :mode="editingTaskId ? 'edit' : 'create'"
      :saving="saving"
      :error="formError"
      :assignee-options="assigneeOptions"
      :initial="modalInitial"
      @close="closeModal"
      @save="saveFromModal"
    />

    <div v-if="showProjectModal" class="modal-overlay" @click.self="closeProjectEdit">
      <div class="modal-panel">
        <button type="button" class="modal-close" aria-label="Close" @click="closeProjectEdit">
          <X :size="18" :stroke-width="1.75" />
        </button>
        <h2>Project details</h2>
        <form class="field-stack" @submit.prevent="saveProjectDetails">
          <label>
            Description
            <textarea
              v-model="projectForm.description"
              placeholder="Brief description (optional)"
              rows="3"
              maxlength="500"
              :disabled="savingProject"
            />
          </label>
          <LinksEditor v-model="projectForm.links" :disabled="savingProject" />
          <p v-if="projectFormError" class="error-line">{{ projectFormError }}</p>
          <div class="modal-actions">
            <button type="button" class="btn-outline" :disabled="savingProject" @click="closeProjectEdit">
              Cancel
            </button>
            <button type="submit" class="btn-primary" :disabled="savingProject">
              {{ savingProject ? 'Saving…' : 'Save changes' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ArrowLeft, Calendar, ClipboardList, Pencil, Plus, Trash2, UserRound, X } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import { apiJson } from '@/api/client'
import TaskEditModal from '@/components/TaskEditModal.vue'
import LinksEditor from '@/components/LinksEditor.vue'
import LinksList from '@/components/LinksList.vue'
import { linksForApi } from '@/utils/links'
import { user } from '@/composables/session'
import { useWriteAccess } from '@/composables/useWriteAccess'
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

const route = useRoute()
const { writeRestricted, writeDisabledTitle } = useWriteAccess()

const project = ref(null)
const tasks = ref([])
const team = ref([])
const contacts = ref([])
const usersById = ref({})
const contactsById = ref({})
const loading = ref(true)
const error = ref('')
const busyId = ref(null)
const flashId = ref(null)
let flashTimer = null

const showModal = ref(false)
const editingTaskId = ref(null)
const saving = ref(false)
const formError = ref('')
const modalInitial = ref({
  title: '',
  description: '',
  links: [],
  assignee_key: null,
  due_date: '',
  status: 'pending',
})

const showProjectModal = ref(false)
const savingProject = ref(false)
const projectFormError = ref('')
const projectForm = ref({ description: '', links: [] })

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

const assigneeOptions = computed(() =>
  buildAssigneeOptions({
    users: team.value,
    contacts: contacts.value,
    currentUser: user.value,
  }),
)

function assigneeName(task) {
  return resolveAssigneeName(task, {
    usersById: usersById.value,
    contactsById: contactsById.value,
    fallback: 'Unassigned',
  })
}

function assigneeSeed(task) {
  return task.assignee_id || task.assignee_contact_id || task.title
}

function triggerFlash(taskId) {
  flashId.value = taskId
  if (flashTimer) clearTimeout(flashTimer)
  flashTimer = setTimeout(() => {
    flashId.value = null
  }, 700)
}

function resetForm() {
  modalInitial.value = {
    title: '',
    description: '',
    links: [],
    assignee_key: null,
    due_date: '',
    status: 'pending',
  }
  formError.value = ''
  editingTaskId.value = null
}

function openProjectEdit() {
  if (writeRestricted.value) return
  if (!project.value) return
  projectForm.value = {
    description: project.value.description || '',
    links: Array.isArray(project.value.links) ? project.value.links.map((l) => ({ ...l })) : [],
  }
  projectFormError.value = ''
  showProjectModal.value = true
}

function closeProjectEdit() {
  showProjectModal.value = false
  projectFormError.value = ''
}

async function saveProjectDetails() {
  if (!projectId.value) return
  savingProject.value = true
  projectFormError.value = ''
  try {
    const updated = await apiJson(`/api/v1/projects/${projectId.value}`, {
      method: 'PATCH',
      body: JSON.stringify({
        description: projectForm.value.description.trim() || null,
        links: linksForApi(projectForm.value.links),
      }),
    })
    project.value = { ...project.value, ...updated }
    closeProjectEdit()
  } catch (err) {
    console.error('[AdminProjectTasks] project save failed', err)
    projectFormError.value = err.message || 'Failed to save project'
  } finally {
    savingProject.value = false
  }
}

function openCreate() {
  if (writeRestricted.value) return
  resetForm()
  showModal.value = true
}

function openEdit(task) {
  if (writeRestricted.value) return
  editingTaskId.value = task.id
  modalInitial.value = {
    title: task.title || '',
    description: task.description || '',
    links: task.links || [],
    assignee_key: taskAssigneeKey(task),
    due_date: task.due_date ? String(task.due_date).slice(0, 10) : '',
    status: task.status || 'pending',
  }
  formError.value = ''
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  resetForm()
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
    const [proj, taskList, users, contactList] = await Promise.all([
      apiJson(`/api/v1/projects/${projectId.value}`),
      apiJson(`/api/v1/tasks?project_id=${projectId.value}`),
      apiJson('/api/v1/users').catch((err) => {
        console.error('[AdminProjectTasks] failed to load users', err)
        return []
      }),
      apiJson('/api/v1/contacts').catch((err) => {
        console.error('[AdminProjectTasks] failed to load contacts', err)
        return []
      }),
    ])

    project.value = proj
    tasks.value = Array.isArray(taskList) ? taskList : []
    team.value = Array.isArray(users) ? users : []
    contacts.value = Array.isArray(contactList) ? contactList : []
    const map = {}
    for (const u of team.value) map[u.id] = u
    if (user.value?.id != null) map[user.value.id] = map[user.value.id] || user.value
    usersById.value = map
    const cmap = {}
    for (const c of contacts.value) cmap[c.id] = c
    contactsById.value = cmap
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

function buildAssigneePayload(assigneeKey) {
  const { assignee_id, assignee_contact_id } = parseAssigneeKey(assigneeKey)
  if (!assignee_id && !assignee_contact_id) {
    return { clear_assignee: true }
  }
  return { assignee_id, assignee_contact_id }
}

async function saveFromModal(payload) {
  if (!payload.title.trim()) return

  saving.value = true
  formError.value = ''
  try {
    const assigneePayload = buildAssigneePayload(payload.assignee_key)
    if (editingTaskId.value) {
      const updated = await apiJson(`/api/v1/tasks/${editingTaskId.value}`, {
        method: 'PATCH',
        body: JSON.stringify({
          title: payload.title.trim(),
          description: payload.description,
          links: payload.links,
          status: payload.status || 'pending',
          due_date: payload.due_date || null,
          ...assigneePayload,
        }),
      })
      const idx = tasks.value.findIndex((t) => t.id === editingTaskId.value)
      if (idx !== -1) tasks.value[idx] = { ...tasks.value[idx], ...updated }
      triggerFlash(updated.id)
    } else {
      if (!projectId.value) return
      const { clear_assignee, ...assignees } = assigneePayload
      const created = await apiJson('/api/v1/tasks', {
        method: 'POST',
        body: JSON.stringify({
          title: payload.title.trim(),
          description: payload.description,
          links: payload.links,
          project_id: projectId.value,
          status: payload.status || 'pending',
          due_date: payload.due_date || null,
          assignee_id: assignees.assignee_id ?? null,
          assignee_contact_id: assignees.assignee_contact_id ?? null,
        }),
      })
      tasks.value = [created, ...tasks.value]
    }
    closeModal()
  } catch (err) {
    console.error('[AdminProjectTasks] save task failed', err)
    formError.value = err.message || 'Failed to save task'
  } finally {
    saving.value = false
  }
}

async function confirmDelete(task) {
  if (writeRestricted.value) return
  if (!window.confirm('Delete this task?')) return

  busyId.value = task.id
  error.value = ''
  try {
    await apiJson(`/api/v1/tasks/${task.id}`, { method: 'DELETE' })
    tasks.value = tasks.value.filter((t) => t.id !== task.id)
  } catch (err) {
    console.error('[AdminProjectTasks] delete failed', err)
    error.value = err.message || 'Failed to delete task'
  } finally {
    busyId.value = null
  }
}

onMounted(loadPage)
watch(projectId, (id, prev) => {
  if (id && id !== prev) loadPage()
})
</script>

<style scoped>
.app-back {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.project-links {
  margin-top: 0.45rem;
}

.btn-with-icon {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}

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
