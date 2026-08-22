<template>

  <div class="landing">



    <!-- NAV -->

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

            <RouterLink to="/login" class="nav-link">Sign in</RouterLink>

            <RouterLink to="/signup" class="nav-cta">Start for free</RouterLink>

          </template>

        </div>

      </div>

    </nav>



    <!-- HERO -->

    <section class="hero">

      <div class="hero-inner">

        <h1 class="hero-title" :class="{ visible: show.title }">

          <template v-if="signedIn">

            Hello, {{ firstName }}.<br />

            <em class="accent">Capture anything. Ask anything.</em>

          </template>

          <template v-else>

            Say it.<br />

            <em class="accent">Plenvo sorts it.</em>

          </template>

        </h1>



        <p class="hero-sub" :class="{ visible: show.sub }">

          <template v-if="signedIn">

            Paste notes, assign work, or ask how the team is tracking — Plenvo AI reads context and keeps your board current.

          </template>

          <template v-else>

            Meeting notes, personal tasks, team assignments — organized the moment you write them.

          </template>

        </p>



        <ul class="bullets">

          <li v-for="(b, i) in displayBullets" :key="b" class="bullet" :class="{ visible: show.bullets[i] }">

            <span>{{ b }}</span>

          </li>

        </ul>



        <div class="hero-ctas" :class="{ visible: show.cta }">

          <template v-if="signedIn">

            <RouterLink v-if="user?.role === 'admin'" to="/app/admin/ai-terminal" class="btn-primary">Open Plenvo AI →</RouterLink>

            <RouterLink :to="workspaceTo" class="btn-ghost">Open workspace</RouterLink>

          </template>

          <template v-else>

            <RouterLink to="/signup" class="btn-primary">Start for free — takes 60 seconds →</RouterLink>

            <a href="#demo" class="btn-ghost" @click.prevent="scrollToDemo">See Plenvo AI in action ↓</a>

          </template>

        </div>



        <div v-if="!signedIn" class="trust-bar" :class="{ visible: show.trust }">

          <span>✓ No charge for 14 days · No card required</span>

          <span class="sep">·</span>

          <span>✓ Cancel anytime</span>

          <span class="sep">·</span>

          <span>✓ GDPR compliant</span>

          <span class="sep">·</span>

          <span>✓ Stop losing tasks in notes, chats & your head</span>

        </div>

      </div>

      <div class="hero-glow" />

    </section>



    <!-- DEMO -->

    <section class="demo-section" id="demo" ref="demoRef">

      <div class="demo-inner" :class="{ visible: show.demo }">

        <p class="section-eyebrow">Plenvo AI</p>

        <h2 class="demo-title">Watch it read your day.<br />Then try it yourself.</h2>

        <div class="demo-window">

          <div class="demo-bar">

            <span class="dot r"/><span class="dot a"/><span class="dot g"/>

            <span class="demo-bar-title">Plenvo · AI Capture</span>

          </div>

          <div class="demo-body">

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

          </div>

        </div>

        <div v-if="signedIn && user?.role === 'admin'" class="demo-cta-row">

          <RouterLink to="/app/admin/ai-terminal" class="btn-primary">Open Plenvo AI →</RouterLink>

        </div>

      </div>

    </section>



    <!-- FEATURES -->

    <section class="features" ref="featuresRef">

      <div class="section-inner">

        <p class="section-eyebrow">What's inside</p>

        <h2 class="section-heading" :class="{ visible: show.features }">

          Everything you juggle.<br />Finally in one place.

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



    <!-- SECURITY -->

    <section class="security-section" ref="secRef">

      <div class="section-inner">

        <div class="security-grid" :class="{ visible: show.security }">

          <div class="sec-left">

            <p class="section-eyebrow">Enterprise security</p>

            <h2 class="sec-heading">Your data is yours.<br />Full stop.</h2>

            <p class="sec-body">

              Plenvo is built with the same security principles used in defence and space

              infrastructure. Your tasks, goals and projects are encrypted, isolated, and never shared.

            </p>

            <RouterLink to="/security" class="btn-ghost-sm">View security details →</RouterLink>

          </div>

          <div class="sec-right">

            <div class="sec-badge" v-for="s in securityItems" :key="s.title">

              <span class="sec-icon">{{ s.icon }}</span>

              <div>

                <h4>{{ s.title }}</h4>

                <p>{{ s.desc }}</p>

              </div>

            </div>

          </div>

        </div>

      </div>

    </section>



    <!-- PRICING -->

    <section v-if="showPublicPricing" class="pricing-section" ref="pricingRef">

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
              v-if="plan.cta === 'trial' && pricingPlanCta"
              :to="pricingPlanCta.to"
              :class="plan.featured ? 'btn-primary full' : 'btn-outline full'"
            >
              {{ pricingPlanCta.label }}
            </RouterLink>

            <span v-else-if="plan.cta === 'trial' && signedIn" class="plan-note">Ask your admin to upgrade in Account</span>

            <RouterLink v-else-if="plan.cta === 'trial'" to="/signup" :class="plan.featured ? 'btn-primary full' : 'btn-outline full'">
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



    <!-- FINAL CTA -->

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

    <section v-else class="final-cta" ref="ctaRefSignup">

      <div class="cta-inner" :class="{ visible: show.finalCta }">

        <h2>Start today. Free for 14 days.</h2>

        <p>

          No payment friction. Just sign up and start organising your work, life and team in one place.

        </p>

        <RouterLink to="/signup" class="btn-primary large">Start for free →</RouterLink>

        <p class="cta-note">Cancel anytime · {{ symbol }}0 today · Takes 60 seconds</p>

      </div>

    </section>



    <!-- FOOTER -->

    <footer class="footer">

      <div class="footer-inner">

        <div class="footer-brand">

          <span class="logo" aria-label="Plenvo">
            <PlenvoLogo tag="span" variant="lockup" compact />
          </span>

          <p>Work. Life. Team. All in one place.</p>

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

