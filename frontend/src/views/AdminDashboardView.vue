<template>
  <div>
    <PageHeader
      eyebrow="Overview"
      title="Dashboard"
      description="One place to publish training, assign it, and see who’s finished — before you scale to projects and wider team tracking."
    />
    <div class="grid">
      <section class="card">
        <h2>Next steps</h2>
        <div class="links">
          <RouterLink to="/admin/trainings/new">Create a training</RouterLink>
          <RouterLink to="/admin/assign">Assign people</RouterLink>
          <RouterLink to="/assignments">See all assignments</RouterLink>
        </div>
      </section>
      <section class="card card-wide">
        <h2>Your trainings</h2>
        <p class="hint">Edit content or remove a training you no longer need. Deleting removes all assignments for that training.</p>
        <p v-if="manageError" class="alert-error">{{ manageError }}</p>
        <div v-if="!trainingsManage.length" class="muted small">No trainings yet — create one to get started.</div>
        <div v-else class="table-scroll">
          <table class="data-table">
            <thead>
              <tr>
                <th scope="col">Title</th>
                <th scope="col">Type</th>
                <th scope="col" class="actions-col">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="t in trainingsManage" :key="t.id">
                <td>{{ t.title }}</td>
                <td class="type">{{ formatTrainingType(t.content_type) }}</td>
                <td class="actions-cell">
                  <RouterLink
                    class="link-action"
                    :to="{ name: 'edit-training', params: { trainingId: String(t.id) } }"
                  >
                    Edit
                  </RouterLink>
                  <RouterLink
                    class="link-action"
                    :to="{
                      name: 'training-summary',
                      params: { trainingId: String(t.id) },
                      query: { title: t.title },
                    }"
                  >
                    Summary
                  </RouterLink>
                  <button type="button" class="link-danger" @click="deleteTraining(t)">Delete</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
      <section class="card">
        <h2>Completion summary</h2>
        <p class="hint">Pick a training by name to see completion counts for your team.</p>
        <div v-if="trainingOptions.length" class="row">
          <label class="pick">
            <span>Training</span>
            <select v-model.number="summaryPickId" class="inp">
              <option v-for="o in trainingOptions" :key="o.id" :value="o.id">
                {{ o.title }}
              </option>
            </select>
          </label>
          <RouterLink
            v-if="summaryPickId"
            class="btn-link"
            :to="{
              name: 'training-summary',
              params: { trainingId: summaryPickId },
              query: summaryTitle ? { title: summaryTitle } : {},
            }"
          >
            Open summary
          </RouterLink>
        </div>
        <div v-else class="row">
          <span class="muted small">No trainings yet — create one first, then refresh this page.</span>
        </div>
      </section>
      <section class="card">
        <h2>Add a team member</h2>
        <p class="hint">They’ll use this email and password to sign in. Assign training by the same work email.</p>
        <p v-if="userError" class="alert-error">{{ userError }}</p>
        <p v-if="userOk" class="alert-success">{{ userOk }}</p>
        <form class="mini-form" @submit.prevent="createUser">
          <input v-model="newEmail" type="email" required placeholder="Work email" class="inp" :disabled="userBusy" />
          <input v-model="newPassword" type="password" required placeholder="Password (min 8 characters)" minlength="8" class="inp" :disabled="userBusy" />
          <input v-model="newName" type="text" required placeholder="Full name" class="inp" :disabled="userBusy" />
          <button type="submit" class="btn" :disabled="userBusy">{{ userBusy ? 'Creating…' : 'Create account' }}</button>
        </form>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

import { apiJson } from '@/api/client'
import PageHeader from '@/components/PageHeader.vue'
import { fetchTrainingOptions } from '@/utils/trainingCatalog'

const trainingOptions = ref([])
const summaryPickId = ref(null)
const summaryTitle = computed(() => {
  const id = summaryPickId.value
  const o = trainingOptions.value.find((x) => x.id === id)
  return o?.title || ''
})

const trainingsManage = ref([])
const manageError = ref('')

async function loadTrainingsList() {
  try {
    const list = await apiJson('/api/v1/trainings')
    trainingsManage.value = Array.isArray(list) ? list : []
  } catch {
    trainingsManage.value = []
  }
}

function formatTrainingType(ct) {
  if (ct === 'youtube') return 'YouTube'
  if (ct === 'external_link') return 'Link'
  if (ct === 'upload') return 'File upload'
  return ct
}

