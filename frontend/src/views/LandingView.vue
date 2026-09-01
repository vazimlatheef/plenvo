<template>
  <div class="landing">
    <nav class="nav">
      <div class="nav-inner">
        <RouterLink to="/" class="logo" aria-label="Plenvo">
          <PlenvoLogo tag="span" variant="lockup" />
        </RouterLink>
        <div class="nav-links">
          <RouterLink to="/about" class="nav-link">About</RouterLink>
          <RouterLink to="/security" class="nav-link">Security</RouterLink>
          <RouterLink to="/support" class="nav-link">Support</RouterLink>
          <SiteAccountMenu v-if="signedIn" />
          <template v-else>
            <RouterLink to="/login" class="nav-link nav-link--auth">Sign in</RouterLink>
            <a href="#pricing" class="nav-cta" @click.prevent="scrollToPricing">Start for free</a>
          </template>
        </div>
      </div>
    </nav>

    <section class="hero">
      <div class="hero-inner">
        <div class="hero-copy">
          <h1 class="hero-title" :class="{ visible: show.title }">
            <template v-if="signedIn">
              Hello, {{ firstName }}.<br />
              <em class="accent">Capture anything. Ask anything.</em>
            </template>
            <template v-else>
              Type your day.<br />
              <em class="accent">Plenvo sorts the rest.</em>
            </template>
          </h1>

          <p class="hero-sub" :class="{ visible: show.sub }">
            <template v-if="signedIn">
              Projects, tasks, and what’s next — one workspace.
            </template>
            <template v-else>
              Paste notes. Get tasks, owners, and what’s next.
            </template>
          </p>

          <ul class="bullets">
            <li
              v-for="(b, i) in displayBullets"
              :key="b"
              class="bullet"
              :class="{ visible: show.bullets[i] }"
            >
              <span>{{ b }}</span>
            </li>
          </ul>

          <div class="hero-ctas" :class="{ visible: show.cta }">
            <template v-if="signedIn">
              <RouterLink v-if="user?.role === 'admin'" to="/app/admin/ai-terminal" class="btn-primary">
                Open Plenvo AI →
              </RouterLink>
              <RouterLink :to="workspaceTo" class="btn-ghost">Open workspace</RouterLink>
            </template>
            <template v-else>
              <a href="#pricing" class="btn-primary" @click.prevent="scrollToPricing">Start for free →</a>
            </template>
          </div>

          <div v-if="!signedIn" class="trust-bar" :class="{ visible: show.trust }">
            <span>✓ No charge for 14 days · No card required</span>
            <span class="sep">·</span>
            <span>✓ Cancel anytime</span>
            <span class="sep">·</span>
            <span>✓ GDPR compliant</span>
            <span class="sep">·</span>
            <span>✓ For managers, professionals, and students</span>
          </div>
        </div>

        <div id="demo" class="hero-demo" :class="{ visible: show.demo }">
          <p class="section-eyebrow">Plenvo AI</p>
          <h2 class="demo-title">Paste a note or ask what’s next.</h2>

          <div class="demo-tabs" role="tablist" aria-label="Audience">
            <button
              type="button"
              class="demo-tab"
              :class="{ 'demo-tab--active': demoAudience === 'team' }"
              @click="selectAudience('team')"
            >
              Team
            </button>
            <button
              type="button"
              class="demo-tab"
              :class="{ 'demo-tab--active': demoAudience === 'solo' }"
              @click="selectAudience('solo')"
            >
              Solo
            </button>
          </div>

          <div class="demo-tabs demo-tabs--mode" role="tablist" aria-label="Preview mode">
            <button
              type="button"
              class="demo-tab"
              :class="{ 'demo-tab--active': demoMode === 'capture' }"
              @click="selectMode('capture')"
            >
              Capture notes
            </button>
            <button
              type="button"
              class="demo-tab"
              :class="{ 'demo-tab--active': demoMode === 'ask' }"
              @click="selectMode('ask')"
            >
              Ask Brief
            </button>
          </div>

          <p class="demo-tagline">Assigned in seconds.</p>

          <div class="demo-window">
            <div class="demo-bar">
              <span class="dot r" /><span class="dot a" /><span class="dot g" />
              <span class="demo-bar-title">Plenvo · {{ demoMode === 'ask' ? 'AI Brief' : 'AI Capture' }}</span>
            </div>
            <div class="demo-body">
              <template v-if="demoMode === 'capture'">
                <div class="demo-col">
                  <p class="col-label">You paste</p>
                  <p class="demo-input">
                    "{{ displayedDemoText }}<span v-if="showDemoCursor" class="demo-cursor">|</span>"
                  </p>
                </div>
                <div class="demo-sep">→</div>
                <div class="demo-col">
                  <p class="col-label">Plenvo creates</p>
                  <div class="demo-tasks">
                    <div
                      v-for="(task, i) in demoTasks"
                      :key="task"
                      class="demo-task"
                      :class="{ visible: demoTasksVisible[i] }"
                    >
                      {{ task }}
                    </div>
                  </div>
                </div>
              </template>
              <template v-else>
                <div class="demo-col demo-col--full">
                  <p class="col-label">You ask</p>
                  <p class="demo-input">
                    "{{ displayedDemoText }}<span v-if="showDemoCursor" class="demo-cursor">|</span>"
                  </p>
                </div>
                <div class="demo-sep">→</div>
                <div class="demo-col demo-col--full">
                  <p class="col-label">Brief answers</p>
                  <div class="demo-briefing">
                    <p
                      v-for="(line, i) in demoBriefing"
                      :key="line.label"
                      :class="{ visible: demoBriefVisible[i] }"
                    >
                      <strong>{{ line.label }}:</strong> {{ line.text }}
                    </p>
                  </div>
                </div>
              </template>
            </div>
          </div>

          <div v-if="signedIn && user?.role === 'admin'" class="demo-cta-row">
            <RouterLink to="/app/admin/ai-terminal" class="btn-primary">Open Plenvo AI →</RouterLink>
          </div>
        </div>
      </div>
      <div class="hero-glow" />
    </section>

    <section v-if="showPublicPricing" id="pricing" class="pricing-section" ref="pricingRef">
      <div class="section-inner">
        <p class="section-eyebrow">Pricing</p>
        <p v-if="signedIn && billing?.on_trial" class="pricing-trial-note">
          You're on a free trial{{ trialDaysLeft != null ? ` — ${trialDaysLeft} day${trialDaysLeft === 1 ? '' : 's'} left` : '' }}.
          Pick a plan below{{ canManageBilling ? '' : ' (ask your admin to upgrade)' }}.
        </p>
        <h2 class="section-heading" :class="{ visible: show.pricing }">
          Simple. Transparent.<br />No per-seat surprises.
        </h2>
        <div class="pricing-grid" :class="{ visible: show.pricing }">
          <div v-for="plan in displayPlans" :key="plan.name" :class="['plan-card', plan.featured ? 'featured' : '']">
            <div class="plan-top">
              <span v-if="plan.featured" class="plan-badge">Most popular</span>
              <h3>{{ plan.name }}</h3>
              <div class="plan-price">
                <span class="plan-amount">{{ plan.price }}</span>
                <span class="plan-period" v-if="plan.price !== 'Custom'">/ month</span>
              </div>
              <p class="plan-members">{{ plan.members }}</p>
            </div>
            <ul class="plan-features">
              <li v-for="f in plan.features" :key="f">✓ {{ f }}</li>
            </ul>
            <RouterLink
              v-if="plan.cta === 'trial' && signedIn && canManageBilling"
              to="/app/account"
              :class="plan.featured ? 'btn-primary full' : 'btn-outline full'"
            >
              Choose plan →
            </RouterLink>
            <span v-else-if="plan.cta === 'trial' && signedIn" class="plan-note">Ask your admin to upgrade in Account</span>
            <RouterLink
              v-else-if="plan.cta === 'trial'"
              :to="plan.signupTo"
              :class="plan.featured ? 'btn-primary full' : 'btn-outline full'"
            >
              Start for free →
            </RouterLink>
            <a v-else href="mailto:hi@plenvo.io" :class="plan.featured ? 'btn-primary full' : 'btn-outline full'">
              Contact us →
            </a>
            <p v-if="plan.note" class="plan-note">{{ plan.note }}</p>
          </div>
        </div>
        <p class="currency-note">Prices shown in {{ currencyLabel }}</p>
      </div>
    </section>

    <section class="features" ref="featuresRef">
      <div class="section-inner">
        <p class="section-eyebrow">What's inside</p>
        <h2 class="section-heading" :class="{ visible: show.features }">
          Work, assigned.<br />Progress, visible.
        </h2>
        <div class="feature-grid">
          <div
            v-for="(f, i) in features"
            :key="f.title"
            class="feature-card"
            :class="{ visible: show.featureCards[i] }"
            :style="{ transitionDelay: `${i * 0.07}s` }"
          >
            <span class="f-icon">{{ f.icon }}</span>
            <h3>{{ f.title }}</h3>
            <p>{{ f.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="security-strip" ref="secRef">
      <p class="security-line" :class="{ visible: show.security }">
        Your data is encrypted, isolated, and never sold.
        <RouterLink to="/security" class="btn-ghost-sm">Security details →</RouterLink>
      </p>
    </section>

    <section v-if="signedIn && !showPublicPricing" class="final-cta" ref="ctaRefPaid">
      <div class="cta-inner" :class="{ visible: show.finalCta }">
        <h2>Welcome back, {{ firstName }}.</h2>
        <p>Your workspace is ready — capture something in Plenvo AI or jump straight to your board.</p>
        <div class="cta-row">
          <RouterLink v-if="user?.role === 'admin'" to="/app/admin/ai-terminal" class="btn-primary large">Open Plenvo AI →</RouterLink>
          <RouterLink :to="workspaceTo" class="btn-ghost large">Open workspace →</RouterLink>
        </div>
      </div>
    </section>

    <section v-else-if="signedIn && showPublicPricing" class="final-cta" ref="ctaRefTrial">
      <div class="cta-inner" :class="{ visible: show.finalCta }">
        <h2>Your trial is active.</h2>
        <p>Explore Plenvo AI and your workspace — choose a plan when you're ready.</p>
        <div class="cta-row">
          <RouterLink v-if="canManageBilling" to="/app/account" class="btn-primary large">Upgrade in Account →</RouterLink>
          <RouterLink v-if="user?.role === 'admin'" to="/app/admin/ai-terminal" class="btn-ghost large">Open Plenvo AI →</RouterLink>
          <RouterLink :to="workspaceTo" class="btn-ghost large">Open workspace →</RouterLink>
        </div>
      </div>
    </section>

    <footer class="footer">
      <div class="footer-inner">
        <div class="footer-brand">
          <span class="logo" aria-label="Plenvo">
            <PlenvoLogo tag="span" variant="lockup" compact />
          </span>
          <p>Notes become assigned work.</p>
        </div>
        <div class="footer-links">
          <RouterLink to="/about">About</RouterLink>
          <RouterLink to="/security">Security</RouterLink>
          <RouterLink to="/support">Support</RouterLink>
          <RouterLink to="/privacy">Privacy</RouterLink>
          <RouterLink to="/terms">Terms</RouterLink>
          <a href="mailto:hi@plenvo.io">hi@plenvo.io</a>
        </div>
      </div>
      <div class="footer-bottom">
        <span>© 2026 Plenvo. All rights reserved.</span>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'

import { apiJson } from '@/api/client'
import SiteAccountMenu from '@/components/SiteAccountMenu.vue'
import PlenvoLogo from '@/components/PlenvoLogo.vue'
import { appHomeRoute, loadSessionUser, user } from '@/composables/session'
import { useCurrency } from '@/composables/useCurrency'

const { currencyLabel, personalPrice, teamPrice, enterprisePrice } = useCurrency()

const signedIn = computed(() => !!user.value)
const firstName = computed(() => user.value?.first_name || 'there')
const workspaceTo = computed(() => appHomeRoute())

const billing = ref(null)
const billingLoaded = ref(false)

const hasPaidSubscription = computed(() => Boolean(billing.value?.has_paid_subscription))

const showPublicPricing = computed(() => {
  if (!signedIn.value) return true
  if (!billingLoaded.value) return false
  return !hasPaidSubscription.value
})

const canManageBilling = computed(() => Boolean(billing.value?.can_manage_billing))

const featuresRef = ref(null)
const secRef = ref(null)
const pricingRef = ref(null)
const ctaRefPaid = ref(null)
const ctaRefTrial = ref(null)

function scrollToPricing() {
  document.getElementById('pricing')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

const demoAudience = ref('team')
const demoMode = ref('capture')

const demoCopy = {
  team: {
    capture: {
      input:
        'Team standup Monday 9am. Finish API docs by Thursday — high priority. Assign homepage mockups to Alex by Friday.',
      tasks: [
        'Team standup · Monday 9am',
        'API docs · Thursday · High',
        'Homepage mockups · Friday · Alex',
      ],
      briefing: [],
    },
    ask: {
      input: 'How is my team doing this week? Who is carrying the most, and how can I improve performance?',
      tasks: [],
      briefing: [
        { label: 'Snapshot', text: '4 open tasks, 1 overdue.' },
        { label: 'Focus', text: 'API docs (Alex, due Thu) is highest priority.' },
        { label: 'Load', text: 'Alex is carrying the most; Maya has slack. Rebalance one item this week.' },
      ],
    },
  },
  solo: {
    capture: {
      input: 'Finish the client proposal by Wednesday. Renew passport next month. Read chapter 3 this weekend.',
      tasks: [
        'Client proposal · Wednesday',
        'Renew passport · Next month',
        'Leadership book · Chapter 3',
      ],
      briefing: [],
    },
    ask: {
      input: "What's next for me this week?",
      tasks: [],
      briefing: [
        { label: 'Snapshot', text: '3 open, none overdue.' },
        { label: 'Next', text: 'Client proposal due Wednesday.' },
        { label: 'Then', text: 'Chapter 3 this weekend — passport can wait.' },
      ],
    },
  },
}

const activeDemo = computed(() => demoCopy[demoAudience.value][demoMode.value])
const demoInputFull = computed(() => activeDemo.value.input)
const demoTasks = computed(() => activeDemo.value.tasks)
const demoBriefing = computed(() => activeDemo.value.briefing)

const displayedDemoText = ref('')
const showDemoCursor = ref(false)
const demoTasksVisible = ref([])
const demoBriefVisible = ref([])

let typeInterval = null
let revealTimeouts = []

function clearDemoTimers() {
  if (typeInterval) {
    clearInterval(typeInterval)
    typeInterval = null
  }
  revealTimeouts.forEach((id) => clearTimeout(id))
  revealTimeouts = []
}

function resetDemoAnimation() {
  clearDemoTimers()
  displayedDemoText.value = ''
  showDemoCursor.value = false
  demoTasksVisible.value = demoTasks.value.map(() => false)
  demoBriefVisible.value = demoBriefing.value.map(() => false)
}

function startDemoAnimation() {
  resetDemoAnimation()
  showDemoCursor.value = true
  let i = 0
  const full = demoInputFull.value
  typeInterval = setInterval(() => {
    if (i < full.length) {
      displayedDemoText.value += full[i]
      i++
      return
    }
    clearInterval(typeInterval)
    typeInterval = null
    showDemoCursor.value = false
    const afterType = setTimeout(() => {
      if (demoMode.value === 'capture') {
        demoTasks.value.forEach((_, idx) => {
          revealTimeouts.push(
            setTimeout(() => {
              demoTasksVisible.value[idx] = true
            }, idx * 280),
          )
        })
      } else {
        demoBriefing.value.forEach((_, idx) => {
          revealTimeouts.push(
            setTimeout(() => {
              demoBriefVisible.value[idx] = true
            }, idx * 280),
          )
        })
      }
    }, 400)
    revealTimeouts.push(afterType)
  }, 22)
}

function selectAudience(id) {
  if (demoAudience.value === id) return
  demoAudience.value = id
  startDemoAnimation()
}

function selectMode(mode) {
  if (demoMode.value === mode) return
  demoMode.value = mode
  startDemoAnimation()
}

const bullets = computed(() => [
  '✓ Projects, tasks, and what’s next — one workspace',
  '✓ Boards, calendar, and priorities — yours or the team’s',
  `✓ From ${personalPrice.value}/mo · 14-day trial · No card`,
])

const signedInBullets = [
  '✓ Plenvo AI — capture notes or ask what’s next',
  '✓ Paste notes, assign work, or ask how work is tracking',
  '✓ Private. Encrypted. Yours.',
]

const displayBullets = computed(() => (signedIn.value ? signedInBullets : bullets.value))

const trialDaysLeft = computed(() => {
  const iso = billing.value?.trial_ends_at
  if (!iso) return null
  const end = new Date(iso)
  if (Number.isNaN(end.getTime())) return null
  const days = Math.ceil((end.getTime() - Date.now()) / (1000 * 60 * 60 * 24))
  return Math.max(0, days)
})

async function loadBilling() {
  if (!signedIn.value) {
    billing.value = null
    billingLoaded.value = true
    return
  }
  billingLoaded.value = false
  try {
    billing.value = await apiJson('/api/v1/billing/account')
  } catch {
    billing.value = null
  } finally {
    billingLoaded.value = true
  }
}

function revealPricingSection() {
  if (!showPublicPricing.value) {
    show.pricing = false
    return
  }
  nextTick(() => {
    const el = pricingRef.value
    if (!el) return
    const rect = el.getBoundingClientRect()
    if (rect.top < window.innerHeight && rect.bottom > 0) {
      show.pricing = true
      return
    }
    observe(el, 'pricing')
  })
}

watch(showPublicPricing, () => {
  revealPricingSection()
})

watch(signedIn, async () => {
  await loadBilling()
  revealPricingSection()
})

const features = [
  {
    icon: '⚡',
    title: 'Plenvo AI',
    desc: 'Paste notes or ask what’s next. Tasks, owners, and a live brief appear from context.',
  },
  {
    icon: '📋',
    title: 'Tasks & projects',
    desc: 'Boards, calendar, and priorities in one workspace — yours or the team’s.',
  },
  {
    icon: '👥',
    title: 'Team & training',
    desc: 'Assign work and courses without forcing everyone into another account. See who is done.',
  },
]

const displayPlans = computed(() => [
  {
    name: 'Personal',
    id: 'personal',
    signupTo: '/signup?plan=personal',
    price: personalPrice.value,
    members: '1 person, unlimited everything',
    features: [
      'Unlimited projects & tasks',
      'Plenvo AI',
      'Calendar view',
      'Smart task prioritization',
      'Mobile ready',
    ],
    cta: 'trial',
    featured: false,
  },
  {
    name: 'Team',
    id: 'team',
    signupTo: '/signup?plan=team',
    price: teamPrice.value,
    members: 'Up to 5 team members',
    features: [
      'Everything in Personal',
      'Up to 5 team members',
      'Team task assignment',
      'Training management',
      'Member workload view',
      'Performance summary',
      'Priority support',
    ],
    cta: 'trial',
    featured: true,
  },
  {
    name: 'Enterprise',
    id: 'enterprise',
    signupTo: '/signup?plan=enterprise',
    price: enterprisePrice.value,
    members: 'Unlimited team members',
    features: [
      'Everything in Team',
      'Unlimited team members',
      'Team priority insights',
      'Dedicated support',
    ],
    cta: 'trial',
    featured: false,
  },
])

const show = reactive({
  title: false,
  sub: false,
  bullets: [false, false, false],
  cta: false,
  trust: false,
  demo: false,
  features: false,
  featureCards: features.map(() => false),
  security: false,
  pricing: false,
  finalCta: false,
})

function observe(el, key, cardKey = null, count = 0) {
  if (!el) return
  const obs = new IntersectionObserver(
    ([e]) => {
      if (e.isIntersecting) {
        show[key] = true
        if (cardKey) {
          for (let i = 0; i < count; i++) {
            setTimeout(() => {
              show[cardKey][i] = true
            }, i * 90)
          }
        }
        obs.disconnect()
      }
    },
    { threshold: 0.1 },
  )
  obs.observe(el)
}

onMounted(async () => {
  await loadSessionUser()
  await loadBilling()

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const delays = reduceMotion ? [0, 0] : [80, 220]
  setTimeout(() => {
    show.title = true
  }, delays[0])
  setTimeout(() => {
    show.sub = true
  }, delays[1])
  for (let i = 0; i < displayBullets.value.length; i++) {
    setTimeout(() => {
      show.bullets[i] = true
    }, reduceMotion ? 0 : 420 + i * 120)
  }
  const base = reduceMotion ? 0 : 420 + displayBullets.value.length * 120
  setTimeout(() => {
    show.cta = true
  }, base + 80)
  setTimeout(() => {
    show.trust = true
  }, base + 180)
  setTimeout(() => {
    show.demo = true
    startDemoAnimation()
  }, reduceMotion ? 0 : 280)

  observe(featuresRef.value, 'features', 'featureCards', features.length)
  observe(secRef.value, 'security')
  revealPricingSection()
  const ctaEl = ctaRefPaid.value || ctaRefTrial.value
  if (ctaEl) observe(ctaEl, 'finalCta')
})

onBeforeUnmount(() => {
  clearDemoTimers()
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Instrument+Serif:ital@0;1&display=swap');

.landing {
  background: var(--color-bg);
  color: var(--color-text);
  font-family: 'Inter', sans-serif;
  overflow-x: hidden;
}

.nav {
  position: sticky;
  top: 0;
  z-index: 50;
  border-bottom: 1px solid var(--color-border);
  background: rgba(15, 18, 16, 0.95);
  backdrop-filter: blur(20px);
}
.nav-inner {
  max-width: 1160px;
  margin: 0 auto;
  padding: 0.9rem 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.logo {
  display: inline-flex;
  align-items: center;
  text-decoration: none;
}
.logo:hover {
  text-decoration: none;
}
.nav-links {
  display: flex;
  align-items: center;
  gap: 1.75rem;
}
.nav-link {
  font-size: 0.85rem;
  font-weight: 400;
  color: var(--color-text-muted);
  text-decoration: none;
  transition: color 0.2s;
}
.nav-link:hover {
  color: var(--color-text);
  text-decoration: none;
}
.nav-cta {
  font-size: 0.85rem;
  font-weight: 600;
  padding: 0.5rem 1.25rem;
  border-radius: 999px;
  background: var(--color-accent);
  color: #0f1210;
  text-decoration: none;
  transition: filter 0.2s, transform 0.15s;
}
.nav-cta:hover {
  filter: brightness(1.1);
  transform: translateY(-1px);
  text-decoration: none;
}

.hero {
  padding: 4.5rem 1.5rem 3.5rem;
  position: relative;
  overflow: hidden;
}
.hero-glow {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(ellipse 45% 50% at 12% 0%, rgba(196, 163, 90, 0.14), transparent),
    radial-gradient(ellipse 40% 50% at 92% 40%, rgba(196, 163, 90, 0.07), transparent);
}
.hero-inner {
  max-width: 1160px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: minmax(0, 0.95fr) minmax(0, 1.05fr);
  gap: 3rem;
  align-items: center;
  position: relative;
  z-index: 1;
}
.hero-copy {
  text-align: left;
}

.hero-title,
.hero-sub,
.bullet,
.hero-ctas,
.trust-bar,
.hero-demo {
  opacity: 0;
  transform: translateY(16px);
  transition: opacity 0.65s ease, transform 0.65s ease;
}
.hero-title.visible,
.hero-sub.visible,
.bullet.visible,
.hero-ctas.visible,
.trust-bar.visible,
.hero-demo.visible {
  opacity: 1;
  transform: translateY(0);
}

@media (prefers-reduced-motion: reduce) {
  .hero-title,
  .hero-sub,
  .bullet,
  .hero-ctas,
  .trust-bar,
  .hero-demo,
  .section-heading,
  .feature-card,
  .security-line,
  .pricing-grid,
  .cta-inner,
  .demo-task,
  .demo-briefing p {
    opacity: 1;
    transform: none;
    transition: none;
  }
}

.hero-title {
  font-family: 'Instrument Serif', serif;
  font-size: clamp(2.6rem, 5vw, 4.2rem);
  font-weight: 400;
  line-height: 1.08;
  margin: 0 0 1rem;
  color: var(--color-text);
  letter-spacing: -0.01em;
}
.accent {
  color: var(--color-accent);
  font-style: italic;
}
.hero-sub {
  font-size: 1.05rem;
  font-weight: 300;
  color: var(--color-text-muted);
  max-width: 440px;
  margin: 0 0 1.75rem;
  line-height: 1.7;
}

.bullets {
  list-style: none;
  padding: 0;
  margin: 0 0 1.75rem;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.5rem;
}
.bullet {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.93rem;
  color: var(--color-text);
}

.hero-ctas {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 1rem;
  margin-bottom: 1.4rem;
  flex-wrap: wrap;
}

.trust-bar {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 0.55rem;
  flex-wrap: wrap;
  font-size: 0.75rem;
  color: var(--color-text-muted);
}
.sep {
  color: var(--color-border);
}

.btn-primary {
  display: inline-block;
  font-family: 'Inter', sans-serif;
  font-weight: 600;
  font-size: 0.9rem;
  padding: 0.75rem 1.75rem;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--color-accent), #a6853a);
  color: #0f1210;
  text-decoration: none;
  border: none;
  cursor: pointer;
  transition: filter 0.2s, transform 0.2s;
}
.btn-primary:hover {
  filter: brightness(1.08);
  transform: translateY(-2px);
  text-decoration: none;
}
.btn-primary.full {
  display: block;
  text-align: center;
  width: 100%;
}
.btn-primary.large {
  padding: 0.9rem 2.25rem;
  font-size: 1rem;
}
.btn-ghost.large {
  padding: 0.9rem 2.25rem;
  font-size: 1rem;
}

.btn-ghost {
  display: inline-block;
  font-family: 'Inter', sans-serif;
  font-weight: 500;
  font-size: 0.9rem;
  padding: 0.75rem 1.5rem;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
  text-decoration: none;
  transition: border-color 0.2s, color 0.2s;
  cursor: pointer;
  background: none;
}
.btn-ghost:hover {
  border-color: var(--color-accent);
  color: var(--color-text);
  text-decoration: none;
}

.btn-ghost-sm {
  display: inline-block;
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--color-accent);
  text-decoration: none;
  border-bottom: 1px solid rgba(196, 163, 90, 0.4);
  padding-bottom: 1px;
  margin-left: 0.5rem;
  transition: border-color 0.2s;
}
.btn-ghost-sm:hover {
  border-color: var(--color-accent);
  text-decoration: none;
}

.btn-outline {
  display: inline-block;
  font-family: 'Inter', sans-serif;
  font-weight: 600;
  font-size: 0.9rem;
  padding: 0.75rem 1.75rem;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  color: var(--color-text);
  text-decoration: none;
  transition: border-color 0.2s, color 0.2s;
  text-align: center;
  cursor: pointer;
  background: none;
}
.btn-outline:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
  text-decoration: none;
}
.btn-outline.full {
  display: block;
  width: 100%;
}

.section-inner {
  max-width: 1160px;
  margin: 0 auto;
}
.section-eyebrow {
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: var(--color-accent);
  margin: 0 0 0.6rem;
  font-weight: 600;
}
.section-heading {
  font-family: 'Instrument Serif', serif;
  font-size: clamp(2rem, 3.5vw, 2.9rem);
  font-weight: 400;
  margin: 0 0 2.25rem;
  line-height: 1.18;
  opacity: 0;
  transform: translateY(18px);
  transition: opacity 0.65s ease, transform 0.65s ease;
}
.section-heading.visible {
  opacity: 1;
  transform: translateY(0);
}

.hero-demo {
  min-width: 0;
}
.demo-title {
  font-family: 'Instrument Serif', serif;
  font-size: clamp(1.35rem, 2.2vw, 1.7rem);
  font-weight: 400;
  margin: 0.15rem 0 0.85rem;
  line-height: 1.25;
}
.demo-tabs {
  display: inline-flex;
  gap: 0.35rem;
  margin: 0 0.5rem 0.65rem 0;
  padding: 0.2rem;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.2);
}
.demo-tab {
  font-family: 'Inter', sans-serif;
  font-size: 0.75rem;
  font-weight: 500;
  padding: 0.35rem 0.75rem;
  border: none;
  border-radius: 999px;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
}
.demo-tab--active {
  background: rgba(196, 163, 90, 0.16);
  color: var(--color-text);
}
.demo-tagline {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: var(--color-accent);
  margin: 0 0 0.85rem;
}
.demo-briefing p {
  margin: 0 0 0.5rem;
  font-size: 0.82rem;
  line-height: 1.5;
  color: var(--color-text-muted);
  opacity: 0;
  transform: translateY(10px);
  transition: opacity 0.45s ease, transform 0.45s ease;
}
.demo-briefing p.visible {
  opacity: 1;
  transform: translateY(0);
}
.demo-col--full {
  min-width: 0;
}
.demo-window {
  background: #070a08;
  border: 1px solid var(--color-border);
  border-radius: 14px;
  overflow: hidden;
}
.demo-bar {
  background: var(--color-surface);
  padding: 0.55rem 0.85rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  border-bottom: 1px solid var(--color-border);
}
.dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
}
.dot.r {
  background: #ff5f57;
}
.dot.a {
  background: #ffbd2e;
}
.dot.g {
  background: #28c840;
}
.demo-bar-title {
  margin-left: 0.4rem;
  font-size: 0.72rem;
  color: var(--color-text-muted);
  font-family: 'Inter', sans-serif;
}
.demo-body {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 1.1rem;
  padding: 1.15rem;
  align-items: start;
}
.col-label {
  font-size: 0.62rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--color-text-muted);
  margin: 0 0 0.55rem;
  font-weight: 600;
}
.demo-input {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  font-style: italic;
  border-left: 2px solid var(--color-border);
  padding-left: 0.7rem;
  margin: 0;
  line-height: 1.6;
  min-height: 4.5rem;
}
.demo-cursor {
  display: inline-block;
  color: var(--color-accent);
  font-style: normal;
  animation: blink 1s step-end infinite;
}
@keyframes blink {
  50% {
    opacity: 0;
  }
}
.demo-sep {
  font-size: 1.4rem;
  color: var(--color-accent);
  display: flex;
  align-items: center;
  padding-top: 1.1rem;
  opacity: 0.6;
}
.demo-tasks {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.demo-task {
  font-size: 0.78rem;
  background: var(--color-surface);
  padding: 0.45rem 0.7rem;
  border-radius: 7px;
  color: var(--color-text);
  opacity: 0;
  transform: translateY(12px);
  transition: opacity 0.5s ease, transform 0.5s ease;
}
.demo-task.visible {
  opacity: 1;
  transform: translateY(0);
}
.demo-cta-row {
  margin-top: 1rem;
}

.cta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: center;
}

