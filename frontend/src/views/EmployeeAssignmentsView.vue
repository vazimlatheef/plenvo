<template>
  <div>
    <PageHeader
      eyebrow="Your work"
      title="Assignments"
      description="Complete each item on your own time. Your manager sees progress — no chasing email threads."
    />
    <p v-if="loading" class="muted">Loading your assignments…</p>
    <p v-else-if="error" class="alert-error">{{ error }}</p>
    <p v-else-if="!items.length" class="muted">Nothing assigned yet. When your manager assigns training, it will appear here.</p>
    <div v-else class="list">
      <article v-for="a in items" :key="a.id" class="card">
        <header class="head">
          <span class="aid">{{ labelForCard(a) }}</span>
          <span class="status" :data-s="a.status">{{ a.status.replaceAll('_', ' ') }}</span>
        </header>
        <p v-if="user?.role === 'admin'" class="assignee-line">{{ assigneeLabel(a) }}</p>
        <h2 class="title">{{ a.training_title }}</h2>
        <p class="desc">{{ a.training_description || '—' }}</p>

        <div v-if="a.content_type === 'youtube' && embedId(a)" class="media">
          <div class="ratio">
            <iframe
              :title="`Video: ${a.training_title}`"
              :src="embedUrl(a)"
              loading="lazy"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
              referrerpolicy="strict-origin-when-cross-origin"
              allowfullscreen
            />
          </div>
        </div>
        <p v-else-if="a.content_type === 'youtube' && !embedId(a)" class="media muted small">
          Add a valid YouTube link or ID to this training (admin can edit in the system).
        </p>
        <p v-else-if="a.content_type === 'external_link' && a.external_url" class="media">
          <a :href="a.external_url" class="resource-link" target="_blank" rel="noopener noreferrer">
            Open training resource
          </a>
        </p>
        <p v-else-if="a.content_type === 'upload'" class="muted small">
          This training uses a file upload. Ask your admin to switch to YouTube or an external link if you cannot access the file.
        </p>

        <div v-if="canUpdate(a)" class="actions">
          <button
            type="button"
            class="btn secondary"
            :disabled="busyId === a.id || a.status === 'in_progress'"
            @click="setProgress(a, 'in_progress')"
          >
            Mark in progress
          </button>
          <button
            type="button"
            class="btn"
            :disabled="busyId === a.id || a.status === 'completed'"
            @click="setProgress(a, 'completed')"
          >
            Mark completed
          </button>
        </div>
        <p v-else-if="user?.role === 'admin'" class="muted small">
          Only the assignee can update progress on this card.
        </p>
        <p v-if="a.started_at || a.completed_at" class="meta small">
          <span v-if="a.started_at">Started {{ formatTs(a.started_at) }}</span>
          <span v-if="a.completed_at"> · Completed {{ formatTs(a.completed_at) }}</span>
        </p>
      </article>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'

import { apiJson } from '@/api/client'
import { user } from '@/composables/session'
import PageHeader from '@/components/PageHeader.vue'
import { extractYoutubeId, youtubeEmbedUrl } from '@/utils/youtube'

const loading = ref(true)
const error = ref('')
const items = ref([])
const busyId = ref(null)

function canUpdate(a) {
  const mine = user.value?.email?.toLowerCase?.()
  const theirs = a.assignee_email?.toLowerCase?.()
  return Boolean(mine && theirs && mine === theirs)
}

function embedId(a) {
  return extractYoutubeId(a.youtube_video_id || '')
}

function embedUrl(a) {
  const id = embedId(a)
  return id ? youtubeEmbedUrl(id) : ''
}

function labelForCard(a) {
  if (user.value?.role === 'admin') {
    return 'Team assignment'
  }
  return 'Your assignment'
}

function assigneeLabel(a) {
  const name = a.assignee_full_name || 'Team member'
  const email = a.assignee_email || ''
  return email ? `${name} · ${email}` : name
}

function formatTs(iso) {
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const res = await apiJson('/api/v1/assignments')
    items.value = res.items || []
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to load'
  } finally {
    loading.value = false
  }
}

async function setProgress(row, status) {
  busyId.value = row.id
  error.value = ''
  try {
    const updated = await apiJson(`/api/v1/assignments/${row.id}/progress`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    })
    const i = items.value.findIndex((x) => x.id === row.id)
    if (i !== -1) {
      items.value[i] = {
        ...items.value[i],
        status: updated.status,
        started_at: updated.started_at,
        completed_at: updated.completed_at,
      }
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Update failed'
  } finally {
    busyId.value = null
  }
}

onMounted(load)
</script>

<style scoped>
.list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 1.15rem 1.25rem;
}

.head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.aid {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  letter-spacing: 0.04em;
}

.assignee-line {
  margin: 0 0 0.5rem;
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.status {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  padding: 0.25rem 0.5rem;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  color: var(--color-accent);
}

.title {
  font-family: var(--font-display);
  font-size: 1.35rem;
  margin: 0 0 0.35rem;
}

.desc {
  margin: 0 0 1rem;
  font-size: 0.9rem;
  color: var(--color-text-muted);
}

.media {
  margin-bottom: 1rem;
}

.resource-link {
  display: inline-block;
  font-weight: 500;
  padding: 0.5rem 0.85rem;
  border-radius: 8px;
  background: var(--color-accent-soft);
  border: 1px solid var(--color-border);
  text-decoration: none;
  color: var(--color-accent);
}

.resource-link:hover {
  border-color: var(--color-accent);
}

.ratio {
  position: relative;
  padding-bottom: 56.25%;
  height: 0;
  overflow: hidden;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: #0a0a0a;
}

.ratio iframe {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: 0;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.btn {
  font-family: var(--font-body);
  font-size: 0.85rem;
  font-weight: 500;
  padding: 0.5rem 0.85rem;
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
  opacity: 0.5;
  cursor: not-allowed;
}

.meta {
  margin: 0.75rem 0 0;
  color: var(--color-text-muted);
}

.small {
  font-size: 0.85rem;
}

.muted {
  color: var(--color-text-muted);
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