import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'

import { apiJson } from '@/api/client'
import SiteAccountMenu from '@/components/SiteAccountMenu.vue'
import PlenvoLogo from '@/components/PlenvoLogo.vue'
import { appHomeRoute, loadSessionUser, user } from '@/composables/session'
import { useCurrency } from '@/composables/useCurrency'



const { symbol, currencyLabel, personalPrice, teamPrice, enterprisePrice } = useCurrency()

const signedIn = computed(() => !!user.value)
const firstName = computed(() => user.value?.first_name || 'there')
const workspaceTo = computed(() => appHomeRoute())

const billing = ref(null)
const billingLoaded = ref(false)

const hasPaidSubscription = computed(() => Boolean(billing.value?.has_paid_subscription))

/** Show public pricing: logged out, on trial, or trial expired — hide for active paid subs. */
const showPublicPricing = computed(() => {
  if (!signedIn.value) return true
  if (!billingLoaded.value) return false
  return !hasPaidSubscription.value
})

const canManageBilling = computed(() => Boolean(billing.value?.can_manage_billing))

const pricingPlanCta = computed(() => {
  if (!signedIn.value) return { to: '/signup', label: 'Start for free →' }
  if (canManageBilling.value) return { to: '/app/account', label: 'Choose plan →' }
  return null
})



const demoRef = ref(null)

const featuresRef = ref(null)

const secRef = ref(null)

const pricingRef = ref(null)

const ctaRefPaid = ref(null)

const ctaRefTrial = ref(null)

const ctaRefSignup = ref(null)



const demoInputFull =

  'Team standup at 9am Monday. Finish the API docs by Thursday — high priority. Call mum this weekend. Side project: update landing page copy. Gym: leg day Tuesday 6pm.'



const demoTasks = [

  '📅 Team standup · Monday 9am · Recurring',

  '📋 API docs · Thursday · High',

  '👨‍👩‍👧 Call mum · This weekend · Personal',

  '🚀 Update landing page · Side project · Medium',

  '💪 Leg day · Tuesday 6pm · Health',

]



const displayedDemoText = ref('')

const showDemoCursor = ref(false)

const demoTasksVisible = ref(demoTasks.map(() => false))

let demoAnimationStarted = false



const bullets = computed(() => [

  '✓ Paste your day in words — Plenvo creates your tasks',

  '✓ Work, life and team — all in one place',

  '✓ AI that reads context, not just keywords',

  `✓ From ${personalPrice.value}/mo · Free for 14 days · No card required`,

  '✓ Your data. Private. Encrypted. Always yours.',

])

