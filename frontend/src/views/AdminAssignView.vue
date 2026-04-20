<template>
  <div>
    <PageHeader
      eyebrow="People"
      title="Assign training"
      description="Choose what to assign and who completes it. People see it instantly on their assignments page."
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
        <label class="field">
          <span>People (work emails)</span>
          <textarea
            v-model="emailsRaw"
            rows="3"
            placeholder="alex@company.com, sam@company.com"
            required
            :disabled="submitting || !trainingOptions.length"
          />
        </label>
        <p class="hint">One or more emails, separated by commas or new lines. Each person must already have an account (add them on the dashboard).</p>
        <button type="submit" class="btn" :disabled="submitting || !trainingOptions.length">
          {{ submitting ? 'Assigning…' : 'Assign' }}
        </button>
      </form>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'

import { apiJson } from '@/api/client'
import PageHeader from '@/components/PageHeader.vue'
import { fetchTrainingOptions } from '@/utils/trainingCatalog'

const trainingOptions = ref([])
const trainingId = ref(1)
const emailsRaw = ref('')
const submitting = ref(false)
const error = ref('')
const success = ref('')

onMounted(async () => {
  trainingOptions.value = await fetchTrainingOptions()
  if (trainingOptions.value.length) {
    trainingId.value = trainingOptions.value[0].id
  }
})

function parseEmails(raw) {
  return raw
    .split(/[,;\n]+/)
    .map((s) => s.trim())
    .filter(Boolean)
}

async function onSubmit() {
  error.value = ''
  success.value = ''
  const assignee_emails = parseEmails(emailsRaw.value)
  if (assignee_emails.length === 0) {
    error.value = 'Enter at least one work email.'
    return
  }
  submitting.value = true
  try {
    const res = await apiJson('/api/v1/assignments', {
      method: 'POST',
      body: JSON.stringify({
        training_id: trainingId.value,
        assignee_emails,
      }),
    })
    const label =
      trainingOptions.value.find((o) => o.id === trainingId.value)?.title || 'this training'
    success.value =
      res.created > 0
        ? `Assigned “${label}” to ${res.created} person(s). They’ll see it under Assignments.`
        : `Everyone listed was already assigned to “${label}”.`
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
.field select,
.field textarea {
  font-family: var(--font-body);
  font-size: 1rem;
  padding: 0.65rem 0.75rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-bg-elevated);
  color: var(--color-text);
  resize: vertical;
  min-height: 2.75rem;
}

.field input:focus,
.field select:focus,
.field textarea:focus {
  outline: none;
  border-color: var(--color-accent);
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
