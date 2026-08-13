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

          <span :class="['step', step >= 3 ? 'active' : '']">3 · Account</span>

        </div>



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

          <p class="currency-note">Prices shown in {{ currencyLabel }}</p>

          <button class="btn" :disabled="!form.plan" @click="step = 2">Continue →</button>

        </template>



        <template v-if="step === 2">

          <div class="row-2">

            <label class="field">

              <span>First name *</span>

              <input v-model="form.first_name" type="text" placeholder="Jane" required :disabled="loading" />

            </label>

            <label class="field">

              <span>Last name *</span>

              <input v-model="form.last_name" type="text" placeholder="Smith" required :disabled="loading" />

            </label>

          </div>

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

            <span>Job title / Position *</span>

            <input

              v-model="form.position"

              type="text"

              placeholder="e.g. Software Engineer, Product Manager, Founder"

              required

              :disabled="loading"

            />

          </label>



          <label class="field">

            <span>Country *</span>

            <input

              v-model="countrySearch"

              type="text"

              placeholder="Search country…"

              class="search-inp"

              :disabled="loading"

            />

            <select v-model="form.country" required :disabled="loading" @change="onCountryChange">

              <option value="" disabled>Select country</option>

              <template v-if="!countrySearch.trim()">

                <optgroup label="Popular">

                  <option v-for="c in priorityCountries" :key="'p-' + c.code" :value="c.code">

                    {{ c.flag }} {{ c.name }} ({{ c.dial }})

                  </option>

                </optgroup>

                <option disabled>──────────</option>

                <option v-for="c in otherCountries" :key="c.code" :value="c.code">

                  {{ c.flag }} {{ c.name }} ({{ c.dial }})

                </option>

              </template>

              <option v-for="c in filteredCountries" v-else :key="c.code" :value="c.code">

                {{ c.flag }} {{ c.name }} ({{ c.dial }})

              </option>

            </select>

          </label>



          <label class="field">

            <span>Phone</span>

            <div class="phone-row">

              <span class="dial-display" aria-label="Country dial code">

                {{ selectedCountry?.flag || '🌍' }} {{ form.phone_country || '—' }}

              </span>

              <input v-model="form.phone_number" type="tel" placeholder="Phone number" :disabled="loading" />

            </div>

          </label>



          <label class="field">

            <span>LinkedIn URL</span>

            <input v-model="form.linkedin_url" type="url" placeholder="https://linkedin.com/in/…" :disabled="loading" />

          </label>



          <fieldset class="field radios">

            <span>Team size</span>

            <div class="radio-row">

              <label v-for="opt in teamSizeOptions" :key="opt.value" class="radio-opt">

                <input v-model="form.team_size" type="radio" :value="opt.value" :disabled="loading" />

                {{ opt.label }}

              </label>

            </div>

          </fieldset>



          <div class="step2-actions">

            <button class="btn-back" @click="step = 1" :disabled="loading">← Back</button>

            <button class="btn" :disabled="!step2Valid" @click="goToStep3">Continue →</button>

          </div>

        </template>



        <template v-if="step === 3">

          <div class="trial-info">

            <span class="trial-icon">🎁</span>

            <div>

              <strong>Your first month is completely free</strong>

              <p>

                We just need your card to keep your account active after day 30.

                You won't be charged anything today.

              </p>

            </div>

          </div>

          <label class="field">

            <span>Keep your account active</span>

            <div id="card-element" class="card-element" />

          </label>

          <p class="stripe-note">

            🔒 Card saved securely · {{ symbol }}0 charged today · Cancel before day 30, pay nothing

          </p>

          <div class="step2-actions">

            <button class="btn-back" @click="step = 2" :disabled="loading">← Back</button>

            <button class="btn" :disabled="loading || !stripeReady" @click="onSubmit">

              {{ loading ? 'Creating account…' : 'Create my account →' }}

            </button>

          </div>

        </template>

      </div>



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

import { ref, computed, nextTick, onMounted } from 'vue'

import { useRouter } from 'vue-router'

import { loadStripe } from '@stripe/stripe-js'

import { apiJson } from '@/api/client'

import { setSessionUser } from '@/composables/session'

import { login } from '@/services/auth'

import { useCurrency } from '@/composables/useCurrency'

import { COUNTRIES, getPriorityCountries, getOtherCountries, findCountry } from '@/data/countries'



const teamSizeOptions = [

  { value: '1', label: 'Just me' },

  { value: '2-5', label: '2–5' },

  { value: '6-20', label: '6–20' },

  { value: '20+', label: '20+' },

]



const router = useRouter()

const { symbol, prices, currencyLabel } = useCurrency()



