<template>
  <div class="ai-terminal">
    <div class="terminal-header">
      <div class="terminal-icon">
        <Sparkles :size="22" :stroke-width="1.75" />
      </div>
      <div>
        <h2>Plenvo AI</h2>
        <p>Paste notes, assign work, or ask how things are tracking — Plenvo reads your workspace and responds.</p>
      </div>
    </div>

    <!-- Step 1: Input -->
    <div v-if="step === 'input'" class="card">
      <div class="field">
        <label>Note title <span class="optional">(optional)</span></label>
        <input v-model="form.title" placeholder="e.g. Monday standup" />
      </div>

      <div class="field">
        <label>Project <span class="optional">(optional)</span></label>
        <select :value="projectSelectValue" :disabled="creatingProject" @change="onProjectChange">
          <option value="">No project</option>
          <option v-for="p in projects" :key="p.id" :value="String(p.id)">{{ p.title }}</option>
          <option value="__new__">+ New project</option>
        </select>
        <p v-if="projectsLoadError" class="field-hint field-hint--error">{{ projectsLoadError }}</p>
        <div v-if="showInlineCreate" class="inline-create">
          <input
            ref="newProjectInput"
            v-model="newProjectTitle"
            type="text"
            maxlength="100"
            placeholder="Project name"
            :disabled="creatingProject"
            @keydown.enter.prevent="createInlineProject"
            @keydown.escape.prevent="cancelInlineCreate"
          />
          <div class="inline-create__actions">
            <button type="button" class="btn-secondary btn-compact" :disabled="creatingProject" @click="cancelInlineCreate">
              Cancel
            </button>
            <button
              type="button"
              class="btn-primary btn-compact"
              :disabled="creatingProject || !newProjectTitle.trim()"
              @click="createInlineProject"
            >
              {{ creatingProject ? 'Creating…' : 'Create' }}
            </button>
          </div>
          <p v-if="createProjectError" class="field-hint field-hint--error">{{ createProjectError }}</p>
        </div>
      </div>

      <div class="field">
        <label>What do you want to capture or ask?</label>
        <textarea
          v-model="form.raw_text"
          placeholder="Paste notes, add people and work, or ask a question — e.g. what’s next, how the team is tracking."
          rows="8"
        />
      </div>

      <div class="example-row" aria-label="Example briefs">
        <button
          v-for="ex in examples"
          :key="ex.label"
          type="button"
          class="example-chip"
          @click="form.raw_text = ex.text"
        >
          {{ ex.label }}
        </button>
      </div>

      <button
        class="btn-primary"
        :disabled="!form.raw_text.trim() || loading || writeRestricted"
        :title="writeDisabledTitle"
        @click="parseNote"
      >
        <span v-if="loading" class="spinner" />
        <span v-else class="btn-with-icon">
          <Sparkles :size="16" :stroke-width="2" />
          Send to Plenvo
        </span>
      </button>
    </div>

    <!-- Insight-only -->
    <div v-if="step === 'briefing'" class="card">
      <div class="review-header">
        <h3>Briefing</h3>
        <p>Based on live tasks, people, and projects in your workspace.</p>
      </div>
      <div class="briefing-body">{{ briefing }}</div>
      <div class="review-actions">
        <button class="btn-secondary btn-with-icon" type="button" @click="reset">
          <ArrowLeft :size="15" :stroke-width="1.75" />
          New brief
        </button>
      </div>
    </div>

    <!-- Step 2: Review extracted tasks -->
    <div v-if="step === 'review'" class="card">
      <div v-if="briefing" class="briefing-panel">
        <h3>Briefing</h3>
        <div class="briefing-body">{{ briefing }}</div>
      </div>
      <div class="review-header">
        <h3>
          {{ extractedTasks.length }} item{{ extractedTasks.length !== 1 ? 's' : '' }} to confirm
        </h3>
        <p>Review people, projects, and dates — then save to the board.</p>
      </div>

      <div v-for="(task, i) in extractedTasks" :key="i" class="task-card">
        <div class="task-number">{{ i + 1 }}</div>
        <div class="task-fields">
          <div class="field">
            <label>Task</label>
            <input v-model="task.title" />
          </div>
          <div class="field">
            <label>Description</label>
            <input v-model="task.description" placeholder="Optional context" />
          </div>
          <div class="row-fields">
            <div class="field field--flush">
              <label>Assign to</label>
              <select
                :value="taskAssigneeSelectValue(task)"
                @change="onTaskAssigneeChange(task, $event)"
              >
                <option value="">Unassigned</option>
                <option v-for="opt in assigneeOptions" :key="opt.key" :value="opt.key">
                  {{ assigneeOptionLabel(opt) }}
                </option>
                <option
                  v-if="task.suggested_new_contact && canAddMembers"
                  :value="createContactOptionValue(task.suggested_new_contact)"
                >
                  + Create contact '{{ task.suggested_new_contact }}'
                </option>
                <option
                  v-else-if="task.suggested_new_contact && !canAddMembers"
                  value="__limit__"
                  disabled
                >
                  + Create contact '{{ task.suggested_new_contact }}' (limit reached)
                </option>
              </select>
              <span
                class="ai-hint"
                :class="{
                  'ai-hint--matched':
                    (task.assignee_matched && !!task.assignee_key) || !!task.create_contact_name,
                  'ai-hint--empty': !assigneeHint(task),
                }"
              >
                {{ assigneeHint(task) || '\u00a0' }}
              </span>
            </div>
            <div class="field field--flush">
              <label>Project</label>
              <select
                :value="taskProjectSelectValue(task)"
                @change="onTaskProjectChange(task, $event)"
              >
                <option value="">No project</option>
                <option v-for="p in projects" :key="p.id" :value="`id:${p.id}`">{{ p.title }}</option>
                <option
                  v-if="task.suggested_new_project"
                  :value="createProjectOptionValue(task.suggested_new_project)"
                >
                  + Create '{{ task.suggested_new_project }}'
                </option>
              </select>
              <span
                class="ai-hint"
                :class="{
                  'ai-hint--matched': !!task.project_matched || !!task.create_project_title,
                  'ai-hint--empty': !projectHint(task),
                }"
              >
                {{ projectHint(task) || '\u00a0' }}
              </span>
            </div>
            <div class="field field--flush">
              <label>Due Date</label>
              <DatePicker v-model="task.due_date" />
              <span class="ai-hint ai-hint--empty" aria-hidden="true">&nbsp;</span>
            </div>
            <div class="field field--flush">
              <label>Priority</label>
              <select v-model="task.priority">
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
              <span class="ai-hint ai-hint--empty" aria-hidden="true">&nbsp;</span>
            </div>
          </div>
        </div>
        <button class="btn-remove" type="button" @click="removeTask(i)" title="Remove task" aria-label="Remove task">
          <X :size="16" :stroke-width="1.75" />
        </button>
      </div>

      <div class="review-actions">
        <button class="btn-secondary btn-with-icon" type="button" @click="reset">
          <ArrowLeft :size="15" :stroke-width="1.75" />
          Start over
        </button>
        <button
          class="btn-primary"
          :disabled="loading || extractedTasks.length === 0 || writeRestricted"
          :title="writeDisabledTitle"
          @click="confirmTasks"
        >
          <span v-if="loading" class="spinner" />
          <span v-else class="btn-with-icon">
            <Check :size="16" :stroke-width="2" />
            Confirm & Save {{ extractedTasks.length }} Task{{ extractedTasks.length !== 1 ? 's' : '' }}
          </span>
        </button>
      </div>
    </div>

    <!-- Step 3: Success -->
    <div v-if="step === 'success'" class="card success-card">
      <div class="success-icon">
        <Check :size="28" :stroke-width="2" />
      </div>
      <h3>{{ lastCreatedCount }} item{{ lastCreatedCount !== 1 ? 's' : '' }} on the board</h3>
      <p>Assigned work is live. Ask Brief anytime how the team is tracking.</p>
      <button class="btn-primary btn-with-icon" type="button" @click="reset">
        <Sparkles :size="16" :stroke-width="2" />
        New brief
      </button>
    </div>

    <!-- Error -->
    <div v-if="error" class="error-banner">{{ error }}</div>
  </div>