const signedInBullets = [

  '✓ Plenvo AI — capture notes or ask how work is tracking',

  '✓ Projects, tasks, and team — one workspace',

  '✓ Work, study, and life on the same board',

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
    show.pricing = true
    const el = pricingRef.value
    if (!el) return
    const rect = el.getBoundingClientRect()
    if (rect.top >= window.innerHeight || rect.bottom <= 0) {
      observe(el, 'pricing')
    }
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

    desc: 'Paste notes, assign work, or ask what’s next. Plenvo reads context — then tasks, people, and a live briefing appear instantly.',

  },

  {

    icon: '📋',

    title: 'Smart Task Management',

    desc: 'Work tasks, personal goals, team projects. One dashboard. Priority-sorted. Always clear.',

  },

  {

    icon: '📅',

    title: 'Calendar & Scheduling',

    desc: 'Say "weekly meeting Monday 10am" and it appears in your calendar. No clicking through forms.',

  },

  {

    icon: '👥',

    title: 'Team Collaboration',

    desc: "Assign tasks, track progress, manage training. See your team's workload at a glance.",

  },

  {

    icon: '🧠',

    title: 'AI Priority Engine',

    desc: 'Not sure what to tackle next? Plenvo recommends your most important task based on deadlines and context.',

  },

  {

    icon: '🔒',

    title: 'Private & Secure',

    desc: 'Your data is encrypted and completely isolated. We never sell your data. Ever.',

  },

]



const securityItems = [

  { icon: '🔐', title: 'End-to-end encryption', desc: 'All data encrypted in transit and at rest.' },

  { icon: '🏢', title: 'Complete data isolation', desc: 'Your company data is never mixed with others. Guaranteed.' },

  { icon: '🇪🇺', title: 'GDPR compliant', desc: 'Built for European data regulations from day one.' },

  { icon: '🔗', title: 'REST API', desc: 'Integrate with your existing company systems.' },

]



