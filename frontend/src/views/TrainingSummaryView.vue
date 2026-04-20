<template>
  <div>
    <PageHeader
      eyebrow="Outcomes"
      title="Completion summary"
      :description="headerDescription"
    />
    <div v-if="summary && !loading && !error" class="toolbar">
      <RouterLink
        class="btn-link"
        :to="{ name: 'edit-training', params: { trainingId: String(trainingId) } }"
      >
        Edit training
      </RouterLink>
    </div>
    <p v-if="loading" class="muted">Loading numbers…</p>
    <p v-else-if="error" class="alert-error">{{ error }}</p>
    <template v-else>
      <div class="stats">
        <div v-for="item in statRows" :key="item.key" class="stat">
          <span class="value">{{ item.value }}</span>
          <span class="label">{{ item.label }}</span>
        </div>
      </div>
      <section v-if="summary?.rows?.length" class="table-wrap">
        <h2 class="table-title">People &amp; status</h2>
        <div class="table-scroll">
          <table class="data-table">
            <thead>
              <tr>
                <th scope="col">Name</th>
                <th scope="col">Email</th>
                <th scope="col">Status</th>
                <th scope="col">Started</th>
                <th scope="col">Completed</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in summary.rows" :key="idx">
                <td>{{ row.assignee_full_name }}</td>
                <td class="email">{{ row.assignee_email }}</td>
                <td>
                  <span class="pill" :data-s="row.status">{{ formatStatus(row.status) }}</span>
                </td>
                <td class="date">{{ formatTs(row.started_at) }}</td>
                <td class="date">{{ formatTs(row.completed_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
      <p v-else-if="summary && !summary.rows?.length" class="empty muted">
        No one assigned yet. Assign people from the dashboard, then refresh this page.
      </p>
      <p v-if="!loading && !error && summary" class="foot muted small">
        Use this in meetings: who still owes the training, who’s done — without another spreadsheet.
      </p>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import { apiJson } from '@/api/client'
import PageHeader from '@/components/PageHeader.vue'

const route = useRoute()
const trainingId = computed(() => route.params.trainingId)

const titleFromQuery = computed(() => {
  const q = route.query.title
  if (typeof q === 'string' && q.trim()) return q.trim()
  return ''
})

const loading = ref(true)
const error = ref('')
const summary = ref(null)

const headerDescription = computed(() => {
  const t = summary.value?.training_title
  if (t) {
    return `Progress for “${t}”.`
  }
  if (titleFromQuery.value) {
    return `Progress for “${titleFromQuery.value}”.`
  }
  return 'How many people are done, in progress, or not started.'
})

const statRows = computed(() => {
  const s = summary.value
  if (!s) return []
  return [
    { key: 'total', label: 'Assigned', value: s.total_assigned },
    { key: 'done', label: 'Completed', value: s.completed },
    { key: 'prog', label: 'In progress', value: s.in_progress },
    { key: 'ns', label: 'Not started', value: s.not_started },
  ]
})

function formatStatus(s) {
  if (!s) return '—'
  return s.replaceAll('_', ' ')
}

function formatTs(iso) {
  if (!iso) return '—'
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return '—'
  }
}

async function load() {
  loading.value = true
  error.value = ''
  summary.value = null
  try {
    summary.value = await apiJson(`/api/v1/trainings/${trainingId.value}/summary`)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to load summary'
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(trainingId, load)
</script>

<style scoped>
.toolbar {
  margin-bottom: 1rem;
}

.btn-link {
  display: inline-block;
  font-size: 0.85rem;
  font-weight: 500;
  padding: 0.45rem 0.85rem;
  border-radius: 8px;
  background: var(--color-accent-soft);
  color: var(--color-accent);
  text-decoration: none;
  border: 1px solid var(--color-border);
}

.btn-link:hover {
  border-color: var(--color-accent);
}

.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.stat {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 1rem 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.value {
  font-family: var(--font-display);
  font-size: 1.75rem;
  font-weight: 600;
  color: var(--color-text);
}

.label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-text-muted);
}

.table-title {
  font-family: var(--font-display);
  font-size: 1.15rem;
  margin: 0 0 0.75rem;
  color: var(--color-text);
}

.table-wrap {
  margin-bottom: 1.25rem;
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
  padding: 0.65rem 0.85rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
  vertical-align: top;
}

.data-table th {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-muted);
  font-weight: 500;
  background: var(--color-bg-elevated);
}

.data-table tbody tr:last-child td {
  border-bottom: none;
}

.data-table td.email {
  word-break: break-all;
  max-width: 14rem;
}

.data-table td.date {
  color: var(--color-text-muted);
  font-size: 0.85rem;
  white-space: nowrap;
}

.pill {
  display: inline-block;
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 0.2rem 0.5rem;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  color: var(--color-accent);
}

.muted {
  color: var(--color-text-muted);
}

.small {
  font-size: 0.85rem;
}

.empty {
  margin: 0 0 1rem;
}

.foot {
  margin-top: 0.5rem;
  max-width: 42ch;
}

.alert-error {
  padding: 0.6rem 0.75rem;
  border-radius: 8px;
  font-size: 0.85rem;
  color: #f0d0d0;
  background: rgba(180, 60, 60, 0.2);
  border: 1px solid rgba(180, 60, 60, 0.35);
}
</style>
