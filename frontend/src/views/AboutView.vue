<template>
  <div class="page">
    <nav class="nav">
      <div class="nav-inner">
        <RouterLink to="/" class="logo">Plenvo</RouterLink>
        <div class="nav-links">
          <RouterLink to="/security" class="nav-link">Security</RouterLink>
          <RouterLink to="/login" class="nav-link">Sign in</RouterLink>
          <RouterLink to="/signup" class="nav-cta">Start for free</RouterLink>
        </div>
      </div>
    </nav>

    <main class="main">
      <div class="content">
        <p class="eyebrow">About Plenvo</p>
        <h1>Built for managers.<br /><em class="accent">By someone who gets it.</em></h1>

        <div class="story">
          <p>Managing a team is one of the hardest jobs in any company. You're responsible for results you don't directly control. You spend hours chasing updates, running meetings that produce more questions than answers, and trying to keep track of who owns what — across projects, training, and performance.</p>

          <p>Plenvo was built to fix that. One dashboard. Every tool a manager needs. Powered by AI so the admin work disappears and the clarity stays.</p>

          <p>We believe managers should spend their time leading — not chasing. That's why Plenvo turns your meeting notes into assigned tasks automatically, tracks your team's training and performance in real time, and gives you a single view of everything that matters.</p>

          <p>No bloat. No per-seat pricing surprises. No complexity. Just control.</p>
        </div>

        <div class="values">
          <div class="value" v-for="v in values" :key="v.title">
            <span class="v-icon">{{ v.icon }}</span>
            <div>
              <h3>{{ v.title }}</h3>
              <p>{{ v.desc }}</p>
            </div>
          </div>
        </div>

        <div class="cta-block">
          <h2>Ready to take control?</h2>
          <p>Start your 14-day free trial. No credit card required.</p>
          <RouterLink to="/signup" class="btn-primary">Start for free →</RouterLink>
        </div>
      </div>
    </main>

    <footer class="footer">
      <div class="footer-inner">
        <span class="logo small">Plenvo</span>
        <div class="footer-links">
          <RouterLink to="/security" class="nav-link">Security</RouterLink>
          <RouterLink to="/privacy" class="nav-link">Privacy</RouterLink>
          <RouterLink to="/terms" class="nav-link">Terms</RouterLink>
          <a href="mailto:hi@plenvo.io" class="nav-link">hi@plenvo.io</a>
        </div>
        <span class="copy">© 2026 Plenvo</span>
      </div>
    </footer>
  </div>
</template>

<script setup>
const values = [
  { icon: '⚡', title: 'Speed over complexity', desc: 'Every feature is designed to save time, not create new workflows to manage.' },
  { icon: '🔒', title: 'Security first', desc: 'Your company data is isolated, encrypted and GDPR compliant. No exceptions.' },
  { icon: '🎯', title: 'Manager-focused', desc: 'Built exclusively for the person responsible for outcomes. Not for the whole company.' },
  { icon: '🤝', title: 'Honest pricing', desc: 'Flat monthly rate. No per-seat surprises. No hidden fees. Cancel anytime.' },
]
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Instrument+Serif:ital@0;1&display=swap');

.page { background: var(--color-bg); color: var(--color-text); font-family: 'Inter', sans-serif; min-height: 100vh; }

.nav { position: sticky; top: 0; z-index: 50; border-bottom: 1px solid var(--color-border); background: rgba(15,18,16,0.95); backdrop-filter: blur(20px); }
.nav-inner { max-width: 1160px; margin: 0 auto; padding: 0.9rem 1.5rem; display: flex; align-items: center; justify-content: space-between; }
.logo { font-family: 'Instrument Serif', serif; font-size: 1.75rem; color: var(--color-accent); text-decoration: none; letter-spacing: 0.04em; }
.logo.small { font-size: 1.2rem; }
.logo:hover { text-decoration: none; color: var(--color-accent); }
.nav-links { display: flex; align-items: center; gap: 1.75rem; }
.nav-link { font-size: 0.85rem; color: var(--color-text-muted); text-decoration: none; transition: color 0.2s; }
.nav-link:hover { color: var(--color-text); text-decoration: none; }
.nav-cta { font-size: 0.85rem; font-weight: 600; padding: 0.5rem 1.25rem; border-radius: 999px; background: var(--color-accent); color: #0f1210; text-decoration: none; }
.nav-cta:hover { filter: brightness(1.1); text-decoration: none; }

.main { padding: 6rem 1.5rem; }
.content { max-width: 680px; margin: 0 auto; }

.eyebrow { font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.16em; color: var(--color-accent); margin: 0 0 0.75rem; font-weight: 600; }

h1 { font-family: 'Instrument Serif', serif; font-size: clamp(2.4rem, 5vw, 3.5rem); font-weight: 400; line-height: 1.1; margin: 0 0 3rem; }
.accent { color: var(--color-accent); font-style: italic; }

.story { display: flex; flex-direction: column; gap: 1.25rem; margin-bottom: 3.5rem; }
.story p { font-size: 1rem; color: var(--color-text-muted); line-height: 1.85; margin: 0; font-weight: 300; }

.values { display: flex; flex-direction: column; gap: 1.5rem; margin-bottom: 4rem; padding: 2rem; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius); }
.value { display: flex; gap: 1rem; align-items: flex-start; }
.v-icon { font-size: 1.2rem; flex-shrink: 0; margin-top: 2px; }
.value h3 { margin: 0 0 0.25rem; font-size: 0.95rem; font-weight: 600; color: var(--color-text); }
.value p { margin: 0; font-size: 0.875rem; color: var(--color-text-muted); line-height: 1.6; }

.cta-block { text-align: center; padding: 3rem; background: var(--color-bg-elevated); border: 1px solid var(--color-border); border-radius: var(--radius); }
.cta-block h2 { font-family: 'Instrument Serif', serif; font-size: 1.8rem; font-weight: 400; margin: 0 0 0.5rem; }
.cta-block p { font-size: 0.9rem; color: var(--color-text-muted); margin-bottom: 1.5rem; }

.btn-primary { display: inline-block; font-weight: 600; font-size: 0.9rem; padding: 0.75rem 1.75rem; border-radius: 999px; background: linear-gradient(135deg, var(--color-accent), #a6853a); color: #0f1210; text-decoration: none; transition: filter 0.2s, transform 0.2s; }
.btn-primary:hover { filter: brightness(1.08); transform: translateY(-2px); text-decoration: none; }

.footer { border-top: 1px solid var(--color-border); padding: 1.5rem; }
.footer-inner { max-width: 1160px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }
.footer-links { display: flex; gap: 1.5rem; }
.copy { font-size: 0.78rem; color: var(--color-text-muted); }
</style>