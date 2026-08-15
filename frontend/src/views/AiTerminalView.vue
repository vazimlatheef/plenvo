<template>
  <div class="ai-terminal">
    <div class="terminal-header">
      <div class="terminal-icon">⚡</div>
      <div>
        <h2>AI Terminal</h2>
        <p>Paste meeting notes or updates — AI extracts tasks instantly</p>
      </div>
    </div>

    <!-- Step 1: Input -->
    <div v-if="step === 'input'" class="card">
      <div class="field">
        <label>Note Title <span class="optional">(optional)</span></label>
        <input v-model="form.title" placeholder="e.g. Weekly Sync — 25 Apr" />
      </div>

      <div class="field">
        <label>Project <span class="optional">(optional)</span></label>
        <select v-model="form.project_id">
          <option :value="null">No project</option>
          <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.title }}</option>
        </select>
      </div>

      <div class="field">
        <label>Paste your notes *</label>
        <textarea
          v-model="form.raw_text"
          placeholder="e.g. John to finish Q3 report by Friday. Sarah to schedule client call with Acme. Urgent: fix login bug before Monday."
          rows="8"
        />
      </div>

      <button class="btn-primary" :disabled="!form.raw_text.trim() || loading" @click="parseNote">
        <span v-if="loading" class="spinner" />
        <span v-else>⚡ Extract Tasks with AI</span>
      </button>
    </div>

    <!-- Step 2: Review extracted tasks -->
    <div v-if="step === 'review'" class="card">
      <div class="review-header">
        <h3>AI extracted {{ extractedTasks.length }} task{{ extractedTasks.length !== 1 ? 's' : '' }}</h3>
        <p>Review, edit, assign users — then confirm to save.</p>
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
            <div class="field">
              <label>Assign to</label>
              <select v-model="task.assignee_id">
                <option :value="null">Unassigned</option>
                <option v-for="u in teamMembers" :key="u.id" :value="u.id">{{ u.full_name }}</option>
              </select>
              <span v-if="task.assignee_name" class="ai-hint">AI detected: {{ task.assignee_name }}</span>
            </div>
            <div class="field">
              <label>Due Date</label>
              <DatePicker v-model="task.due_date" />
            </div>
            <div class="field">
              <label>Priority</label>
              <select v-model="task.priority">
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>
          </div>
        </div>
        <button class="btn-remove" @click="removeTask(i)" title="Remove task">✕</button>
      </div>

      <div class="review-actions">
        <button class="btn-secondary" @click="reset">← Start over</button>
        <button class="btn-primary" :disabled="loading || extractedTasks.length === 0" @click="confirmTasks">
          <span v-if="loading" class="spinner" />
          <span v-else>✓ Confirm & Save {{ extractedTasks.length }} Task{{ extractedTasks.length !== 1 ? 's' : '' }}</span>
        </button>
      </div>
    </div>

    <!-- Step 3: Success -->
    <div v-if="step === 'success'" class="card success-card">
      <div class="success-icon">✓</div>
      <h3>{{ lastCreatedCount }} task{{ lastCreatedCount !== 1 ? 's' : '' }} created</h3>
      <p>Your team has been assigned. Tasks are now live on the dashboard.</p>
      <button class="btn-primary" @click="reset">⚡ Parse another note</button>
    </div>

    <!-- Error -->
    <div v-if="error" class="error-banner">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiJson } from '@/api/client'
import DatePicker from '@/components/DatePicker.vue'

const step = ref('input')
const loading = ref(false)
const error = ref(null)
const noteId = ref(null)
const lastCreatedCount = ref(0)

const form = ref({ title: '', raw_text: '', project_id: null })
const extractedTasks = ref([])
const projects = ref([])
const teamMembers = ref([])

onMounted(async () => {
  try {
    const [proj, users] = await Promise.all([
      apiJson('/api/v1/projects'),
      apiJson('/api/v1/users'),
    ])
    projects.value = Array.isArray(proj) ? proj : []
    teamMembers.value = Array.isArray(users) ? users : []
  } catch {
    // non-fatal
  }
})

