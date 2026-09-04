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
        <TaskViewModeToggle v-if="tasks.length" v-model="viewMode" />
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

    <TaskKanbanBoard
      v-else-if="viewMode === 'kanban'"
      :tasks="tasks"
      :busy-id="busyId"
      :flash-id="flashId"
      :write-restricted="writeRestricted"
      :write-disabled-title="writeDisabledTitle"
      :assignee-name="assigneeName"
      :assignee-seed="assigneeSeed"
      @status-change="onStatusChange"
      @edit="openEdit"
      @delete="confirmDelete"
    />

    <TaskListView
      v-else
      :status-groups="statusGroups"
      :busy-id="busyId"
      :flash-id="flashId"
      :write-restricted="writeRestricted"
      :write-disabled-title="writeDisabledTitle"
      :assignee-name="assigneeName"
      :assignee-seed="assigneeSeed"
      @status-change="onStatusChange"
      @edit="openEdit"
      @delete="confirmDelete"
    />

    <TaskEditModal
      :open="showModal"
      :mode="editingTaskId ? 'edit' : 'create'"
      :saving="saving"
      :error="formError"
      :assignee-options="assigneeOptions"
      :show-project="true"
      :projects="allProjects"
      :allow-delete="!!editingTaskId && !writeRestricted"
      :initial="modalInitial"
      @close="closeModal"
      @save="saveFromModal"
      @delete="deleteFromModal"
    />

    <div v-if="showProjectModal" class="modal-overlay" @click.self="closeProjectEdit">
      <div class="modal-panel">
        <button type="button" class="modal-close" aria-label="Close" @click="closeProjectEdit">
          <X :size="18" :stroke-width="1.75" />
        </button>
        <h2>Project details</h2>
        <form class="field-stack" @submit.prevent="saveProjectDetails">
          <label>
            Project name *
            <input
              v-model="projectForm.title"
              type="text"
              required
              maxlength="100"
              :disabled="savingProject"
            />
          </label>
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
import { ArrowLeft, ClipboardList, Pencil, Plus, X } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import { apiJson } from '@/api/client'
import { normalizeDueTime, sortStatusTasksByDue } from '@/utils/taskDue'
import TaskEditModal from '@/components/TaskEditModal.vue'
import TaskKanbanBoard from '@/components/TaskKanbanBoard.vue'
import TaskListView from '@/components/TaskListView.vue'
import TaskViewModeToggle from '@/components/TaskViewModeToggle.vue'
import LinksEditor from '@/components/LinksEditor.vue'
import LinksList from '@/components/LinksList.vue'
import { linksForApi } from '@/utils/links'
import { user } from '@/composables/session'
import { useTaskViewMode } from '@/composables/useTaskViewMode'
import { useWriteAccess } from '@/composables/useWriteAccess'
import {
  buildAssigneeOptions,
  currentUserAssigneeKey,
  parseAssigneeKey,
  resolveAssigneeName,
  taskAssigneeKey,
} from '@/utils/assignee'
import { STATUS_GROUPS } from '@/utils/ui'
import { confirmDeleteTask, removeDeletedTask } from '@/utils/recurrence'

const route = useRoute()
const { viewMode } = useTaskViewMode('kanban')
const { writeRestricted, writeDisabledTitle } = useWriteAccess()

const project = ref(null)
const allProjects = ref([])
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
  due_time: '',
  status: 'pending',
  priority: 'medium',
  project_id: null,
})

const showProjectModal = ref(false)
const savingProject = ref(false)
const projectFormError = ref('')
const projectForm = ref({ title: '', description: '', links: [] })

const projectId = computed(() => {
  const id = Number(route.params.projectId)
  return Number.isFinite(id) && id > 0 ? id : null
})

const statusGroups = computed(() =>
  STATUS_GROUPS.map((group) => ({
    ...group,
    tasks: sortStatusTasksByDue(tasks.value.filter((t) => t.status === group.key), group.key),
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
    assignee_key: currentUserAssigneeKey(user.value),
    due_date: '',
    due_time: '',
    recurrence: 'none',
    status: 'pending',
    priority: 'medium',
    project_id: projectId.value,
  }
  formError.value = ''
  editingTaskId.value = null
}

function openProjectEdit() {
  if (writeRestricted.value) return
  if (!project.value) return
  projectForm.value = {
    title: project.value.title || '',
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
        title: projectForm.value.title.trim(),
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
    due_time: normalizeDueTime(task.due_time),
    recurrence: task.recurrence || 'none',
    series_id: task.series_id || null,
    status: task.status || 'pending',
    priority: task.priority || 'medium',
    project_id: task.project_id ?? projectId.value,
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
    const [proj, taskList, users, contactList, projectList] = await Promise.all([
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
      apiJson('/api/v1/projects').catch(() => []),
    ])

    project.value = proj
    allProjects.value = Array.isArray(projectList) ? projectList : []
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

async function onStatusChange({ task, status: next }) {
  if (writeRestricted.value) return
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
          priority: payload.priority || 'medium',
          due_date: payload.due_date || null,
          due_time: payload.due_date && payload.due_time ? payload.due_time : null,
          project_id: payload.project_id ?? null,
          ...assigneePayload,
        }),
      })
      if (updated.project_id !== projectId.value) {
        tasks.value = tasks.value.filter((t) => t.id !== updated.id)
      } else {
        const idx = tasks.value.findIndex((t) => t.id === editingTaskId.value)
        if (idx !== -1) tasks.value[idx] = { ...tasks.value[idx], ...updated }
        triggerFlash(updated.id)
      }
    } else {
      if (!projectId.value) return
      const { clear_assignee, ...assignees } = assigneePayload
      const created = await apiJson('/api/v1/tasks', {
        method: 'POST',
        body: JSON.stringify({
          title: payload.title.trim(),
          description: payload.description,
          links: payload.links,
          project_id: payload.project_id || projectId.value,
          status: payload.status || 'pending',
          priority: payload.priority || 'medium',
          due_date: payload.due_date || null,
          due_time: payload.due_date && payload.due_time ? payload.due_time : null,
          recurrence: payload.recurrence || 'none',
          assignee_id: assignees.assignee_id ?? null,
          assignee_contact_id: assignees.assignee_contact_id ?? null,
        }),
      })
      if (created.series_id) {
        await loadPage()
      } else if ((created.project_id || null) === projectId.value) {
        tasks.value = [created, ...tasks.value]
      }
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
  if (!confirmDeleteTask(task)) return

  busyId.value = task.id
  error.value = ''
  try {
    await apiJson(`/api/v1/tasks/${task.id}`, { method: 'DELETE' })
    const remaining = removeDeletedTask(tasks.value, task)
    tasks.value = remaining
    if (editingTaskId.value && !remaining.some((t) => t.id === editingTaskId.value)) {
      closeModal()
    }
  } catch (err) {
    console.error('[AdminProjectTasks] delete failed', err)
    error.value = err.message || 'Failed to delete task'
  } finally {
    busyId.value = null
  }
}

async function deleteFromModal() {
  const task = tasks.value.find((t) => t.id === editingTaskId.value)
  if (!task) return
  await confirmDelete(task)
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

</style>
