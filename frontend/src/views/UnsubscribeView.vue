<template>
  <div class="auth-page">
    <div class="panel">
      <p class="eyebrow">Plenvo</p>
      <h1>{{ title }}</h1>
      <p v-if="loading" class="lede">Updating your email preferences…</p>
      <p v-else class="lede">{{ body }}</p>
      <p class="foot">
        <RouterLink to="/login">Sign in</RouterLink>
        <span> · </span>
        <RouterLink to="/app/profile">Profile</RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { apiJson } from '@/api/client'

const route = useRoute()
const loading = ref(true)
const title = ref('Unsubscribe')
const body = ref('')

onMounted(async () => {
  const token = typeof route.query.token === 'string' ? route.query.token.trim() : ''
  if (!token) {
    title.value = 'Link not valid'
    body.value = 'This unsubscribe link is missing a token. Open the Unsubscribe link from a Plenvo email, or change preferences in Profile → Notifications.'
    loading.value = false
    return
  }
  try {
    const data = await apiJson(
      `/api/v1/email/unsubscribe?token=${encodeURIComponent(token)}&format=json`,
      { skipAuth: true },
    )
    title.value = data?.title || "You're unsubscribed"
    body.value =
      data?.body ||
      'You will no longer receive non-essential Plenvo emails. Password resets may still be sent when required.'
  } catch (err) {
    title.value = 'Link not valid'
    body.value =
      err?.message ||
      'This unsubscribe link is invalid or has already expired. You can also turn off emails in Profile → Notifications.'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
}

.panel {
  width: 100%;
  max-width: 400px;
  padding: 2rem 1.75rem;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: calc(var(--radius) + 4px);
  box-shadow: var(--shadow);
}

.eyebrow {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: var(--color-accent);
  margin: 0 0 0.5rem;
}

h1 {
  font-family: var(--font-display);
  font-weight: 400;
  font-size: 1.75rem;
  margin: 0 0 0.5rem;
}

.lede {
  margin: 0 0 1.25rem;
  font-size: 0.9rem;
  line-height: 1.5;
  color: var(--color-text-muted);
}

.foot {
  margin: 1.25rem 0 0;
  text-align: center;
  font-size: 0.85rem;
}

.foot a {
  color: var(--color-text-muted);
  text-decoration: none;
}

.foot a:hover {
  color: var(--color-accent);
}
</style>