const step = ref(1)

const loading = ref(false)

const error = ref('')

const done = ref(false)

const stripeReady = ref(false)

const countrySearch = ref('')



const priorityCountries = getPriorityCountries()

const otherCountries = getOtherCountries()



const plans = computed(() => [

  { id: 'personal', name: 'Personal', price: `${symbol.value}${prices.value.personal}`, members: '1 person, unlimited everything', popular: false },

  { id: 'team', name: 'Team', price: `${symbol.value}${prices.value.team}`, members: 'Up to 5 people', popular: true },

  { id: 'enterprise', name: 'Enterprise', price: `${symbol.value}${prices.value.enterprise}`, members: '5+ people, unlimited', popular: false },

])



const form = ref({

  plan: 'team',

  first_name: '',

  last_name: '',

  email: '',

  password: '',

  company_name: '',

  position: '',

  country: '',

  phone_country: '',

  phone_number: '',

  linkedin_url: '',

  team_size: '',

  timezone: '',

})



let stripe = null

let cardElement = null



const selectedCountry = computed(() => findCountry(form.value.country))



const filteredCountries = computed(() => {

  const q = countrySearch.value.trim().toLowerCase()

  if (!q) return COUNTRIES

  return COUNTRIES.filter(

    (c) =>

      c.name.toLowerCase().includes(q) ||

      c.code.toLowerCase().includes(q) ||

      c.dial.includes(q),

  )

})



const step2Valid = computed(

  () =>

    form.value.first_name.trim() &&

    form.value.last_name.trim() &&

    form.value.email.trim() &&

    form.value.password.length >= 8 &&

    form.value.company_name.trim() &&

    form.value.position.trim() &&

    form.value.country,

)



function detectCountryCode() {

  try {

    const locale = Intl.DateTimeFormat().resolvedOptions().locale || ''

    const part = locale.split('-')[1]

    if (part && COUNTRIES.some((c) => c.code === part.toUpperCase())) {

      return part.toUpperCase()

    }

  } catch {

    /* ignore */

  }

  return 'GB'

}



function onCountryChange() {

  const c = findCountry(form.value.country)

  if (c) form.value.phone_country = c.dial

}



onMounted(() => {

  form.value.country = detectCountryCode()

  form.value.timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || ''

  onCountryChange()

})



async function goToStep3() {

  step.value = 3

  await nextTick()

  await mountStripe()

}



async function mountStripe() {

  const key = import.meta.env.VITE_STRIPE_PUBLIC_KEY || ''

  if (!key) {

    error.value = 'Payment not configured. Contact hi@plenvo.io'

    return

  }

  stripe = await loadStripe(key)

  const elements = stripe.elements()

  cardElement = elements.create('card', {

    style: {

      base: {

        color: '#e8e4d8',

        fontFamily: 'Inter, sans-serif',

        fontSize: '15px',

        '::placeholder': { color: 'rgba(232,228,216,0.35)' },

      },

      invalid: { color: '#f87171' },

    },

  })

  cardElement.mount('#card-element')

  cardElement.on('ready', () => {

    stripeReady.value = true

  })

}



