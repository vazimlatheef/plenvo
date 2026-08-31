<template>
  <div>
    <PageHeader
      eyebrow="Content"
      title="New training"
      description="Publish a video or link your team can complete on their own time. Use YouTube or an external link."
    />
    <section class="card">
      <p v-if="error" class="alert-error">{{ error }}</p>
      <form class="form" @submit.prevent="onSubmit">
        <label class="field">
          <span>Title</span>
          <input v-model="title" required maxlength="300" :disabled="busy" placeholder="e.g. Annual compliance refresher" />
        </label>
        <label class="field">
          <span>Description (optional)</span>
          <textarea v-model="description" rows="3" :disabled="busy" placeholder="What should team members take away?" />
        </label>
        <label class="field">
          <span>How team members view it</span>
          <select v-model="contentType" :disabled="busy">
            <option value="youtube">YouTube video</option>
            <option value="external_link">External link</option>
          </select>
        </label>
        <label v-if="contentType === 'youtube'" class="field">
          <span>YouTube video ID or URL</span>
          <input
            v-model="youtubeVideoId"
            placeholder="youtube.com/watch?v=… or youtube.com/shorts/…"
            :disabled="busy"
          />
        </label>
        <label v-if="contentType === 'external_link'" class="field">
          <span>Resource URL</span>
          <input v-model="externalUrl" type="text" inputmode="url" placeholder="docs.google.com" :disabled="busy" />
        </label>
        <button type="submit" class="btn" :disabled="busy">{{ busy ? 'Saving…' : 'Publish training' }}</button>
      </form>
      <p v-if="createdId" class="ok">
        <strong>{{ createdTitle }}</strong> is live.
        <RouterLink
          :to="{
            name: 'training-summary',
            params: { trainingId: createdId },
            query: { title: createdTitle },
          }"
        >
          View completion summary
        </RouterLink>
      </p>
    </section>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

import { apiJson } from '@/api/client'
import PageHeader from '@/components/PageHeader.vue'
import { rememberLastTraining } from '@/utils/trainingCatalog'
import { resolveTrainingMedia } from '@/utils/trainingMedia'

const title = ref('')
const description = ref('')
const contentType = ref('youtube')
const youtubeVideoId = ref('')
const externalUrl = ref('')
const busy = ref(false)
const error = ref('')
const createdId = ref(null)
const createdTitle = ref('')

watch(contentType, () => {
  error.value = ''
})

async function onSubmit() {
  error.value = ''
  createdId.value = null
  createdTitle.value = ''
  const media = resolveTrainingMedia({
    contentType: contentType.value,
    youtubeInput: youtubeVideoId.value,
    externalInput: externalUrl.value,
  })
  if (media.error) {
    error.value = media.error
    return
  }
  const body = {
    title: title.value.trim(),
    description: description.value.trim() || null,
    content_type: media.content_type,
    external_url: media.external_url,
    youtube_video_id: media.youtube_video_id,
  }
  busy.value = true
  try {
    const res = await apiJson('/api/v1/trainings', {
      method: 'POST',
      body: JSON.stringify(body),
    })
    createdId.value = res.id
    createdTitle.value = res.title || title.value.trim()
    rememberLastTraining({ id: res.id, title: createdTitle.value })
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed'
  } finally {
    busy.value = false
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
.field textarea,
.field select {
  font-family: var(--font-body);
  font-size: 1rem;
  padding: 0.65rem 0.75rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-bg-elevated);
  color: var(--color-text);
}

.field input:focus,
.field textarea:focus,
.field select:focus {
  outline: none;
  border-color: var(--color-accent);
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
  color: var(--color-text);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
}

.ok {
  margin: 1rem 0 0;
  font-size: 0.9rem;
  color: var(--color-text-muted);
}

.ok strong {
  color: var(--color-text);
}
</style>