const displayPlans = computed(() => [

  {

    name: 'Personal',

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

    price: teamPrice.value,

    members: 'Up to 5 people',

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

    price: enterprisePrice.value,

    members: '5+ people, unlimited',

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

  title: false, sub: false,

  bullets: [false, false, false, false, false],

  cta: false, trust: false,

  demo: false, features: false,

  featureCards: features.map(() => false),

  security: false, pricing: false, finalCta: false,

})



function startDemoAnimation() {

  if (demoAnimationStarted) return

  demoAnimationStarted = true

  showDemoCursor.value = true

  let i = 0

  const typeInterval = setInterval(() => {

    if (i < demoInputFull.length) {

      displayedDemoText.value += demoInputFull[i]

      i++

    } else {

      clearInterval(typeInterval)

      showDemoCursor.value = false

      setTimeout(() => {

        demoTasks.forEach((_, idx) => {

          setTimeout(() => {

            demoTasksVisible.value[idx] = true

          }, idx * 300)

        })

      }, 500)

    }

  }, 30)

}



function observe(el, key, cardKey = null, count = 0) {

  if (!el) return

  const obs = new IntersectionObserver(([e]) => {

    if (e.isIntersecting) {

      show[key] = true

      if (cardKey) {

        for (let i = 0; i < count; i++) {

          setTimeout(() => { show[cardKey][i] = true }, i * 90)

        }

      }

      obs.disconnect()

    }

  }, { threshold: 0.1 })

  obs.observe(el)

}



function observeDemo(el) {

  if (!el) return

  const obs = new IntersectionObserver(([e]) => {

    if (e.isIntersecting) {

      show.demo = true

      startDemoAnimation()

      obs.disconnect()

    }

  }, { threshold: 0.1 })

  obs.observe(el)

}



function scrollToDemo() {

  document.getElementById('demo')?.scrollIntoView({ behavior: 'smooth' })

}



onMounted(async () => {

  await loadSessionUser()

  await loadBilling()

  const delays = [100, 260]

  const keys = ['title', 'sub']

  keys.forEach((k, i) => setTimeout(() => { show[k] = true }, delays[i]))

  for (let i = 0; i < displayBullets.value.length; i++) {

    setTimeout(() => { show.bullets[i] = true }, 560 + i * 140)

  }

  const base = 560 + displayBullets.value.length * 140

  setTimeout(() => { show.cta = true }, base + 100)

  setTimeout(() => { show.trust = true }, base + 250)



  observeDemo(demoRef.value)

  observe(featuresRef.value, 'features', 'featureCards', features.length)

  observe(secRef.value, 'security')

  revealPricingSection()

  const ctaEl = ctaRefPaid.value || ctaRefTrial.value || ctaRefSignup.value

  if (ctaEl) observe(ctaEl, 'finalCta')

})

</script>



<style scoped>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Instrument+Serif:ital@0;1&display=swap');



/* BASE */

.landing {

  background: var(--color-bg);

  color: var(--color-text);

  font-family: 'Inter', sans-serif;

  overflow-x: hidden;

}



/* NAV */

.nav {

  position: sticky; top: 0; z-index: 50;

  border-bottom: 1px solid var(--color-border);

  background: rgba(15,18,16,0.95);

  backdrop-filter: blur(20px);

}

.nav-inner {

  max-width: 1160px; margin: 0 auto;

  padding: 0.9rem 1.5rem;

  display: flex; align-items: center; justify-content: space-between;

}

.logo {
  display: inline-flex;
  align-items: center;
  text-decoration: none;
}

.logo:hover { text-decoration: none; }

.nav-links { display: flex; align-items: center; gap: 1.75rem; }

.nav-link { font-size: 0.85rem; font-weight: 400; color: var(--color-text-muted); text-decoration: none; transition: color 0.2s; }

.nav-link:hover { color: var(--color-text); text-decoration: none; }

.nav-cta {

  font-size: 0.85rem; font-weight: 600;

  padding: 0.5rem 1.25rem; border-radius: 999px;

  background: var(--color-accent); color: #0f1210;

  text-decoration: none; transition: filter 0.2s, transform 0.15s;

}

.nav-cta:hover { filter: brightness(1.1); transform: translateY(-1px); text-decoration: none; }



/* HERO */

.hero {

  min-height: 96vh; display: flex; align-items: center;

  padding: 7rem 1.5rem 5rem; position: relative; overflow: hidden;

}

.hero-glow {

  position: absolute; inset: 0; pointer-events: none;

  background:

    radial-gradient(ellipse 55% 45% at 50% -5%, rgba(196,163,90,0.15), transparent),

    radial-gradient(ellipse 35% 55% at 88% 45%, rgba(196,163,90,0.06), transparent);

}

.hero-inner { max-width: 740px; margin: 0 auto; text-align: center; position: relative; z-index: 1; }



/* Hero — always visible; scroll sections animate in */

.badge, .hero-title, .hero-sub, .bullet, .hero-ctas, .trust-bar {

  opacity: 1;

  transform: translateY(0);

}

/* Fade-up animation for below-the-fold sections */

@media (prefers-reduced-motion: reduce) {

  .badge, .hero-title, .hero-sub, .bullet, .hero-ctas, .trust-bar,

  .demo-inner, .section-heading, .feature-card, .security-grid, .pricing-grid, .cta-inner, .demo-task {

    opacity: 1;

    transform: none;

    transition: none;

  }

}



.badge {

  display: inline-flex; align-items: center;

  font-size: 0.7rem; font-weight: 500; letter-spacing: 0.1em; text-transform: uppercase;

  padding: 0.38rem 1rem; border-radius: 999px;

  border: 1px solid rgba(196,163,90,0.4); color: var(--color-accent);

  margin-bottom: 2rem;

}

.hero-title {

  font-family: 'Instrument Serif', serif;

  font-size: clamp(3.2rem, 7.5vw, 5.2rem);

  font-weight: 400; line-height: 1.06;

  margin: 0 0 1.25rem; color: var(--color-text); letter-spacing: -0.01em;

}

.accent { color: var(--color-accent); font-style: italic; }

.hero-sub {

  font-size: 1.05rem; font-weight: 300; color: var(--color-text-muted);

  max-width: 540px; margin: 0 auto 2.5rem; line-height: 1.75;

}

.br-desktop { display: block; }



/* Bullets */

.bullets {

  list-style: none; padding: 0; margin: 0 auto 2.75rem;

  display: flex; flex-direction: column; align-items: center; gap: 0.55rem;

  max-width: 520px;

}

.bullet { display: flex; align-items: center; gap: 0.6rem; font-size: 0.93rem; color: var(--color-text); }



/* CTAs */

.hero-ctas { display: flex; align-items: center; justify-content: center; gap: 1rem; margin-bottom: 1.75rem; flex-wrap: wrap; }



/* Trust bar */

.trust-bar {

  display: flex; align-items: center; justify-content: center;

  gap: 0.7rem; flex-wrap: wrap; font-size: 0.75rem; color: var(--color-text-muted);

}

.sep { color: var(--color-border); }



/* BUTTONS */

.btn-primary {

  display: inline-block; font-family: 'Inter', sans-serif;

  font-weight: 600; font-size: 0.9rem;

  padding: 0.75rem 1.75rem; border-radius: 999px;

  background: linear-gradient(135deg, var(--color-accent), #a6853a);

  color: #0f1210; text-decoration: none; border: none; cursor: pointer;

  transition: filter 0.2s, transform 0.2s;

}

.btn-primary:hover { filter: brightness(1.08); transform: translateY(-2px); text-decoration: none; }

.btn-primary.full { display: block; text-align: center; width: 100%; }

.btn-primary.large { padding: 0.9rem 2.25rem; font-size: 1rem; }

.btn-ghost.large { padding: 0.9rem 2.25rem; font-size: 1rem; }



.btn-ghost {

  display: inline-block; font-family: 'Inter', sans-serif;

  font-weight: 500; font-size: 0.9rem;

  padding: 0.75rem 1.5rem; border-radius: 999px;

  border: 1px solid var(--color-border); color: var(--color-text-muted);

  text-decoration: none; transition: border-color 0.2s, color 0.2s;

  cursor: pointer; background: none;

}

.btn-ghost:hover { border-color: var(--color-accent); color: var(--color-text); text-decoration: none; }



.btn-ghost-sm {

  display: inline-block; font-size: 0.85rem; font-weight: 500;

  color: var(--color-accent); text-decoration: none;

  border-bottom: 1px solid rgba(196,163,90,0.4);

  padding-bottom: 1px; transition: border-color 0.2s;

}

.btn-ghost-sm:hover { border-color: var(--color-accent); text-decoration: none; }



.btn-outline {

  display: inline-block; font-family: 'Inter', sans-serif;

  font-weight: 600; font-size: 0.9rem;

  padding: 0.75rem 1.75rem; border-radius: 999px;

  border: 1px solid var(--color-border); color: var(--color-text);

  text-decoration: none; transition: border-color 0.2s, color 0.2s;

  text-align: center; cursor: pointer; background: none;

}

.btn-outline:hover { border-color: var(--color-accent); color: var(--color-accent); text-decoration: none; }

.btn-outline.full { display: block; width: 100%; }



/* SHARED SECTIONS */

.section-inner { max-width: 1160px; margin: 0 auto; }

.section-eyebrow { font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.16em; color: var(--color-accent); margin: 0 0 0.75rem; font-weight: 600; }

.section-heading {

  font-family: 'Instrument Serif', serif;

  font-size: clamp(2rem, 3.5vw, 2.9rem); font-weight: 400;

  margin: 0 0 3rem; line-height: 1.18;

  opacity: 0; transform: translateY(18px);

  transition: opacity 0.65s ease, transform 0.65s ease;

}

.section-heading.visible { opacity: 1; transform: translateY(0); }



/* DEMO */

.demo-section { padding: 5.5rem 1.5rem; background: var(--color-bg-elevated); border-top: 1px solid var(--color-border); border-bottom: 1px solid var(--color-border); }

.demo-inner {

  max-width: 920px; margin: 0 auto;

  opacity: 0; transform: translateY(24px);

  transition: opacity 0.7s ease, transform 0.7s ease;

}

.demo-inner.visible { opacity: 1; transform: translateY(0); }

.demo-title {

  font-family: 'Instrument Serif', serif;

  font-size: clamp(1.8rem, 3vw, 2.5rem); font-weight: 400;

  margin: 0.5rem 0 2rem; line-height: 1.2;

}

.demo-window { background: #070a08; border: 1px solid var(--color-border); border-radius: 14px; overflow: hidden; box-shadow: 0 40px 80px rgba(0,0,0,0.5); }

.demo-bar { background: var(--color-surface); padding: 0.7rem 1rem; display: flex; align-items: center; gap: 0.4rem; border-bottom: 1px solid var(--color-border); }

.dot { width: 10px; height: 10px; border-radius: 50%; }

.dot.r { background: #ff5f57; } .dot.a { background: #ffbd2e; } .dot.g { background: #28c840; }

.demo-bar-title { margin-left: 0.5rem; font-size: 0.75rem; color: var(--color-text-muted); font-family: 'Inter', sans-serif; }

.demo-body { display: grid; grid-template-columns: 1fr auto 1fr; gap: 2rem; padding: 1.75rem; align-items: start; }

.col-label { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.12em; color: var(--color-text-muted); margin: 0 0 0.75rem; font-weight: 600; }

.demo-input { font-size: 0.875rem; color: var(--color-text-muted); font-style: italic; border-left: 2px solid var(--color-border); padding-left: 0.75rem; margin: 0; line-height: 1.7; min-height: 5.5rem; }

.demo-cursor {

  display: inline-block;

  color: var(--color-accent);

  font-style: normal;

  animation: blink 1s step-end infinite;

}

@keyframes blink {

  50% { opacity: 0; }

}

.demo-sep { font-size: 1.75rem; color: var(--color-accent); display: flex; align-items: center; padding-top: 1.5rem; opacity: 0.6; }

.demo-tasks { display: flex; flex-direction: column; gap: 0.5rem; }

.demo-task {

  font-size: 0.82rem;

  background: var(--color-surface);

  padding: 0.55rem 0.8rem;

  border-radius: 7px;

  color: var(--color-text);

  opacity: 0;

  transform: translateY(22px);

  transition: opacity 0.65s cubic-bezier(.22,1,.36,1), transform 0.65s cubic-bezier(.22,1,.36,1);

}

.demo-task.visible {

  opacity: 1;

  transform: translateY(0);

}



.demo-cta-row {
  margin-top: 1.75rem;
  text-align: center;
}

.cta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: center;
}

.cta-row .btn-outline.large {
  display: inline-block;
  font-family: 'Inter', sans-serif;
  font-weight: 600;
  font-size: 1rem;
  padding: 0.9rem 2.25rem;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  color: var(--color-text);
  text-decoration: none;
  background: none;
}

.cta-row .btn-outline.large:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
  text-decoration: none;
}

/* FEATURES */

.features { padding: 6rem 1.5rem; }

.feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.25rem; }

.feature-card {

  background: var(--color-surface); border: 1px solid var(--color-border);

  border-radius: var(--radius); padding: 1.6rem;

  opacity: 0; transform: translateY(22px);

  transition: opacity 0.5s ease, transform 0.5s ease, border-color 0.2s, box-shadow 0.2s;

}

.feature-card.visible { opacity: 1; transform: translateY(0); }

.feature-card:hover { border-color: rgba(196,163,90,0.45); box-shadow: 0 8px 32px rgba(0,0,0,0.2); transform: translateY(-3px); }

.f-icon { font-size: 1.35rem; display: block; margin-bottom: 0.75rem; }

.feature-card h3 { font-family: 'Instrument Serif', serif; font-size: 1.05rem; margin: 0 0 0.4rem; font-weight: 400; color: var(--color-text); }

.feature-card p { font-size: 0.85rem; color: var(--color-text-muted); margin: 0; line-height: 1.65; }



/* SECURITY */

.security-section { padding: 6rem 1.5rem; background: var(--color-bg-elevated); border-top: 1px solid var(--color-border); }

.security-grid {

  display: grid; grid-template-columns: 1fr 1fr; gap: 5rem; align-items: start;

  opacity: 0; transform: translateY(20px);

  transition: opacity 0.7s ease, transform 0.7s ease;

}

.security-grid.visible { opacity: 1; transform: translateY(0); }

.sec-heading { font-family: 'Instrument Serif', serif; font-size: clamp(1.8rem, 3vw, 2.6rem); font-weight: 400; margin: 0.5rem 0 1rem; line-height: 1.18; }

.sec-body { font-size: 0.9rem; color: var(--color-text-muted); line-height: 1.8; margin-bottom: 1.75rem; }

.sec-right { display: flex; flex-direction: column; gap: 1.25rem; }

.sec-badge { display: flex; gap: 0.875rem; align-items: flex-start; }

.sec-icon { font-size: 1.1rem; flex-shrink: 0; margin-top: 2px; }

.sec-badge h4 { margin: 0 0 0.2rem; font-size: 0.875rem; font-weight: 600; color: var(--color-text); }

.sec-badge p { margin: 0; font-size: 0.8rem; color: var(--color-text-muted); line-height: 1.4; }



/* PRICING */

.pricing-section { padding: 6rem 1.5rem; }

.pricing-trial-note {
  text-align: center;
  font-size: 0.9rem;
  color: var(--color-accent);
  margin: -0.5rem auto 1.5rem;
  max-width: 520px;
  line-height: 1.55;
}

.pricing-grid {

  display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.25rem;

  opacity: 0; transform: translateY(20px);

  transition: opacity 0.65s ease, transform 0.65s ease;

}

.pricing-grid.visible { opacity: 1; transform: translateY(0); }

.plan-card {

  background: var(--color-surface); border: 1px solid var(--color-border);

  border-radius: calc(var(--radius) + 4px); padding: 2rem;

  display: flex; flex-direction: column; gap: 0;

  transition: border-color 0.2s;

  position: relative;

}

.plan-card.featured {

  border-color: rgba(196,163,90,0.5);

  box-shadow: 0 0 60px rgba(196,163,90,0.08);

}

.plan-top { margin-bottom: 1.5rem; }

.plan-badge {

  display: inline-block; font-size: 0.65rem; font-weight: 700;

  text-transform: uppercase; letter-spacing: 0.1em;

  padding: 0.25rem 0.6rem; border-radius: 999px;

  background: rgba(196,163,90,0.15); color: var(--color-accent);

  border: 1px solid rgba(196,163,90,0.3); margin-bottom: 0.75rem;

}

.plan-top h3 { font-size: 1rem; font-weight: 600; margin: 0 0 0.75rem; color: var(--color-text); }

.plan-price { display: flex; align-items: baseline; gap: 0.25rem; margin-bottom: 0.25rem; }

.plan-amount { font-family: 'Instrument Serif', serif; font-size: 2.8rem; color: var(--color-accent); line-height: 1; }

.plan-period { font-size: 0.9rem; color: var(--color-text-muted); }

.plan-members { font-size: 0.8rem; color: var(--color-text-muted); margin: 0; }

.plan-features { list-style: none; padding: 0; margin: 0 0 1.75rem; display: flex; flex-direction: column; gap: 0.6rem; flex: 1; }

.plan-features li { font-size: 0.85rem; color: var(--color-text); }

.plan-note { text-align: center; font-size: 0.72rem; color: var(--color-text-muted); margin: 0.75rem 0 0; }

.currency-note {

  text-align: center;

  font-size: 0.75rem;

  color: var(--color-text-muted);

  margin-top: 1.25rem;

}



/* FINAL CTA */

.final-cta { padding: 6rem 1.5rem; background: var(--color-bg-elevated); border-top: 1px solid var(--color-border); }

.cta-inner {

  max-width: 560px; margin: 0 auto; text-align: center;

  opacity: 0; transform: translateY(20px);

  transition: opacity 0.65s ease, transform 0.65s ease;

}

.cta-inner.visible { opacity: 1; transform: translateY(0); }

.cta-inner h2 { font-family: 'Instrument Serif', serif; font-size: clamp(2rem, 4vw, 3rem); font-weight: 400; margin: 0 0 0.75rem; }

.cta-inner p { font-size: 0.95rem; color: var(--color-text-muted); margin-bottom: 2rem; }

.cta-note { font-size: 0.75rem; color: var(--color-text-muted); margin-top: 1rem; margin-bottom: 0; }



/* FOOTER */

.footer { border-top: 1px solid var(--color-border); padding: 3rem 1.5rem 2rem; }

.footer-inner {

  max-width: 1160px; margin: 0 auto 2rem;

  display: flex; align-items: center; justify-content: space-between;

  gap: 2rem; flex-wrap: wrap;

}

.footer-brand p { font-size: 0.82rem; color: var(--color-text-muted); margin: 0.35rem 0 0; }

.footer-links { display: flex; gap: 1.5rem; }

.footer-links a { font-size: 0.85rem; color: var(--color-text-muted); text-decoration: none; transition: color 0.2s; }

.footer-links a:hover { color: var(--color-text); text-decoration: none; }

.footer-bottom { max-width: 1160px; margin: 0 auto; padding-top: 1.5rem; border-top: 1px solid var(--color-border); font-size: 0.78rem; color: var(--color-text-muted); }



/* RESPONSIVE */

@media (max-width: 900px) {

  .pricing-grid { grid-template-columns: 1fr; max-width: 440px; }

  .security-grid { grid-template-columns: 1fr; gap: 2.5rem; }

  .footer-inner { flex-direction: column; align-items: flex-start; }

}

@media (max-width: 640px) {

  .hero { padding: 5rem 1rem 3rem; }

  .demo-body { grid-template-columns: 1fr; }

  .demo-sep { display: none; }

  .hero-ctas { flex-direction: column; }

  .br-desktop { display: none; }

  .nav-links .nav-link:not(:last-child) { display: none; }

}

</style>