async function parseNote() {
  error.value = null
  loading.value = true
  try {
    const data = await apiJson('/api/v1/ai/parse-note', {
      method: 'POST',
      body: JSON.stringify({
        raw_text: form.value.raw_text,
        title: form.value.title || null,
        project_id: form.value.project_id,
      }),
    })
    noteId.value = data.note_id
    extractedTasks.value = data.extracted_tasks.map(t => ({ ...t, assignee_id: null }))
    step.value = 'review'
  } catch (e) {
    error.value = e?.message || 'Something went wrong. Please try again.'
  } finally {
    loading.value = false
  }
}

async function confirmTasks() {
  error.value = null
  loading.value = true
  try {
    const tasks = extractedTasks.value.map(t => ({
      title: t.title,
      description: t.description || null,
      assignee_id: t.assignee_id || null,
      due_date: t.due_date || null,
      priority: t.priority,
      project_id: form.value.project_id,
    }))
    const data = await apiJson('/api/v1/ai/confirm-tasks', {
      method: 'POST',
      body: JSON.stringify({ note_id: noteId.value, tasks }),
    })
    lastCreatedCount.value = data.created
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
  form.value = { title: '', raw_text: '', project_id: null }
  extractedTasks.value = []
  noteId.value = null
  error.value = null
}
</script>

<style scoped>
.ai-terminal {
  max-width: 780px;
  margin: 0 auto;
  padding: 2rem 1rem;
  font-family: 'DM Sans', sans-serif;
}

.terminal-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
}

.terminal-icon {
  font-size: 2rem;
  background: #0f172a;
  color: #facc15;
  width: 52px;
  height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.terminal-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: #0f172a;
}

.terminal-header p {
  margin: 0;
  color: #64748b;
  font-size: 0.9rem;
}

.card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 1.2rem;
}

.field label {
  font-size: 0.82rem;
  font-weight: 600;
  color: #374151;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.optional {
  font-weight: 400;
  color: #94a3b8;
  text-transform: none;
  letter-spacing: 0;
}

input, select, textarea {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.65rem 0.9rem;
  font-size: 0.95rem;
  color: #0f172a;
  background: #f8fafc;
  outline: none;
  transition: border-color 0.2s;
  font-family: inherit;
}

input:focus, select:focus, textarea:focus {
  border-color: #0f172a;
  background: #fff;
}

textarea { resize: vertical; }

.btn-primary {
  background: #0f172a;
  color: #fff;
  border: none;
  border-radius: 10px;
  padding: 0.8rem 1.6rem;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background 0.2s, opacity 0.2s;
}

.btn-primary:hover:not(:disabled) { background: #1e293b; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-secondary {
  background: transparent;
  color: #64748b;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.8rem 1.4rem;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: border-color 0.2s;
}

.btn-secondary:hover { border-color: #94a3b8; color: #0f172a; }

.review-header { margin-bottom: 1.5rem; }
.review-header h3 { margin: 0 0 4px; font-size: 1.15rem; color: #0f172a; }
.review-header p { margin: 0; color: #64748b; font-size: 0.88rem; }

.task-card {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  padding: 1.2rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  margin-bottom: 1rem;
  position: relative;
}

.task-number {
  background: #0f172a;
  color: #fff;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 700;
  flex-shrink: 0;
  margin-top: 4px;
}

.task-fields { flex: 1; }

.row-fields {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 1rem;
}

.ai-hint {
  font-size: 0.75rem;
  color: #f59e0b;
  font-style: italic;
}

.btn-remove {
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  font-size: 1rem;
  padding: 4px;
  flex-shrink: 0;
}
.btn-remove:hover { color: #ef4444; }

.review-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e2e8f0;
}

.success-card { text-align: center; padding: 3rem 2rem; }

.success-icon {
  width: 64px;
  height: 64px;
  background: #dcfce7;
  color: #16a34a;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.8rem;
  margin: 0 auto 1rem;
}

.success-card h3 { font-size: 1.4rem; color: #0f172a; margin: 0 0 8px; }
.success-card p { color: #64748b; margin: 0 0 1.5rem; }

.error-banner {
  margin-top: 1rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
  padding: 0.8rem 1rem;
  border-radius: 8px;
  font-size: 0.9rem;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  display: inline-block;
}

@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 600px) {
  .row-fields { grid-template-columns: 1fr; }
}
</style>