</template>

<script setup>
import { ArrowLeft, Check, Sparkles, X } from '@lucide/vue'
import { ref, computed, nextTick, onMounted } from 'vue'
import { apiJson } from '@/api/client'
import DatePicker from '@/components/DatePicker.vue'
import { user } from '@/composables/session'
import { useWriteAccess } from '@/composables/useWriteAccess'
import {
  assigneeOptionLabel,
  buildAssigneeOptions,
  parseAssigneeKey,
  taskAssigneeKey,
} from '@/utils/assignee'

const NEW_PROJECT_VALUE = '__new__'
const CREATE_PROJECT_PREFIX = 'new:'
const CREATE_CONTACT_PREFIX = 'contact:'

const { writeRestricted, writeDisabledTitle } = useWriteAccess()

const step = ref('input')
const loading = ref(false)
const error = ref(null)
const noteId = ref(null)
const lastCreatedCount = ref(0)

const form = ref({ title: '', raw_text: '', project_id: null })
const extractedTasks = ref([])
const briefing = ref('')
const intent = ref('capture')

const examples = [
  {
    label: 'Monday dump',
    text: 'Standup 9am Monday. API docs due Thursday — high priority. Call mum this weekend. Side project: refresh landing copy. Gym Tuesday 6pm.',
  },
  {
    label: 'Add someone + work',
    text: 'Maya starts Monday as designer — add her. Homepage mockups by Friday. Alex reviews API docs Thursday.',
  },
  {
    label: 'What’s next?',
    text: 'What’s the single most important thing I should tackle today?',
  },
  {
    label: 'Team pulse',
    text: 'How is the team tracking this week? Who’s overloaded and who has slack?',
  },
]
const projects = ref([])
const teamMembers = ref([])
const contacts = ref([])
const projectsLoadError = ref('')
const teamLimits = ref({
  can_add_members: true,
  limit_message: null,
  member_limit: null,
  member_count: 0,
  plan_tier: 'team',
})

