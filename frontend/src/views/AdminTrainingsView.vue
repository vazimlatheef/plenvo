<template>
  <div class="app-page">
    <div class="app-page-header">
      <h1>Training</h1>
      <div class="header-actions">
        <RouterLink
          v-if="!writeRestricted"
          to="/app/admin/assign"
          class="btn-outline btn-with-icon"
        >
          Assign training
          <ArrowRight :size="14" :stroke-width="1.75" />
        </RouterLink>
        <button
          v-else
          type="button"
          class="btn-outline btn-with-icon"
          disabled
          :title="writeDisabledTitle"
        >
          Assign training
          <ArrowRight :size="14" :stroke-width="1.75" />
        </button>
        <RouterLink
          v-if="!writeRestricted"
          to="/app/admin/trainings/new"
          class="btn-primary btn-with-icon"
        >
          <Plus :size="16" :stroke-width="2" />
          New training
        </RouterLink>
        <button
          v-else
          type="button"
          class="btn-primary btn-with-icon"
          disabled
          :title="writeDisabledTitle"
        >
          <Plus :size="16" :stroke-width="2" />
          New training
        </button>
      </div>
    </div>

    <p v-if="loading" class="muted-line">Loading trainings…</p>
    <p v-else-if="error" class="error-line">{{ error }}</p>

    <div v-else-if="trainings.length === 0" class="empty-panel">
      <p>No trainings yet — publish one for your team to complete.</p>
      <RouterLink v-if="!writeRestricted" to="/app/admin/trainings/new" class="btn-primary btn-with-icon">
        <Plus :size="16" :stroke-width="2" />
        Create training
      </RouterLink>
      <button
        v-else
        type="button"
        class="btn-primary btn-with-icon"
        disabled
        :title="writeDisabledTitle"
      >
        <Plus :size="16" :stroke-width="2" />
        Create training
      </button>
    </div>

    <ul v-else class="dense-list">
      <li v-for="training in trainings" :key="training.id" class="dense-row training-row">
        <span
          class="avatar avatar--lg"
          :class="`avatar-tone-${avatarTone(training.id || training.title)}`"
        >
          {{ getInitials(training.title) }}
        </span>
        <div class="dense-row__meta training-meta">
          <span class="dense-row__title">{{ training.title }}</span>
          <span class="training-sub">
            {{ contentLabel(training.content_type) }}
            <template v-if="training.description"> · {{ training.description }}</template>
          </span>
        </div>
        <div class="training-stats">
          <span class="stat-pill">{{ training.total_assigned }} assigned</span>
          <span class="stat-pill stat-pill--done">{{ training.completed }} completed</span>
        </div>
        <div class="training-actions">
          <RouterLink
            :to="{
              name: 'training-summary',
              params: { trainingId: String(training.id) },
              query: { title: training.title },
            }"
            class="btn-outline link-btn btn-with-icon"
          >
            Completion summary
            <ArrowRight :size="14" :stroke-width="1.75" />
          </RouterLink>
          <RouterLink
            :to="{ name: 'edit-training', params: { trainingId: String(training.id) } }"
            class="btn-ghost-sm"
          >
            Edit
          </RouterLink>
          <button
            type="button"
            class="btn-ghost-sm btn-ghost-sm--danger"
            :disabled="writeRestricted || deletingId === training.id"
            :title="writeRestricted ? writeDisabledTitle : 'Delete training'"
            @click="confirmDeleteTraining(training)"
          >
            Delete
          </button>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ArrowRight, Plus } from '@lucide/vue'
import { onMounted, ref } from 'vue'

import { apiJson } from '@/api/client'
import { useWriteAccess } from '@/composables/useWriteAccess'
import { avatarTone, getInitials } from '@/utils/ui'

const { writeRestricted, writeDisabledTitle } = useWriteAccess()

const trainings = ref([])
const loading = ref(true)
const error = ref('')
const deletingId = ref(null)

function contentLabel(type) {
  if (type === 'youtube') return 'YouTube'
  if (type === 'external_link') return 'External link'
  if (type === 'upload') return 'File upload'
  return 'Training'
}

async function loadTrainings() {
  loading.value = true
  error.value = ''
  try {
    const data = await apiJson('/api/v1/trainings')
    trainings.value = Array.isArray(data) ? data : []
  } catch (err) {
    console.error('[TrainingsList] load failed', err)
    error.value = err.message || 'Failed to load trainings'
  } finally {
    loading.value = false
  }
}

async function confirmDeleteTraining(training) {
  if (writeRestricted.value) return
  const ok = window.confirm(`Delete “${training.title}”? Assignments for this training are removed.`)
  if (!ok) return
  deletingId.value = training.id
  error.value = ''
  try {
    await apiJson(`/api/v1/trainings/${training.id}`, { method: 'DELETE' })
    trainings.value = trainings.value.filter((t) => t.id !== training.id)
  } catch (err) {
    console.error('[TrainingsList] delete failed', err)
    error.value = err.message || 'Failed to delete training'
  } finally {
    deletingId.value = null
  }
}

onMounted(loadTrainings)
</script>

<style scoped>
.header-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
}

.training-row {
  grid-template-columns: 36px minmax(0, 1fr) auto auto;
  gap: 0.75rem 1rem;
}

.training-meta {
  flex-direction: column;
  align-items: flex-start;
  gap: 0.15rem;
  min-width: 0;
}

.training-sub {
  font-size: 0.78rem;
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.training-stats {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.3rem;
}

.stat-pill {
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  padding: 0.22rem 0.5rem;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
  white-space: nowrap;
}

.stat-pill--done {
  color: var(--color-accent);
  border-color: rgba(196, 163, 90, 0.35);
}

.training-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.35rem;
}

.btn-ghost-sm {
  font-size: 0.78rem;
  color: var(--color-text-muted);
  text-decoration: none;
}

.btn-ghost-sm:hover {
  color: var(--color-accent);
}

.btn-ghost-sm--danger:hover {
  color: var(--color-text);
}

@media (max-width: 720px) {
  .training-row {
    grid-template-columns: 36px minmax(0, 1fr);
  }

  .training-stats,
  .training-actions {
    grid-column: 2;
    align-items: flex-start;
  }
}
</style>