async function onSubmit() {

  error.value = ''

  loading.value = true

  try {

    const billingName = `${form.value.first_name} ${form.value.last_name}`.trim()

    const { paymentMethod, error: se } = await stripe.createPaymentMethod({

      type: 'card',

      card: cardElement,

      billing_details: { name: billingName, email: form.value.email },

    })

    if (se) {

      error.value = se.message

      loading.value = false

      return

    }



    await apiJson('/api/v1/signup', {

      method: 'POST',

      body: JSON.stringify({

        first_name: form.value.first_name.trim(),

        last_name: form.value.last_name.trim(),

        email: form.value.email.trim(),

        password: form.value.password,

        company_name: form.value.company_name.trim(),

        position: form.value.position.trim(),

        phone_country: form.value.phone_country || null,

        phone_number: form.value.phone_number.trim() || null,

        country: form.value.country || null,

        team_size: form.value.team_size || null,

        timezone: form.value.timezone || null,

        linkedin_url: form.value.linkedin_url.trim() || null,

        plan: form.value.plan,

        stripe_payment_method_id: paymentMethod.id,

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

  min-height: 100vh;

  display: grid;

  place-items: center;

  padding: 2rem 1rem;

  font-family: 'Inter', sans-serif;

  background: radial-gradient(ellipse 80% 50% at 50% -20%, rgba(196, 163, 90, 0.11), transparent), var(--color-bg);

}

.panel {

  width: 100%;

  max-width: 520px;

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

.steps {

  display: flex;

  align-items: center;

  gap: 0.5rem;

  margin-bottom: 1.5rem;

  font-size: 0.72rem;

  flex-wrap: wrap;

}

.step {

  color: var(--color-text-muted);

}

.step.active {

  color: var(--color-accent);

  font-weight: 600;

}

.step-sep {

  color: var(--color-border);

}

.form {

  display: flex;

  flex-direction: column;

  gap: 1rem;

}

.row-2 {

  display: grid;

  grid-template-columns: 1fr 1fr;

  gap: 0.75rem;

}

.plan-selector {

  display: flex;

  flex-direction: column;

  gap: 0.75rem;

}

.plan-option {

  position: relative;

  padding: 1rem 1.25rem;

  border-radius: 8px;

  border: 2px solid var(--color-border);

  background: var(--color-surface);

  cursor: pointer;

}

.plan-option.selected {

  border-color: var(--color-accent);

  background: rgba(196, 163, 90, 0.05);

}

.plan-header {

  display: flex;

  align-items: center;

  gap: 0.5rem;

}

.plan-name {

  font-weight: 600;

}

.popular-badge {

  font-size: 0.65rem;

  padding: 0.2rem 0.5rem;

  border-radius: 4px;

  background: rgba(196, 163, 90, 0.2);

  color: var(--color-accent);

}

.plan-price {

  font-family: 'Instrument Serif', serif;

  font-size: 1.75rem;

  color: var(--color-accent);

}

.plan-check {

  position: absolute;

  top: 1rem;

  right: 1rem;

  width: 20px;

  height: 20px;

  border-radius: 50%;

  border: 2px solid var(--color-border);

  display: flex;

  align-items: center;

  justify-content: center;

  font-size: 0.7rem;

  color: transparent;

}

.plan-option.selected .plan-check {

  border-color: var(--color-accent);

  background: var(--color-accent);

  color: #0f1210;

}

.currency-note {

  font-size: 0.72rem;

  color: var(--color-text-muted);

  text-align: center;

  margin: -0.25rem 0 0;

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

.field input,

.field select,

.search-inp {

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

.phone-row {

  display: flex;

  gap: 0.5rem;

}

.dial-display {

  display: flex;

  align-items: center;

  gap: 0.35rem;

  padding: 0.65rem 0.75rem;

  border-radius: 8px;

  border: 1px solid var(--color-border);

  background: var(--color-bg);

  color: var(--color-text-muted);

  font-size: 0.9rem;

  min-width: 6.5rem;

  flex-shrink: 0;

  text-transform: none;

  letter-spacing: normal;

}

.radios {

  border: none;

  padding: 0;

  margin: 0;

}

.radio-row {

  display: flex;

  flex-wrap: wrap;

  gap: 0.75rem;

  text-transform: none;

  letter-spacing: normal;

  font-size: 0.9rem;

}

.radio-opt {

  display: flex;

  align-items: center;

  gap: 0.35rem;

  color: var(--color-text);

}

.trial-info {

  display: flex;

  gap: 0.875rem;

  padding: 0.875rem;

  background: rgba(196, 163, 90, 0.08);

  border: 1px solid rgba(196, 163, 90, 0.2);

  border-radius: 8px;

}

.trial-info p {

  margin: 0.35rem 0 0;

  font-size: 0.85rem;

  color: var(--color-text-muted);

  line-height: 1.55;

  text-transform: none;

  letter-spacing: normal;

}

.card-element {

  padding: 0.75rem;

  border-radius: 8px;

  border: 1px solid var(--color-border);

  background: var(--color-surface);

}

.stripe-note {

  font-size: 0.72rem;

  color: var(--color-text-muted);

  text-align: center;

  margin: -0.25rem 0 0;

}

.btn {

  font-weight: 600;

  padding: 0.7rem 1rem;

  border: none;

  border-radius: 8px;

  background: linear-gradient(135deg, var(--color-accent), #a6853a);

  color: #0f1210;

  cursor: pointer;

  flex: 1;

}

.btn:disabled {

  opacity: 0.55;

  cursor: not-allowed;

}

.step2-actions {

  display: flex;

  gap: 0.75rem;

}

.btn-back {

  font-size: 0.875rem;

  background: none;

  border: 1px solid var(--color-border);

  color: var(--color-text-muted);

  padding: 0.65rem 1rem;

  border-radius: 8px;

  cursor: pointer;

}

.alert.error {

  padding: 0.65rem 0.75rem;

  border-radius: 8px;

  color: #f0d0d0;

  background: rgba(180, 60, 60, 0.18);

  border: 1px solid rgba(180, 60, 60, 0.3);

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


