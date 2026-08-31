<template>
  <div class="auth-page">
    <div class="panel">
      <p class="eyebrow">Plenvo</p>
      <h1>Set a new password</h1>
      <p class="lede">Choose a new password for your account. Minimum 8 characters.</p>

      <p v-if="!token" class="error" role="alert">Missing reset token. Request a new link from the sign-in page.</p>
      <p v-else-if="error" class="error" role="alert">{{ error }}</p>
      <p v-if="done" class="success" role="status">{{ done }}</p>

      <form v-if="token && !done" class="form" @submit.prevent="onSubmit">
        <label class="field">
          <span>New password</span>
          <PasswordField
            v-model="password"
            autocomplete="new-password"
            placeholder="Min 8 characters"
            :minlength="8"
            required
            :disabled="loading"
          />
        </label>
        <label class="field">
          <span>Confirm password</span>
          <PasswordField
            v-model="confirm"
            autocomplete="new-password"
            placeholder="Repeat password"
            :minlength="8"
            required
            :disabled="loading"
          />
        </label>
        <button type="submit" class="btn" :disabled="loading || !canSubmit">
          {{ loading ? 'Updating…' : 'Update password' }}
        </button>
      </form>

      <p class="foot">
        <RouterLink to="/login">{{ done ? 'Sign in →' : '← Back to sign in' }}</RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'

import { apiJson } from '@/api/client'
import PasswordField from '@/components/PasswordField.vue'

const route = useRoute()
const token = computed(() => (typeof route.query.token === 'string' ? route.query.token.trim() : ''))

const password = ref('')
const confirm = ref('')
const loading = ref(false)
const error = ref('')
const done = ref('')

const canSubmit = computed(
  () => password.value.length >= 8 && password.value === confirm.value,
)

async function onSubmit() {
  if (!canSubmit.value || !token.value) return
  if (password.value !== confirm.value) {
    error.value = 'Passwords do not match.'
    return
  }
  error.value = ''
  loading.value = true
  try {
    const res = await apiJson('/api/v1/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify({
        token: token.value,
        password: password.value,
      }),
    })
    done.value = res.message || 'Your password has been updated. You can sign in now.'
  } catch (e) {
    error.value = e?.message || 'Reset failed. Request a new link from the sign-in page.'
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