async function deleteTraining(t) {
  manageError.value = ''
  const ok = window.confirm(`Delete “${t.title}”? This removes all assignments for this training.`)
  if (!ok) return
  try {
    await apiJson(`/api/v1/trainings/${t.id}`, { method: 'DELETE' })
    trainingOptions.value = await fetchTrainingOptions()
    if (trainingOptions.value.length) {
      summaryPickId.value = trainingOptions.value[0].id
    } else {
      summaryPickId.value = null
    }
    await loadTrainingsList()
  } catch (e) {
    manageError.value = e instanceof Error ? e.message : 'Could not delete'
  }
}

onMounted(async () => {
  trainingOptions.value = await fetchTrainingOptions()
  if (trainingOptions.value.length) {
    summaryPickId.value = trainingOptions.value[0].id
  }
  await loadTrainingsList()
})

const newEmail = ref('')
const newPassword = ref('')
const newName = ref('')
const userBusy = ref(false)
const userError = ref('')
const userOk = ref('')

async function createUser() {
  userError.value = ''
  userOk.value = ''
  userBusy.value = true
  try {
    const u = await apiJson('/users', {
      method: 'POST',
      body: JSON.stringify({
        email: newEmail.value.trim(),
        password: newPassword.value,
        full_name: newName.value.trim(),
        role: 'employee',
      }),
    })
    userOk.value = `Added ${u.full_name} — they’ll sign in with ${u.email}. Use that email when you assign training.`
    newPassword.value = ''
  } catch (e) {
    userError.value = e instanceof Error ? e.message : 'Failed'
  } finally {
    userBusy.value = false
  }
}
</script>

<style scoped>
.grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}

.card-wide {
  grid-column: 1 / -1;
}

.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 1.25rem 1.35rem;
}

.card h2 {
  font-family: var(--font-display);
  font-size: 1.2rem;
  margin: 0 0 0.75rem;
}

.links {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.hint {
  font-size: 0.85rem;
  color: var(--color-text-muted);
  margin: 0 0 0.75rem;
}

.row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: flex-end;
}

.pick {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  flex: 1;
  min-width: 200px;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-text-muted);
}

.inp {
  font-family: var(--font-body);
  font-size: 0.9rem;
  padding: 0.5rem 0.65rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-bg-elevated);
  color: var(--color-text);
}

.mini-form {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.btn {
  font-family: var(--font-body);
  font-weight: 500;
  padding: 0.55rem 0.85rem;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--color-accent), #a6853a);
  color: #0f1210;
  cursor: pointer;
}

.btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-link {
  display: inline-block;
  font-size: 0.85rem;
  font-weight: 500;
  padding: 0.55rem 0.85rem;
  border-radius: 8px;
  background: var(--color-accent-soft);
  color: var(--color-accent);
  text-decoration: none;
  border: 1px solid var(--color-border);
  align-self: center;
}

.btn-link:hover {
  text-decoration: none;
  border-color: var(--color-accent);
}

.alert-error {
  margin: 0 0 0.75rem;
  padding: 0.5rem 0.65rem;
  border-radius: 8px;
  font-size: 0.85rem;
  color: #f0d0d0;
  background: rgba(180, 60, 60, 0.2);
  border: 1px solid rgba(180, 60, 60, 0.35);
}

.alert-success {
  margin: 0 0 0.75rem;
  padding: 0.5rem 0.65rem;
  border-radius: 8px;
  font-size: 0.85rem;
  color: #d8f0e4;
  background: rgba(60, 140, 100, 0.2);
  border: 1px solid rgba(60, 140, 100, 0.35);
}

.muted {
  color: var(--color-text-muted);
}

.small {
  font-size: 0.85rem;
}

.table-scroll {
  overflow-x: auto;
  border-radius: var(--radius);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.data-table th,
.data-table td {
  padding: 0.6rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}

.data-table th {
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-muted);
  font-weight: 500;
  background: var(--color-bg-elevated);
}

.data-table tbody tr:last-child td {
  border-bottom: none;
}

.data-table .type {
  color: var(--color-text-muted);
  white-space: nowrap;
}

.actions-col {
  width: 1%;
}

.actions-cell {
  white-space: nowrap;
}

.link-action {
  font-size: 0.85rem;
  font-weight: 500;
  margin-right: 0.75rem;
  text-decoration: none;
  color: var(--color-accent);
}

.link-action:hover {
  text-decoration: underline;
}

.link-danger {
  font-family: var(--font-body);
  font-size: 0.85rem;
  font-weight: 500;
  padding: 0;
  border: none;
  background: none;
  color: #e8a0a0;
  cursor: pointer;
  text-decoration: underline;
}

.link-danger:hover {
  color: #f0c0c0;
}
</style>
