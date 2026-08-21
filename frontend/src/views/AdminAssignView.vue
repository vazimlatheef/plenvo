<template>
  <div>
    <PageHeader
      eyebrow="People"
      title="Assign training"
      description="Choose training and team members. Contacts receive a magic link by email; members with accounts can also use Assignments."
    />
    <section class="card">
      <p v-if="error" class="alert-error">{{ error }}</p>
      <p v-if="success" class="alert-success">{{ success }}</p>
      <form class="form" @submit.prevent="onSubmit">
        <label class="field">
          <span>Training</span>
          <select v-if="trainingOptions.length" v-model.number="trainingId" required :disabled="submitting">
            <option v-for="o in trainingOptions" :key="o.id" :value="o.id">
              {{ o.title }}
            </option>
          </select>
          <p v-else class="empty-hint">Create a training first (New training), then return here.</p>
        </label>

        <div class="field">
          <span>Assign to</span>
          <p v-if="loadingPeople" class="empty-hint">Loading team…</p>
          <p v-else-if="assigneeOptions.length === 0" class="empty-hint">
            Add team members on the Team page first.
          </p>
          <div v-else class="assignee-list">
            <label v-for="opt in assigneeOptions" :key="opt.key" class="assignee-option">
              <input
                v-model="selectedKeys"
                type="checkbox"
                :value="opt.key"
                :disabled="submitting || !trainingOptions.length"
              />
              <span>{{ assigneeOptionLabel(opt) }}</span>
              <span v-if="opt.email" class="assignee-email">{{ opt.email }}</span>
            </label>
          </div>
        </div>

        <p class="hint">
          Select one or more people. Contacts without a Plenvo account complete training via the email link.
        </p>
        <button
          type="submit"
          class="btn"
          :disabled="submitting || !trainingOptions.length || selectedKeys.length === 0"
        >
          {{ submitting ? 'Assigning…' : 'Assign' }}
        </button>
      </form>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

import { apiJson } from '@/api/client'
import { user } from '@/composables/session'
import PageHeader from '@/components/PageHeader.vue'
import { assigneeOptionLabel, buildAssigneeOptions, parseAssigneeKey } from '@/utils/assignee'
import { fetchTrainingOptions } from '@/utils/trainingCatalog'

const trainingOptions = ref([])
const trainingId = ref(1)
const selectedKeys = ref([])
const submitting = ref(false)
const loadingPeople = ref(true)
const error = ref('')
const success = ref('')
const users = ref([])
const contacts = ref([])

const assigneeOptions = computed(() =>
  buildAssigneeOptions({
    users: users.value,
    contacts: contacts.value,
    currentUser: user.value,
  }),
)

onMounted(async () => {
  trainingOptions.value = await fetchTrainingOptions()
  if (trainingOptions.value.length) {
    trainingId.value = trainingOptions.value[0].id
  }
  try {
    const [userList, contactList] = await Promise.all([
      apiJson('/api/v1/users?role=employee').catch(() => []),
      apiJson('/api/v1/contacts').catch(() => []),
    ])
    users.value = Array.isArray(userList) ? userList : []
    contacts.value = Array.isArray(contactList) ? contactList : []
  } catch (err) {
    console.error('[AdminAssign] failed to load people', err)
  } finally {
    loadingPeople.value = false
  }
})

async function onSubmit() {
  error.value = ''
  success.value = ''
  if (selectedKeys.value.length === 0) {
    error.value = 'Select at least one person.'
    return
  }

  const assignee_user_ids = []
  const assignee_contact_ids = []
  for (const key of selectedKeys.value) {
    const { assignee_id, assignee_contact_id } = parseAssigneeKey(key)
    if (assignee_id) assignee_user_ids.push(assignee_id)
    if (assignee_contact_id) assignee_contact_ids.push(assignee_contact_id)
  }

  submitting.value = true
  try {
    const res = await apiJson('/api/v1/assignments', {
      method: 'POST',
      body: JSON.stringify({
        training_id: trainingId.value,
        assignee_user_ids,
        assignee_contact_ids,
      }),
    })
    const label =
      trainingOptions.value.find((o) => o.id === trainingId.value)?.title || 'this training'
    success.value =
      res.created > 0
        ? `Assigned “${label}” to ${res.created} person(s). Magic links were emailed where applicable.`
        : `Everyone selected was already assigned to “${label}”.`
    if (res.created > 0) selectedKeys.value = []
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Request failed'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 1.25rem 1.35rem;
  max-width: 520px;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-muted);
}

.field input,
.field select {
  font-family: var(--font-body);
  font-size: 1rem;
  padding: 0.65rem 0.75rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-bg-elevated);
  color: var(--color-text);
  min-height: 2.75rem;
}

.field input:focus,
.field select:focus {
  outline: none;
  border-color: var(--color-accent);
}

.assignee-list {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  max-height: 280px;
  overflow-y: auto;
  padding: 0.5rem;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-bg-elevated);
}

.assignee-option {
  display: grid;
  grid-template-columns: auto 1fr;
  grid-template-rows: auto auto;
  column-gap: 0.55rem;
  row-gap: 0.1rem;
  align-items: center;
  font-size: 0.9rem;
  text-transform: none;
  letter-spacing: normal;
  color: var(--color-text);
  padding: 0.35rem 0.25rem;
  cursor: pointer;
}

.assignee-option input {
  grid-row: 1 / span 2;
  min-height: auto;
  accent-color: var(--color-accent);
}

.assignee-email {
  grid-column: 2;
  font-size: 0.78rem;
  color: var(--color-text-muted);
}

.empty-hint {
  margin: 0;
  font-size: 0.9rem;
  text-transform: none;
  letter-spacing: normal;
  color: var(--color-text-muted);
}

.hint {
  margin: -0.25rem 0 0;
  font-size: 0.85rem;
  color: var(--color-text-muted);
  text-transform: none;
  letter-spacing: normal;
}

.btn {
  font-family: var(--font-body);
  font-weight: 500;
  padding: 0.65rem 1rem;
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

.alert-error {
  margin: 0 0 1rem;
  padding: 0.6rem 0.75rem;
  border-radius: 8px;
  font-size: 0.85rem;
  color: #f0d0d0;
  background: rgba(180, 60, 60, 0.2);
  border: 1px solid rgba(180, 60, 60, 0.35);
}

.alert-success {
  margin: 0 0 1rem;
  padding: 0.6rem 0.75rem;
  border-radius: 8px;
  font-size: 0.85rem;
  color: #d8f0e4;
  background: rgba(60, 140, 100, 0.2);
  border: 1px solid rgba(60, 140, 100, 0.35);
}
</style>
