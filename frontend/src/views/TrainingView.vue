<template>
  <div class="training-page">
    <div class="panel">
      <RouterLink to="/" class="logo">Plenvo</RouterLink>

      <p v-if="loading" class="muted">Loading your training…</p>
      <p v-else-if="error" class="alert error">{{ error }}</p>

      <template v-else-if="data">
        <p class="eyebrow">Assigned to {{ data.assignee_first_name }} {{ data.assignee_last_name }}</p>
        <h1>{{ data.training_title }}</h1>
        <p class="lede">{{ data.training_description || 'Complete this training at your own pace.' }}</p>
        <p class="meta">Assigned by <strong>{{ data.assigned_by_full_name }}</strong></p>

        <div v-if="data.content_type === 'youtube' && youtubeId" class="media">
          <div class="ratio">
            <iframe
              :title="data.training_title"
              :src="`https://www.youtube-nocookie.com/embed/${youtubeId}`"
              allowfullscreen
            />
          </div>
        </div>
        <p v-else-if="data.content_type === 'external_link' && data.external_url" class="media">
          <a :href="data.external_url" target="_blank" rel="noopener noreferrer" class="resource-link">
            Open training resource →
          </a>
        </p>

        <p class="status-line">
          Status: <span class="pill">{{ statusLabel }}</span>
        </p>

        <div v-if="!done" class="actions">
          <button
            type="button"
            class="btn secondary"
            :disabled="busy || data.status === 'in_progress'"
            @click="setStatus('in_progress')"
          >
            Start / In progress
          </button>
          <button
            type="button"
            class="btn"
            :disabled="busy || data.status === 'completed'"
            @click="setStatus('completed')"
          >
            Mark complete
          </button>
        </div>
        <p v-else class="success">✓ Training complete. Thank you!</p>

        <div class="cta-box">
          <p>Manage all your work in Plenvo — 1 month free →</p>
          <RouterLink to="/signup" class="btn-cta">Start for free →</RouterLink>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { apiJson } from '@/api/client'
import { extractYoutubeId } from '@/utils/youtube'

const route = useRoute()
const loading = ref(true)
const error = ref('')
const data = ref(null)
const busy = ref(false)
const done = ref(false)

const youtubeId = computed(() =>
  data.value?.youtube_video_id ? extractYoutubeId(data.value.youtube_video_id) : null
)

const statusLabel = computed(() => {
  const s = data.value?.status || 'not_started'
  return s.replaceAll('_', ' ')
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    data.value = await apiJson(`/api/v1/training/token/${route.params.token}`)
    done.value = data.value.status === 'completed'
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Could not load training'
  } finally {
    loading.value = false
  }
}

async function setStatus(status) {
  busy.value = true
  error.value = ''
  try {
    const res = await apiJson(`/api/v1/training/token/${route.params.token}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    })
    data.value = { ...data.value, status: res.status, started_at: res.started_at, completed_at: res.completed_at }
    if (res.status === 'completed') done.value = true
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Could not save progress'
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Instrument+Serif:ital@0;1&display=swap');

.training-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 2rem 1rem;
  font-family: 'Inter', sans-serif;
  background: radial-gradient(ellipse 80% 50% at 50% -20%, rgba(196, 163, 90, 0.11), transparent), var(--color-bg);
}

.panel {
  width: 100%;
  max-width: 640px;
  padding: 2rem;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: calc(var(--radius) + 4px);
  box-shadow: var(--shadow);
}

.logo {
  font-family: 'Instrument Serif', serif;
  font-size: 1.5rem;
  color: var(--color-accent);
  text-decoration: none;
  display: inline-block;
  margin-bottom: 1.5rem;
}

.eyebrow {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-text-muted);
  margin: 0 0 0.5rem;
}

h1 {
  font-family: 'Instrument Serif', serif;
  font-size: 2rem;
  font-weight: 400;
  margin: 0 0 0.75rem;
}

.lede {
  color: var(--color-text-muted);
  margin: 0 0 1rem;
  line-height: 1.6;
}

.meta {
  font-size: 0.9rem;
  color: var(--color-text-muted);
  margin: 0 0 1.25rem;
}

.media {
  margin-bottom: 1.25rem;
}

.ratio {
  position: relative;
  padding-bottom: 56.25%;
  height: 0;
  overflow: hidden;
  border-radius: 8px;
  border: 1px solid var(--color-border);
}

.ratio iframe {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border: 0;
}

.resource-link {
  display: inline-block;
  padding: 0.6rem 1rem;
  border-radius: 8px;
  background: var(--color-accent-soft);
  color: var(--color-accent);
  text-decoration: none;
  font-weight: 500;
}

.status-line {
  margin: 0 0 1rem;
  font-size: 0.9rem;
}

.pill {
  display: inline-block;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  color: var(--color-accent);
  text-transform: capitalize;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.btn {
  font-family: 'Inter', sans-serif;
  font-weight: 600;
  padding: 0.65rem 1.1rem;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--color-accent), #a6853a);
  color: #0f1210;
  cursor: pointer;
}

.btn.secondary {
  background: transparent;
  color: var(--color-text);
  border: 1px solid var(--color-border);
}

.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.success {
  color: #4ade80;
  margin-bottom: 1.5rem;
}

.cta-box {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--color-border);
  text-align: center;
}

.cta-box p {
  margin: 0 0 0.75rem;
  color: var(--color-text-muted);
  font-size: 0.9rem;
}

.btn-cta {
  display: inline-block;
  padding: 0.65rem 1.25rem;
  border-radius: 999px;
  background: var(--color-accent-soft);
  color: var(--color-accent);
  text-decoration: none;
  font-weight: 600;
  border: 1px solid var(--color-border);
}

.muted {
  color: var(--color-text-muted);
}

.alert.error {
  padding: 0.65rem 0.75rem;
  border-radius: 8px;
  color: #f0d0d0;
  background: rgba(180, 60, 60, 0.18);
  border: 1px solid rgba(180, 60, 60, 0.3);
}
</style>
