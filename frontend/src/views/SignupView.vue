<template>
  <div class="signup-page">
    <div class="panel">
      <RouterLink to="/" class="back-link">← Back to Plenvo</RouterLink>
      <p class="eyebrow">Plenvo</p>
      <h1>Start your free trial</h1>
      <p class="lede">30 days free. Your card won't be charged until day 31. Cancel anytime.</p>

      <p v-if="error" class="alert error" role="alert">{{ error }}</p>

      <div v-if="!done" class="form">
        <div class="steps">
          <span :class="['step', step >= 1 ? 'active' : '']">1 · Plan</span>
          <span class="step-sep">→</span>
          <span :class="['step', step >= 2 ? 'active' : '']">2 · Details</span>
          <span class="step-sep">→</span>
          <span :class="['step', step >= 3 ? 'active' : '']">3 · Payment</span>
        </div>

        <!-- Step 1: Plan Selection -->
        <template v-if="step === 1">
          <div class="plan-selector">
            <label 
              v-for="plan in plans" 
              :key="plan.id"
              :class="['plan-option', { selected: form.plan === plan.id }]"
              @click="form.plan = plan.id"
            >
              <input type="radio" :value="plan.id" v-model="form.plan" style="display: none" />
              <div class="plan-header">
                <span class="plan-name">{{ plan.name }}</span>
                <span v-if="plan.popular" class="popular-badge">Most popular</span>
              </div>
              <div class="plan-price-row">
                <span class="plan-price">{{ plan.price }}</span>
                <span class="plan-period">/ month</span>
              </div>
              <div class="plan-members">{{ plan.members }}</div>
              <div class="plan-check">✓</div>
            </label>
          </div>
          <button class="btn" :disabled="!form.plan" @click="step = 2">
            Continue →
          </button>
        </template>

        <!-- Step 2: Your Details -->
        <template v-if="step === 2">
          <label class="field">
            <span>Full name *</span>
            <input v-model="form.full_name" type="text" placeholder="Jane Smith" required :disabled="loading" />
          </label>
          <label class="field">
            <span>Work email *</span>
            <input v-model="form.email" type="email" placeholder="you@company.com" required :disabled="loading" />
          </label>
          <label class="field">
            <span>Password *</span>
            <input v-model="form.password" type="password" placeholder="Min 8 characters" minlength="8" required :disabled="loading" />
          </label>
          <label class="field">
            <span>Company name *</span>
            <input v-model="form.company_name" type="text" placeholder="Acme Corp" required :disabled="loading" />
          </label>
          <label class="field">
            <span>Your position *</span>
            <select v-model="form.position" required :disabled="loading">
              <option value="" disabled>Select your role</option>
              <option value="CEO">CEO</option>
              <option value="COO">COO</option>
              <option value="CTO">CTO</option>
              <option value="CFO">CFO</option>
              <option value="Director">Director</option>
              <option value="Project Manager">Project Manager</option>
              <option value="Manager">Manager</option>
              <option value="Team Lead">Team Lead</option>
              <option value="Other">Other</option>
            </select>
          </label>
          <div class="step2-actions">
            <button class="btn-back" @click="step = 1" :disabled="loading">← Back</button>
            <button class="btn" :disabled="!step2Valid" @click="goToStep3">
              Continue to payment →
            </button>
          </div>
        </template>

        <!-- Step 3: Payment -->
        <template v-if="step === 3">
          <div class="trial-info">
            <span class="trial-icon">🎁</span>
            <div>
              <strong>30 days completely free</strong>
              <p>Your card is saved securely via Stripe. You won't be charged until day 31.</p>
            </div>
          </div>

          <label class="field">
            <span>Card details</span>
            <div id="card-element" class="card-element" />
          </label>

          <div class="step2-actions">
            <button class="btn-back" @click="step = 2" :disabled="loading">← Back</button>
            <button class="btn" :disabled="loading || !stripeReady" @click="onSubmit">
              {{ loading ? 'Starting trial…' : 'Start free trial →' }}
            </button>
          </div>

          <p class="stripe-note">🔒 Payment secured by Stripe · We never store card details</p>
        </template>
      </div>

      <!-- Success -->
      <div v-if="done" class="done-state">
        <div class="done-icon">✓</div>
        <h2>Welcome to Plenvo!</h2>
        <p>Your 30-day free trial has started. Redirecting to your dashboard...</p>
      </div>

      <p class="signin-link">Already have an account? <RouterLink to="/login">Sign in</RouterLink></p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { loadStripe } from '@stripe/stripe-js'
