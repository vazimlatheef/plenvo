<template>
  <div class="login">
    <div class="panel">
      <p class="eyebrow">Plenvo</p>
      <h1>Sign in</h1>
      <p class="lede">
        Sign in with your email address. Plenvo sends you straight to what matters — no hunting for the right screen.
      </p>
      <p v-if="error" class="error" role="alert">{{ error }}</p>
      <form class="form" @submit.prevent="onSubmit">
        <label class="field">
          <span>Email</span>
          <input
            v-model="email"
            type="email"
            autocomplete="username"
            placeholder="you@company.com"
            :disabled="loading"
            required
          />
        </label>
        <label class="field">
          <span>Password</span>
          <input
            v-model="password"
            type="password"
            autocomplete="current-password"
            placeholder="••••••••"
            :disabled="loading"
            required
          />
        </label>
        <p class="forgot-row">
          <RouterLink to="/forgot-password">Forgot password?</RouterLink>
        </p>
        <button type="submit" class="btn" :disabled="loading">
          {{ loading ? 'Signing in…' : 'Continue' }}
        </button>
      </form>
      <p class="foot">
        Don’t have an account?
        <RouterLink to="/signup?plan=team">Start for free</RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { setSessionUser } from '@/composables/session'
import { login } from '@/services/auth'

const route = useRoute()
const router = useRouter()
const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    const me = await login(email.value.trim(), password.value)
    setSessionUser(me)
    const redir = typeof route.query.redirect === 'string' ? route.query.redirect : ''
    if (redir && redir.startsWith('/')) {
      router.replace(redir)
      return
    }
    if (me.role === 'admin') {
      router.replace({ name: 'admin-dashboard' })
    } else {
      router.replace({ name: 'employee-assignments' })
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Sign in failed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login {
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

.lede {
  margin: 0 0 1.25rem;
  font-size: 0.9rem;
}

.error {
  margin: 0 0 1rem;
  padding: 0.6rem 0.75rem;
  border-radius: 8px;
  font-size: 0.85rem;
  color: #f0d0d0;
  background: rgba(180, 60, 60, 0.2);
  border: 1px solid rgba(180, 60, 60, 0.35);
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
}

.field input:focus {
  outline: none;
  border-color: var(--color-accent);
}

.field input:disabled {
  opacity: 0.6;
}

.forgot-row {
  margin: -0.35rem 0 0;
  text-align: right;
  font-size: 0.82rem;
  text-transform: none;
  letter-spacing: normal;
}

.forgot-row a {
  color: var(--color-text-muted);
  text-decoration: none;
}

.forgot-row a:hover {
  color: var(--color-accent);
}

.btn {
  margin-top: 0.25rem;
  font-family: var(--font-body);
  font-weight: 500;
  font-size: 0.95rem;
  padding: 0.65rem 1rem;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--color-accent), #a6853a);
  color: #0f1210;
  cursor: pointer;
}

.btn:hover:not(:disabled) {
  filter: brightness(1.05);
}

.btn:disabled {
  cursor: not-allowed;
  opacity: 0.75;
}

.foot {
  margin: 1.25rem 0 0;
  text-align: center;
  font-size: 0.85rem;
  color: var(--color-text-muted);
}

.foot a {
  color: var(--color-accent);
  text-decoration: none;
  font-weight: 500;
}

.foot a:hover {
  text-decoration: underline;
}
</style>
