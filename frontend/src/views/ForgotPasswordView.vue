<template>
  <div class="auth-page">
    <div class="panel">
      <p class="eyebrow">Plenvo</p>
      <h1>Forgot password</h1>
      <p class="lede">Enter your email address and we'll send a reset link if an account exists.</p>

      <p v-if="error" class="error" role="alert">{{ error }}</p>
      <div v-if="done" class="success-block" role="status">
        <p class="success">{{ done }}</p>
        <p class="hint">
          Didn’t get it? Check your spam or junk folder — reset emails sometimes land there.
          The link expires in 1 hour.
        </p>
      </div>

      <form v-if="!done" class="form" @submit.prevent="onSubmit">
        <label class="field">
          <span>Email</span>
          <input
            v-model="email"
            type="email"
            autocomplete="username"
            placeholder="you@company.com"
            required
            :disabled="loading"
          />
        </label>
        <button type="submit" class="btn" :disabled="loading || !email.trim()">
          {{ loading ? 'Sending…' : 'Send reset link' }}
        </button>
        <p class="hint">If you don’t see the email within a few minutes, check spam or junk.</p>
      </form>

      <p class="foot">
        <RouterLink to="/login">← Back to sign in</RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

import { apiJson } from '@/api/client'

const email = ref('')
const loading = ref(false)
const error = ref('')
const done = ref('')

async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    const res = await apiJson('/api/v1/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email: email.value.trim() }),
    })
    done.value = res.message || "If an account exists for that email, we've sent a password reset link."
  } catch (e) {
    error.value = e?.message || 'Something went wrong. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 2rem 1rem;
  background: radial-gradient(ellipse 80% 50% at 50% -20%, rgba(196, 163, 90, 0.15), transparent),
    var(--color-bg);
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
  color: var(--color-text-muted);
}

.error,
.success {
  margin: 0 0 1rem;
  padding: 0.6rem 0.75rem;
  border-radius: 8px;
  font-size: 0.85rem;
}

.success-block {
  margin: 0 0 1rem;
}

.success-block .success {
  margin: 0 0 0.65rem;
}

.hint {
  margin: 0;
  font-size: 0.8rem;
  line-height: 1.45;
  color: var(--color-text-muted);
  text-transform: none;
  letter-spacing: normal;
}

.form .hint {
  margin-top: -0.25rem;
}

.error {
  color: #f0d0d0;
  background: rgba(180, 60, 60, 0.2);
  border: 1px solid rgba(180, 60, 60, 0.35);
}

.success {
  color: var(--status-done);
  background: var(--status-done-bg);
  border: 1px solid var(--status-done-border);
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

.field input {
  font-family: var(--font-body);
  font-size: 1rem;
  padding: 0.65rem 0.75rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
  text-transform: none;
  letter-spacing: normal;
}

.field input:focus {
  outline: none;
  border-color: var(--color-accent);
}

.btn {
  font-family: var(--font-body);
  font-weight: 600;
  font-size: 0.95rem;
  padding: 0.65rem 1rem;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--color-accent), #a6853a);
  color: #0f1210;
  cursor: pointer;
}

.btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
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