const showInlineCreate = ref(false)
const newProjectTitle = ref('')
const newProjectInput = ref(null)
const creatingProject = ref(false)
const createProjectError = ref('')

const canAddMembers = computed(() => teamLimits.value?.can_add_members !== false)

const assigneeOptions = computed(() =>
  buildAssigneeOptions({
    users: teamMembers.value,
    contacts: contacts.value,
    currentUser: user.value,
  }),
)

const projectSelectValue = computed(() =>
  form.value.project_id == null ? '' : String(form.value.project_id),
)

function createProjectOptionValue(title) {
  return `${CREATE_PROJECT_PREFIX}${title}`
}

function createContactOptionValue(name) {
  return `${CREATE_CONTACT_PREFIX}${name}`
}

function taskAssigneeSelectValue(task) {
  if (task.create_contact_name) {
    return createContactOptionValue(task.create_contact_name)
  }
  return task.assignee_key || ''
}

function onTaskAssigneeChange(task, event) {
  const value = event.target.value
  if (!value) {
    task.assignee_key = null
    task.create_contact_name = null
    return
  }
  if (value.startsWith(CREATE_CONTACT_PREFIX)) {
    if (!canAddMembers.value) {
      event.target.value = taskAssigneeSelectValue(task)
      error.value = teamLimits.value?.limit_message || 'Team member limit reached.'
      return
    }
    task.assignee_key = null
    task.create_contact_name = value.slice(CREATE_CONTACT_PREFIX.length)
    return
  }
  task.assignee_key = value
  task.create_contact_name = null
}

function assigneeHint(task) {
  if (task.assignee_matched && task.assignee_key) {
    return `Matched: ${task.matched_assignee_label || task.assignee_name}`
  }
  if (task.create_contact_name) {
    return `Will create contact: ${task.create_contact_name}`
  }
  if (task.suggested_new_contact || task.assignee_name) {
    if (!canAddMembers.value && task.suggested_new_contact) {
      return (
        teamLimits.value?.limit_message ||
        `AI detected: ${task.suggested_new_contact} — team limit reached`
      )
    }
    return `AI detected: ${task.suggested_new_contact || task.assignee_name} — pick or create`
  }
  return ''
}

function taskProjectSelectValue(task) {
  if (task.create_project_title) {
    return createProjectOptionValue(task.create_project_title)
  }
  if (task.project_id != null) return `id:${task.project_id}`
  return ''
}