import { apiJson } from '@/api/client'
import { setSessionUser } from '@/composables/session'
import { login } from '@/services/auth'

const router = useRouter()
const step = ref(1)
const loading = ref(false)
const error = ref('')
const done = ref(false)
const stripeReady = ref(false)

const plans = [
  { id: 'starter', name: 'Starter', price: '£25', members: 'Up to 5 team members', popular: false },
  { id: 'growth', name: 'Growth', price: '£49', members: 'Up to 20 team members', popular: true },
]

const form = ref({ 
  plan: 'growth', // default to most popular
  full_name: '', 
  email: '', 
  password: '', 
  company_name: '', 
  position: '' 
})

let stripe = null
let cardElement = null

const step2Valid = computed(() =>
  form.value.full_name.trim() &&
  form.value.email.trim() &&
  form.value.password.length >= 8 &&
  form.value.company_name.trim() &&
  form.value.position
)

async function goToStep3() {
  step.value = 3
  await nextTick()
  await mountStripe()
}

async function mountStripe() {
  const key = import.meta.env.VITE_STRIPE_PUBLIC_KEY
  if (!key) { error.value = 'Payment not configured. Contact hi@plenvo.io'; return }
  stripe = await loadStripe(key)
  const elements = stripe.elements()
  cardElement = elements.create('card', {
    style: {
      base: {
        color: '#e8e4d8', fontFamily: 'Inter, sans-serif', fontSize: '15px',
        '::placeholder': { color: 'rgba(232,228,216,0.35)' },
      },
      invalid: { color: '#f87171' },
    },
  })
  cardElement.mount('#card-element')
  cardElement.on('ready', () => { stripeReady.value = true })
}

async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    const { paymentMethod, error: se } = await stripe.createPaymentMethod({
      type: 'card', card: cardElement,
      billing_details: { name: form.value.full_name, email: form.value.email },
    })
    if (se) { error.value = se.message; loading.value = false; return }

    await apiJson('/signup', {
      method: 'POST',
      body: JSON.stringify({ 
        ...form.value, 
        stripe_payment_method_id: paymentMethod.id,
        plan: form.value.plan, // send selected plan to backend
      }),
    })

    const me = await login(form.value.email, form.value.password)
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
  min-height: 100vh; display: grid; place-items: center;
  padding: 2rem 1rem; font-family: 'Inter', sans-serif;
  background: radial-gradient(ellipse 80% 50% at 50% -20%, rgba(196,163,90,0.11), transparent), var(--color-bg);
}
.panel {
  width: 100%; max-width: 460px;
  padding: 2.25rem 2rem;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: calc(var(--radius) + 4px);
  box-shadow: var(--shadow);
  animation: fadeUp 0.65s cubic-bezier(.22,1,.36,1) both;
}
.back-link { font-size: 0.8rem; color: var(--color-text-muted); text-decoration: none; display: inline-block; margin-bottom: 1.25rem; }
.back-link:hover { color: var(--color-text); text-decoration: none; }
.eyebrow { font-family: 'Instrument Serif', serif; font-size: 1.1rem; color: var(--color-accent); margin: 0 0 0.25rem; letter-spacing: 0.04em; }
h1 { font-family: 'Instrument Serif', serif; font-size: 1.9rem; font-weight: 400; margin: 0 0 0.4rem; color: var(--color-text); }
.lede { font-size: 0.875rem; color: var(--color-text-muted); margin: 0 0 1.5rem; line-height: 1.6; font-weight: 300; }

.steps { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1.5rem; font-size: 0.72rem; flex-wrap: wrap; }
.step { color: var(--color-text-muted); transition: color 0.2s; white-space: nowrap; }
.step.active { color: var(--color-accent); font-weight: 600; }
.step-sep { color: var(--color-border); }

.form { display: flex; flex-direction: column; gap: 1rem; }

/* Plan Selector */
.plan-selector { display: flex; flex-direction: column; gap: 0.75rem; }
.plan-option {
  position: relative;
  display: flex; flex-direction: column; gap: 0.25rem;
  padding: 1rem 1.25rem; border-radius: 8px;
  border: 2px solid var(--color-border);
  background: var(--color-surface); cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}
