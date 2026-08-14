<template>
  <div class="verify-page">
    <div class="panel">
      <RouterLink to="/" class="back-link">← Back to Plenvo</RouterLink>
      <p class="eyebrow">Plenvo</p>

      <div v-if="state === 'loading'" class="state">
        <h1>Verifying your email…</h1>
        <p class="lede">Just a moment while we confirm your link.</p>
      </div>

      <div v-else-if="state === 'verified' || state === 'already_verified'" class="state success">
        <div class="icon">✓</div>
        <h1>{{ state === 'verified' ? 'Email verified' : 'Already verified' }}</h1>
        <p class="lede">{{ message }}</p>
        <RouterLink to="/login" class="btn">Sign in →</RouterLink>
      </div>

      <div v-else-if="state === 'expired'" class="state warn">
        <div class="icon">!</div>
        <h1>Link expired</h1>
        <p class="lede">{{ message }}</p>
        <RouterLink to="/login" class="btn-outline">Go to sign in</RouterLink>
      </div>

      <div v-else class="state error">
        <div class="icon">×</div>
        <h1>Invalid link</h1>
        <p class="lede">{{ message || 'This verification link is invalid or has already been used.' }}</p>
        <RouterLink to="/signup" class="btn-outline">Create an account</RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { apiJson } from '@/api/client'

const route = useRoute()
const state = ref('loading')
const message = ref('')

onMounted(async () => {
  const token = typeof route.query.token === 'string' ? route.query.token.trim() : ''
  if (!token) {
    state.value = 'invalid'
    message.value = 'Missing verification token.'
    return
  }

  try {
    const res = await apiJson(`/api/v1/auth/verify-email?token=${encodeURIComponent(token)}`)
    state.value = res.status || 'invalid'
    message.value = res.message || ''
  } catch (e) {
    state.value = 'invalid'
    message.value = e?.message || 'Verification failed. Please try again.'
  }
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Instrument+Serif:ital@0;1&display=swap');

.verify-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 2rem 1rem;
  font-family: 'Inter', sans-serif;
  background: radial-gradient(ellipse 80% 50% at 50% -20%, rgba(196, 163, 90, 0.11), transparent),
    var(--color-bg);
}

.panel {
  width: 100%;
  max-width: 420px;
  padding: 2.25rem 2rem;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: calc(var(--radius) + 4px);
  box-shadow: var(--shadow);
}

.back-link {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  text-decoration: none;
  display: inline-block;
  margin-bottom: 1.25rem;
}

.eyebrow {
  font-family: 'Instrument Serif', serif;
  font-size: 1.1rem;
  color: var(--color-accent);
  margin: 0 0 0.25rem;
}

.state {
  text-align: center;
}

h1 {
  font-family: 'Instrument Serif', serif;
  font-size: 1.75rem;
  font-weight: 400;
  margin: 0 0 0.5rem;
}

.lede {
  font-size: 0.9rem;
  color: var(--color-text-muted);
  line-height: 1.6;
  margin: 0 0 1.5rem;
}

.icon {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0.5rem auto 1rem;
  font-size: 1.4rem;
  font-weight: 600;
}

.success .icon {
  background: rgba(60, 140, 100, 0.2);
  color: #4ade80;
}

.warn .icon {
  background: rgba(196, 163, 90, 0.15);
  color: var(--color-accent);
}

.error .icon {
  background: rgba(180, 60, 60, 0.18);
  color: #f87171;
}

.btn,
.btn-outline {
  display: inline-block;
  font-weight: 600;
  padding: 0.7rem 1.25rem;
  border-radius: 8px;
  text-decoration: none;
}

.btn {
  background: linear-gradient(135deg, var(--color-accent), #a6853a);
  color: #0f1210;
  border: none;
}

.btn-outline {
  border: 1px solid var(--color-border);
  color: var(--color-text);
}
</style>