function onTaskProjectChange(task, event) {
  const value = event.target.value
  if (!value) {
    task.project_id = null
    task.create_project_title = null
    return
  }
  if (value.startsWith(CREATE_PROJECT_PREFIX)) {
    task.project_id = null
    task.create_project_title = value.slice(CREATE_PROJECT_PREFIX.length)
    return
  }
  if (value.startsWith('id:')) {
    task.project_id = Number(value.slice(3))
    task.create_project_title = null
    return
  }
  task.project_id = Number(value)
  task.create_project_title = null
}

function projectHint(task) {
  if (task.project_matched) {
    return `Matched: ${task.matched_project_label || task.project_name}`
  }
  if (task.create_project_title) {
    return `Will create project: ${task.create_project_title}`
  }
  if (task.suggested_new_project || task.project_name) {
    return `AI detected: ${task.suggested_new_project || task.project_name} — pick or create`
  }
  return ''
}

async function loadTeamLimits() {
  try {
    const limits = await apiJson('/api/v1/organisations/me/team-limits')
    teamLimits.value = limits || teamLimits.value
  } catch (err) {
    console.error('[AiTerminal] failed to load team limits', err)
  }
}

async function loadProjects() {
  projectsLoadError.value = ''
  try {
    // Same endpoint / ordering as AdminProjectsView
    const proj = await apiJson('/api/v1/projects')
    projects.value = Array.isArray(proj) ? proj : []
  } catch (err) {
    console.error('[AiTerminal] failed to load projects', err)
    projects.value = []
    projectsLoadError.value = err.message || 'Failed to load projects'
  }
}

function onProjectChange(event) {
  const value = event.target.value
  if (value === NEW_PROJECT_VALUE) {
    event.target.value = projectSelectValue.value
    openInlineCreate()
    return
  }
  form.value.project_id = value === '' ? null : Number(value)
  showInlineCreate.value = false
  createProjectError.value = ''
}

async function openInlineCreate() {
  showInlineCreate.value = true
  createProjectError.value = ''
  newProjectTitle.value = ''
  await nextTick()
  newProjectInput.value?.focus?.()
}

function cancelInlineCreate() {
  showInlineCreate.value = false
  newProjectTitle.value = ''
  createProjectError.value = ''
}

async function createInlineProject() {
  const title = newProjectTitle.value.trim()
  if (!title || creatingProject.value) return

  creatingProject.value = true
  createProjectError.value = ''
  try {
    const created = await apiJson('/api/v1/projects', {
      method: 'POST',
      body: JSON.stringify({
        title,
        description: null,
      }),
    })
    projects.value = [created, ...projects.value.filter((p) => p.id !== created.id)]
    form.value.project_id = created.id
    cancelInlineCreate()
  } catch (err) {
    console.error('[AiTerminal] create project failed', err)
    createProjectError.value = err.message || 'Failed to create project'
  } finally {
    creatingProject.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadProjects(), loadTeamLimits()])
  try {
    const [users, contactList] = await Promise.all([
      apiJson('/api/v1/users').catch(() => []),
      apiJson('/api/v1/contacts').catch(() => []),
    ])
    teamMembers.value = Array.isArray(users) ? users : []
    contacts.value = Array.isArray(contactList) ? contactList : []
  } catch {
    // non-fatal
  }
})