.features {
  padding: 3.5rem 1.5rem 3rem;
}
.feature-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1.25rem;
}
.feature-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 1.4rem;
  opacity: 0;
  transform: translateY(22px);
  transition: opacity 0.5s ease, transform 0.5s ease, border-color 0.2s;
}
.feature-card.visible {
  opacity: 1;
  transform: translateY(0);
}
.feature-card:hover {
  border-color: rgba(196, 163, 90, 0.45);
}
.f-icon {
  font-size: 1.2rem;
  display: block;
  margin-bottom: 0.65rem;
}
.feature-card h3 {
  font-family: 'Instrument Serif', serif;
  font-size: 1.05rem;
  margin: 0 0 0.4rem;
  font-weight: 400;
  color: var(--color-text);
}
.feature-card p {
  font-size: 0.85rem;
  color: var(--color-text-muted);
  margin: 0;
  line-height: 1.65;
}

.security-strip {
  padding: 1.35rem 1.5rem;
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg-elevated);
}
.security-line {
  max-width: 1160px;
  margin: 0 auto;
  font-size: 0.88rem;
  color: var(--color-text-muted);
  opacity: 0;
  transform: translateY(10px);
  transition: opacity 0.5s ease, transform 0.5s ease;
}
.security-line.visible {
  opacity: 1;
  transform: translateY(0);
}

