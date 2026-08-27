<template>
  <div class="signup-page">
    <div class="panel">
      <RouterLink to="/" class="back-link">← Back to Plenvo</RouterLink>

      <p class="eyebrow">Plenvo</p>
      <h1>Start your {{ planLabel }} trial</h1>
      <p class="lede">14 days free on the {{ planLabel }} plan. No credit card required. Cancel anytime.</p>

      <p v-if="error" class="alert error" role="alert">{{ error }}</p>

      <form v-if="!done" class="form" @submit.prevent="onSubmit">
        <label class="field">
          <span>Work email</span>
          <input
            v-model="email"
            type="email"
            autocomplete="username"
            placeholder="you@company.com"
            required
            :disabled="loading"
          />
        </label>
        <label class="field">
          <span>Password</span>
          <input
            v-model="password"
            type="password"
            autocomplete="new-password"
            placeholder="Min 8 characters"
            minlength="8"
            required
            :disabled="loading"
          />
        </label>
        <button type="submit" class="btn" :disabled="loading || !canSubmit">
          {{ loading ? 'Creating account…' : 'Create my account →' }}
        </button>
      </form>

      <div v-if="done" class="done-state">
        <div class="done-icon">✓</div>
        <h2>Welcome to Plenvo!</h2>
        <p>Your 14-day free trial has started. Check your inbox to verify your email — redirecting to your dashboard...</p>
      </div>

      <p class="signin-link">Already have an account? <RouterLink to="/login">Sign in</RouterLink></p>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { apiJson } from '@/api/client'
import { useCurrency } from '@/composables/useCurrency'
import { setSessionUser } from '@/composables/session'
import { login } from '@/services/auth'

const router = useRouter()
const route = useRoute()
const { currency, country, loaded: currencyLoaded, detect } = useCurrency()

const PLAN_LABELS = { personal: 'Personal', team: 'Team', enterprise: 'Enterprise' }

const selectedPlan = computed(() => {
  const raw = String(route.query.plan || 'team').toLowerCase()
  return PLAN_LABELS[raw] ? raw : 'team'
})

const planLabel = computed(() => PLAN_LABELS[selectedPlan.value] || 'Team')

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const done = ref(false)

const canSubmit = computed(() => email.value.trim() && password.value.length >= 8)

onMounted(() => {
  detect({ force: true })
})

async function onSubmit() {
  if (!canSubmit.value) return
  error.value = ''
  loading.value = true
  try {
    if (!currencyLoaded.value) {
      await detect()
    }
    await apiJson('/api/v1/signup', {
      method: 'POST',
      body: JSON.stringify({
        email: email.value.trim(),
        password: password.value,
        currency: currency.value || 'USD',
        country_code: country.value || null,
        plan_tier: selectedPlan.value,
      }),
    })

    const me = await login(email.value.trim(), password.value)
    setSessionUser(me)
    done.value = true
    setTimeout(() => router.replace({ name: 'admin-dashboard' }), 2000)
  } catch (e) {
    error.value = e?.message || 'Signup failed. Please try again or contact hi@plenvo.io'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Instrument+Serif:ital@0;1&display=swap');

.signup-page {
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
  animation: fadeUp 0.65s cubic-bezier(0.22, 1, 0.36, 1) both;
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

h1 {
  font-family: 'Instrument Serif', serif;
  font-size: 1.9rem;
  font-weight: 400;
  margin: 0 0 0.4rem;
}

.lede {
  font-size: 0.875rem;
  color: var(--color-text-muted);
  margin: 0 0 1.5rem;
  line-height: 1.6;
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
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-text-muted);
}

.field input {
  font-family: 'Inter', sans-serif;
  font-size: 0.95rem;
  padding: 0.65rem 0.75rem;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
  text-transform: none;
  letter-spacing: normal;
}

.btn {
  font-weight: 600;
  padding: 0.7rem 1rem;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--color-accent), #a6853a);
  color: #0f1210;
  cursor: pointer;
}

.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.alert.error {
  padding: 0.65rem 0.75rem;
  border-radius: 8px;
  color: #f0d0d0;
  background: rgba(180, 60, 60, 0.18);
  border: 1px solid rgba(180, 60, 60, 0.3);
  margin-bottom: 1rem;
}

.done-state {
  text-align: center;
  padding: 1.5rem 0;
}

.done-icon {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: rgba(60, 140, 100, 0.2);
  color: #4ade80;
  font-size: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
}

.signin-link {
  text-align: center;
  font-size: 0.82rem;
  color: var(--color-text-muted);
  margin-top: 1.25rem;
}

@keyframes fadeUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