async function parseNote() {
  if (writeRestricted.value) return
  error.value = null
  loading.value = true
  try {
    await loadTeamLimits()
    const data = await apiJson('/api/v1/ai/parse-note', {
      method: 'POST',
      body: JSON.stringify({
        raw_text: form.value.raw_text,
        title: form.value.title || null,
        project_id: form.value.project_id,
      }),
    })
    noteId.value = data.note_id
    briefing.value = (data.briefing || '').trim()
    intent.value = data.intent || 'capture'
    extractedTasks.value = (data.extracted_tasks || []).map((t) => {
      const assignee_key = taskAssigneeKey({
        assignee_id: t.assignee_id,
        assignee_contact_id: t.assignee_contact_id,
      })
      const matchedProject = t.project_matched && t.project_id != null ? Number(t.project_id) : null
      const noteProject = form.value.project_id != null ? Number(form.value.project_id) : null
      const suggestedProject = (t.suggested_new_project || '').trim() || null
      const suggestedContact = (t.suggested_new_contact || '').trim() || null
      const matchedAssignee = Boolean(t.assignee_matched && assignee_key)
      return {
        ...t,
        assignee_key: matchedAssignee ? assignee_key : null,
        matched_assignee_label: t.matched_assignee_label || null,
        matched_project_label: t.matched_project_label || null,
        suggested_new_project: suggestedProject,
        suggested_new_contact: suggestedContact,
        project_id: matchedProject ?? (suggestedProject ? null : noteProject),
        project_matched: Boolean(t.project_matched),
        create_project_title: suggestedProject && !matchedProject ? suggestedProject : null,
        create_contact_name:
          suggestedContact && !matchedAssignee && canAddMembers.value ? suggestedContact : null,
      }
    })
    if (extractedTasks.value.length > 0) {
      step.value = 'review'
    } else if (briefing.value) {
      step.value = 'briefing'
    } else {
      error.value = 'Nothing to capture or report — try a note or a question.'
    }
  } catch (e) {
    error.value = e?.message || 'Something went wrong. Please try again.'
  } finally {
    loading.value = false
  }
}

async function confirmTasks() {
  if (writeRestricted.value) return
  error.value = null
  loading.value = true
  try {
    await loadTeamLimits()
    const creatingContacts = new Set(
      extractedTasks.value
        .map((t) => (t.create_contact_name || '').trim().toLowerCase())
        .filter(Boolean),
    )
    if (creatingContacts.size > 0 && !canAddMembers.value) {
      error.value = teamLimits.value?.limit_message || 'Team member limit reached.'
      loading.value = false
      return
    }

    const tasks = extractedTasks.value.map((t) => {
      const { assignee_id, assignee_contact_id } = parseAssigneeKey(t.assignee_key)
      const createTitle = (t.create_project_title || '').trim() || null
      const createContact = (t.create_contact_name || '').trim() || null
      return {
        title: t.title,
        description: t.description || null,
        assignee_id: createContact ? null : assignee_id,
        assignee_contact_id: createContact ? null : assignee_contact_id,
        create_contact_name: createContact,
        due_date: t.due_date || null,
        priority: t.priority,
        project_id: createTitle ? null : t.project_id ?? form.value.project_id ?? null,
        create_project_title: createTitle,
      }
    })
    const data = await apiJson('/api/v1/ai/confirm-tasks', {
      method: 'POST',
      body: JSON.stringify({ note_id: noteId.value, tasks }),
    })
    lastCreatedCount.value = data.created
    if (data.projects_created || data.contacts_created) {
      await Promise.all([loadProjects(), loadTeamLimits()])
      try {
        const contactList = await apiJson('/api/v1/contacts').catch(() => [])
        contacts.value = Array.isArray(contactList) ? contactList : []
      } catch {
        /* ignore */
      }
    }
    step.value = 'success'
  } catch (e) {
    error.value = e?.message || 'Failed to save tasks. Please try again.'
  } finally {
    loading.value = false
  }
}

function removeTask(i) {
  extractedTasks.value.splice(i, 1)
}

function reset() {
  step.value = 'input'
  form.value = { title: '', raw_text: '', project_id: form.value.project_id }
  extractedTasks.value = []
  briefing.value = ''
  intent.value = 'capture'
  noteId.value = null
  error.value = null
  cancelInlineCreate()
}
</script>

<style scoped>
.ai-terminal {
  max-width: 780px;
  margin: 0 auto;
  font-family: var(--font-body);
}

.terminal-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
}

.terminal-icon {
  background: var(--color-surface);
  color: var(--color-accent);
  border: 1px solid var(--color-border);
  width: 52px;
  height: 52px;
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.btn-with-icon {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
}

.example-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  margin: -0.35rem 0 1rem;
}

.example-chip {
  font-family: var(--font-body);
  font-size: 0.78rem;
  padding: 0.35rem 0.7rem;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
}

.example-chip:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.briefing-panel {
  margin-bottom: 1.5rem;
  padding-bottom: 1.25rem;
  border-bottom: 1px solid var(--color-border);
}

.briefing-panel h3,
.review-header h3 {
  margin: 0 0 0.35rem;
  font-family: var(--font-display);
  font-size: 1.35rem;
  font-weight: 400;
}