.pricing-section {
  padding: 4rem 1.5rem 3.5rem;
  scroll-margin-top: 4.5rem;
}
.pricing-trial-note {
  text-align: center;
  font-size: 0.9rem;
  color: var(--color-accent);
  margin: -0.5rem auto 1.5rem;
  max-width: 520px;
  line-height: 1.55;
}
.pricing-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.25rem;
  opacity: 0;
  transform: translateY(20px);
  transition: opacity 0.65s ease, transform 0.65s ease;
}
.pricing-grid.visible {
  opacity: 1;
  transform: translateY(0);
}
.plan-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: calc(var(--radius) + 4px);
  padding: 2rem;
  display: flex;
  flex-direction: column;
}
.plan-card.featured {
  border-color: rgba(196, 163, 90, 0.5);
}
.plan-top {
  margin-bottom: 1.5rem;
}
.plan-badge {
  display: inline-block;
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  padding: 0.25rem 0.6rem;
  border-radius: 999px;
  background: rgba(196, 163, 90, 0.15);
  color: var(--color-accent);
  border: 1px solid rgba(196, 163, 90, 0.3);
  margin-bottom: 0.75rem;
}
.plan-top h3 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 0.75rem;
  color: var(--color-text);
}
.plan-price {
  display: flex;
  align-items: baseline;
  gap: 0.25rem;
  margin-bottom: 0.25rem;
}
.plan-amount {
  font-family: 'Instrument Serif', serif;
  font-size: 2.8rem;
  color: var(--color-accent);
  line-height: 1;
}
.plan-period {
  font-size: 0.9rem;
  color: var(--color-text-muted);
}
.plan-members {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  margin: 0;
}
.plan-features {
  list-style: none;
  padding: 0;
  margin: 0 0 1.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  flex: 1;
}
.plan-features li {
  font-size: 0.85rem;
  color: var(--color-text);
}
.plan-note {
  text-align: center;
  font-size: 0.72rem;
  color: var(--color-text-muted);
  margin: 0.75rem 0 0;
}
.currency-note {
  text-align: center;
  font-size: 0.75rem;
  color: var(--color-text-muted);
  margin-top: 1.25rem;
}