.plan-option:hover { border-color: rgba(196,163,90,0.5); }
.plan-option.selected { 
  border-color: var(--color-accent); 
  background: rgba(196,163,90,0.05);
}
.plan-header { display: flex; align-items: center; gap: 0.5rem; }
.plan-name { font-size: 0.95rem; font-weight: 600; color: var(--color-text); }
.popular-badge {
  font-size: 0.65rem; font-weight: 600; text-transform: uppercase;
  padding: 0.2rem 0.5rem; border-radius: 4px;
  background: rgba(196,163,90,0.2); color: var(--color-accent);
  letter-spacing: 0.05em;
}
.plan-price-row { display: flex; align-items: baseline; gap: 0.25rem; }
.plan-price { font-family: 'Instrument Serif', serif; font-size: 1.75rem; color: var(--color-accent); line-height: 1; }
.plan-period { font-size: 0.8rem; color: var(--color-text-muted); }
.plan-members { font-size: 0.8rem; color: var(--color-text-muted); }
.plan-check {
  position: absolute; top: 1rem; right: 1rem;
  width: 20px; height: 20px; border-radius: 50%;
  border: 2px solid var(--color-border);
  display: flex; align-items: center; justify-content: center;
  font-size: 0.7rem; color: transparent;
  transition: border-color 0.2s, color 0.2s, background 0.2s;
}
.plan-option.selected .plan-check {
  border-color: var(--color-accent);
  background: var(--color-accent);
  color: #0f1210;
}

.field { display: flex; flex-direction: column; gap: 0.35rem; font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--color-text-muted); }
.field input, .field select {
  font-family: 'Inter', sans-serif; font-size: 0.95rem;
  padding: 0.65rem 0.75rem; border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-surface); color: var(--color-text);
  outline: none; transition: border-color 0.2s;
}
.field input:focus, .field select:focus { border-color: var(--color-accent); }
.field input:disabled, .field select:disabled { opacity: 0.55; }
.field select option { background: var(--color-surface); }

.trial-info {
  display: flex; gap: 0.875rem; align-items: flex-start;
  padding: 0.875rem; background: rgba(196,163,90,0.08);
  border: 1px solid rgba(196,163,90,0.2); border-radius: 8px;
}
.trial-icon { font-size: 1.2rem; flex-shrink: 0; }
.trial-info strong { display: block; font-size: 0.875rem; color: var(--color-text); margin-bottom: 0.2rem; }
.trial-info p { margin: 0; font-size: 0.8rem; color: var(--color-text-muted); line-height: 1.5; }

.card-element { padding: 0.75rem; border-radius: 8px; border: 1px solid var(--color-border); background: var(--color-surface); }
.stripe-note { font-size: 0.72rem; color: var(--color-text-muted); text-align: center; margin: 0; }

.btn {
  font-family: 'Inter', sans-serif; font-weight: 600; font-size: 0.9rem;
  padding: 0.7rem 1rem; border: none; border-radius: 8px;
  background: linear-gradient(135deg, var(--color-accent), #a6853a);
  color: #0f1210; cursor: pointer; transition: filter 0.2s, opacity 0.2s; flex: 1;
}
.btn:hover:not(:disabled) { filter: brightness(1.07); }
.btn:disabled { opacity: 0.55; cursor: not-allowed; }

.step2-actions { display: flex; gap: 0.75rem; }
.btn-back {
  font-family: 'Inter', sans-serif; font-size: 0.875rem;
  background: none; border: 1px solid var(--color-border);
  color: var(--color-text-muted); padding: 0.65rem 1rem;
  border-radius: 8px; cursor: pointer; transition: border-color 0.2s; white-space: nowrap;
}
.btn-back:hover { border-color: var(--color-accent); color: var(--color-text); }

.alert { padding: 0.65rem 0.75rem; border-radius: 8px; font-size: 0.85rem; margin-bottom: 0.5rem; }
.error { color: #f0d0d0; background: rgba(180,60,60,0.18); border: 1px solid rgba(180,60,60,0.3); }

.done-state { text-align: center; padding: 1.5rem 0; }
.done-icon { width: 52px; height: 52px; border-radius: 50%; background: rgba(60,140,100,0.2); color: #4ade80; font-size: 1.5rem; display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem; }
.done-state h2 { font-family: 'Instrument Serif', serif; font-weight: 400; margin: 0 0 0.5rem; }
.done-state p { font-size: 0.875rem; color: var(--color-text-muted); margin: 0; }

.signin-link { text-align: center; font-size: 0.82rem; color: var(--color-text-muted); margin-top: 1.25rem; margin-bottom: 0; }
.signin-link a { color: var(--color-accent); text-decoration: none; }
.signin-link a:hover { text-decoration: underline; }

@keyframes fadeUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
</style>