.briefing-body {
  white-space: pre-wrap;
  font-size: 0.95rem;
  line-height: 1.65;
  color: var(--color-text);
}

.terminal-header h2 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 1.75rem;
  font-weight: 400;
  color: var(--color-text);
}

.terminal-header p {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 0.9rem;
}

.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 1.75rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 1.2rem;
}

.field--flush {
  margin-bottom: 0;
}

.field label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  line-height: 1.25;
  min-height: 0.95rem;
}

.optional {
  font-weight: 400;
  color: var(--color-text-muted);
  opacity: 0.75;
  text-transform: none;
  letter-spacing: 0;
}

.field-hint {
  margin: 0.35rem 0 0;
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.field-hint--error {
  color: var(--color-danger);
}

.inline-create {
  margin-top: 0.65rem;
  padding: 0.85rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.inline-create__actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

.btn-compact {
  padding: 0.45rem 0.9rem;
  font-size: 0.82rem;
}

input,
select,
textarea {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 0.65rem 0.9rem;
  font-size: 0.95rem;
  color: var(--color-text);
  background: var(--color-bg);
  outline: none;
  transition: border-color 0.2s;
  font-family: inherit;
}

input:focus,
select:focus,
textarea:focus {
  border-color: var(--color-accent);
}

textarea {
  resize: vertical;
}

.btn-primary {
  background: linear-gradient(135deg, var(--color-accent), #a6853a);
  color: #0f1210;
  border: none;
  border-radius: var(--radius-sm);
  padding: 0.75rem 1.5rem;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: filter 0.2s, opacity 0.2s;
  font-family: inherit;
}

.btn-primary:hover:not(:disabled) {
  filter: brightness(1.08);
}

.btn-primary:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.btn-secondary {
  background: transparent;
  color: var(--color-text-muted);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 0.75rem 1.4rem;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: border-color 0.2s, color 0.2s;
  font-family: inherit;
}

.btn-secondary:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.review-header {
  margin-bottom: 1.5rem;
}

.review-header h3 {
  margin: 0 0 4px;
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 400;
  color: var(--color-text);
}

.review-header p {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 0.88rem;
}

.task-card {
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr) 32px;
  gap: 0.75rem 1rem;
  align-items: start;
  padding: 1.2rem;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  margin-bottom: 1rem;
}

.task-number {
  background: var(--color-accent);
  color: #0f1210;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 700;
  flex-shrink: 0;
  margin-top: calc(0.95rem + 6px);
}

.task-fields {
  min-width: 0;
}

.task-fields > .field:last-child {
  margin-bottom: 0;
}

.row-fields {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1rem;
  align-items: start;
}

.row-fields .field {
  margin-bottom: 0;
  min-width: 0;
}

.ai-hint {
  display: block;
  min-height: 2.5rem;
  padding-top: 0.2rem;
  font-size: 0.75rem;
  line-height: 1.35;
  color: var(--color-text-muted);
  font-style: italic;
}

.ai-hint--empty {
  visibility: hidden;
}

.ai-hint--matched {
  color: var(--color-accent);
  font-style: normal;
}

.btn-remove {
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  margin-top: calc(0.95rem + 6px);
}

.btn-remove:hover {
  color: var(--color-danger);
  background: rgba(248, 113, 113, 0.1);
}

.review-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--color-border);
}

.success-card {
  text-align: center;
  padding: 3rem 2rem;
}

.success-icon {
  width: 64px;
  height: 64px;
  background: var(--status-done-bg);
  color: var(--status-done);
  border: 1px solid var(--status-done-border);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
}

.success-card h3 {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 400;
  color: var(--color-text);
  margin: 0 0 8px;
}

.success-card p {
  color: var(--color-text-muted);
  margin: 0 0 1.5rem;
}

.error-banner {
  margin-top: 1rem;
  background: rgba(248, 113, 113, 0.1);
  border: 1px solid rgba(248, 113, 113, 0.35);
  color: var(--color-danger);
  padding: 0.8rem 1rem;
  border-radius: var(--radius-sm);
  font-size: 0.9rem;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(15, 18, 16, 0.25);
  border-top-color: #0f1210;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  display: inline-block;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 900px) {
  .row-fields {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 600px) {
  .row-fields {
    grid-template-columns: 1fr;
  }
}
</style>