.final-cta {
  padding: 4rem 1.5rem;
  background: var(--color-bg-elevated);
  border-top: 1px solid var(--color-border);
}
.cta-inner {
  max-width: 560px;
  margin: 0 auto;
  text-align: center;
  opacity: 0;
  transform: translateY(20px);
  transition: opacity 0.65s ease, transform 0.65s ease;
}
.cta-inner.visible {
  opacity: 1;
  transform: translateY(0);
}
.cta-inner h2 {
  font-family: 'Instrument Serif', serif;
  font-size: clamp(2rem, 4vw, 3rem);
  font-weight: 400;
  margin: 0 0 0.75rem;
}
.cta-inner p {
  font-size: 0.95rem;
  color: var(--color-text-muted);
  margin-bottom: 2rem;
}
.cta-note {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  margin-top: 1rem;
  margin-bottom: 0;
}

.footer {
  border-top: 1px solid var(--color-border);
  padding: 3rem 1.5rem 2rem;
}
.footer-inner {
  max-width: 1160px;
  margin: 0 auto 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 2rem;
  flex-wrap: wrap;
}
.footer-brand p {
  font-size: 0.82rem;
  color: var(--color-text-muted);
  margin: 0.35rem 0 0;
}
.footer-links {
  display: flex;
  gap: 1.5rem;
}
.footer-links a {
  font-size: 0.85rem;
  color: var(--color-text-muted);
  text-decoration: none;
  transition: color 0.2s;
}
.footer-links a:hover {
  color: var(--color-text);
  text-decoration: none;
}
.footer-bottom {
  max-width: 1160px;
  margin: 0 auto;
  padding-top: 1.5rem;
  border-top: 1px solid var(--color-border);
  font-size: 0.78rem;
  color: var(--color-text-muted);
}

@media (max-width: 980px) {
  .hero-inner {
    grid-template-columns: 1fr;
    gap: 2.25rem;
  }
  .hero-copy {
    text-align: center;
  }
  .hero-sub,
  .bullets,
  .hero-ctas,
  .trust-bar {
    margin-left: auto;
    margin-right: auto;
    justify-content: center;
    align-items: center;
    text-align: center;
  }
  .feature-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .pricing-grid {
    grid-template-columns: 1fr;
    max-width: 440px;
    margin: 0 auto;
  }
  .footer-inner {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 640px) {
  .hero {
    padding: 3.5rem 1rem 2.5rem;
  }
  .demo-body {
    grid-template-columns: 1fr;
  }
  .demo-sep {
    display: none;
  }
  .hero-ctas {
    flex-direction: column;
  }
  .nav-links .nav-link:not(.nav-link--auth):not(.nav-cta) {
    display: none;
  }
  .nav-link--auth {
    display: inline-flex !important;
  }
}
</style>
