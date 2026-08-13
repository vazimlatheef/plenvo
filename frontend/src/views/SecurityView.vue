<template>
  <div class="page">
    <nav class="nav">
      <div class="nav-inner">
        <RouterLink to="/" class="logo">Plenvo</RouterLink>
        <div class="nav-links">
          <RouterLink to="/about" class="nav-link">About</RouterLink>
          <RouterLink to="/login" class="nav-link">Sign in</RouterLink>
          <RouterLink to="/signup" class="nav-cta">Start for free</RouterLink>
        </div>
      </div>
    </nav>

    <main class="main">
      <div class="content">
        <p class="eyebrow">Security</p>
        <h1>Your data stays yours.<br /><em class="accent">Always.</em></h1>
        <p class="lead">Plenvo is built for companies that take data seriously. Here's exactly how we protect your organisation's information.</p>

        <div class="sec-grid">
          <div class="sec-card" v-for="s in sections" :key="s.title">
            <span class="sec-icon">{{ s.icon }}</span>
            <div>
              <h3>{{ s.title }}</h3>
              <p>{{ s.desc }}</p>
            </div>
          </div>
        </div>

        <div class="compliance">
          <p class="eyebrow">Compliance</p>
          <h2>Built for enterprise from day one.</h2>
          <div class="comp-grid">
            <div class="comp-item" v-for="c in compliance" :key="c.title">
              <div class="comp-status" :class="c.status">{{ c.label }}</div>
              <h4>{{ c.title }}</h4>
              <p>{{ c.desc }}</p>
            </div>
          </div>
        </div>

        <div class="contact-block">
          <h2>Security questions?</h2>
          <p>We take every security inquiry seriously. Contact our team directly.</p>
          <a href="mailto:hi@plenvo.io" class="btn-primary">Contact security team →</a>
        </div>
      </div>
    </main>

    <footer class="footer">
      <div class="footer-inner">
        <span class="logo small">Plenvo</span>
        <div class="footer-links">
          <RouterLink to="/about" class="nav-link">About</RouterLink>
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
const sections = [
  {
    icon: '🏢',
    title: 'Complete data isolation',
    desc: 'Every organisation on Plenvo has its own isolated data environment. Your company\'s projects, tasks, employees and notes are completely separated from every other organisation. There is no shared database, no cross-contamination, and no scenario in which another company can access your data.',
  },
  {
    icon: '🔐',
    title: 'End-to-end encryption',
    desc: 'All data is encrypted in transit using TLS 1.3 and encrypted at rest using AES-256. This means your data is protected whether it\'s travelling between your browser and our servers, or sitting in our database.',
  },
  {
    icon: '🔑',
    title: 'Authentication & access control',
    desc: 'Plenvo uses industry-standard JWT authentication with short-lived tokens. Every API request is verified. Employees can only access data within their own organisation. Admins control all user permissions.',
  },
  {
    icon: '🔒',
    title: 'Payment security via Stripe',
    desc: 'Plenvo never stores your card details. All payment processing is handled exclusively by Stripe, a PCI DSS Level 1 certified payment processor. Your card information never touches our servers.',
  },
  {
    icon: '🇪🇺',
    title: 'GDPR compliance',
    desc: 'Plenvo is built for European data regulations. Your data is stored in EU-based infrastructure. You can request data export or deletion at any time. We never sell your data to third parties.',
  },
  {
    icon: '🛡️',
    title: 'Infrastructure security',
    desc: 'Plenvo runs on Render\'s enterprise cloud infrastructure in Frankfurt, EU. All servers are protected by DDoS mitigation, network firewalls, and automated security monitoring. Database backups run daily.',
  },
]

const compliance = [
  { title: 'GDPR', desc: 'EU data regulation compliance. Data stored in Frankfurt, EU.', status: 'live', label: '✓ Live' },
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
.content { max-width: 800px; margin: 0 auto; }

.eyebrow { font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.16em; color: var(--color-accent); margin: 0 0 0.75rem; font-weight: 600; }
h1 { font-family: 'Instrument Serif', serif; font-size: clamp(2.4rem, 5vw, 3.5rem); font-weight: 400; line-height: 1.1; margin: 0 0 1.25rem; }
.accent { color: var(--color-accent); font-style: italic; }
.lead { font-size: 1rem; color: var(--color-text-muted); line-height: 1.8; margin: 0 0 3.5rem; font-weight: 300; max-width: 600px; }

.sec-grid { display: flex; flex-direction: column; gap: 0; margin-bottom: 4rem; border: 1px solid var(--color-border); border-radius: var(--radius); overflow: hidden; }
.sec-card { display: flex; gap: 1.25rem; align-items: flex-start; padding: 1.75rem; border-bottom: 1px solid var(--color-border); transition: background 0.2s; }
.sec-card:last-child { border-bottom: none; }
.sec-card:hover { background: var(--color-surface); }
.sec-icon { font-size: 1.25rem; flex-shrink: 0; margin-top: 2px; }
.sec-card h3 { margin: 0 0 0.4rem; font-size: 0.95rem; font-weight: 600; color: var(--color-text); }
.sec-card p { margin: 0; font-size: 0.875rem; color: var(--color-text-muted); line-height: 1.7; }

.compliance { margin-bottom: 4rem; }
.compliance h2 { font-family: 'Instrument Serif', serif; font-size: clamp(1.6rem, 3vw, 2.2rem); font-weight: 400; margin: 0.5rem 0 2rem; }
.comp-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }
.comp-item { background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius); padding: 1.25rem; }
.comp-status { display: inline-block; font-size: 0.68rem; font-weight: 600; padding: 0.2rem 0.6rem; border-radius: 999px; margin-bottom: 0.6rem; }
.comp-status.live { background: rgba(60,140,100,0.2); color: #4ade80; border: 1px solid rgba(60,140,100,0.3); }
.comp-status.progress { background: rgba(196,163,90,0.15); color: var(--color-accent); border: 1px solid rgba(196,163,90,0.3); }
.comp-status.roadmap { background: rgba(100,116,139,0.15); color: #94a3b8; border: 1px solid rgba(100,116,139,0.2); }
.comp-item h4 { margin: 0 0 0.25rem; font-size: 0.9rem; font-weight: 600; color: var(--color-text); }
.comp-item p { margin: 0; font-size: 0.8rem; color: var(--color-text-muted); line-height: 1.5; }

.contact-block { text-align: center; padding: 3rem; background: var(--color-bg-elevated); border: 1px solid var(--color-border); border-radius: var(--radius); }
.contact-block h2 { font-family: 'Instrument Serif', serif; font-size: 1.8rem; font-weight: 400; margin: 0 0 0.5rem; }
.contact-block p { font-size: 0.9rem; color: var(--color-text-muted); margin-bottom: 1.5rem; }

.btn-primary { display: inline-block; font-weight: 600; font-size: 0.9rem; padding: 0.75rem 1.75rem; border-radius: 999px; background: linear-gradient(135deg, var(--color-accent), #a6853a); color: #0f1210; text-decoration: none; transition: filter 0.2s, transform 0.2s; }
.btn-primary:hover { filter: brightness(1.08); transform: translateY(-2px); text-decoration: none; }

.footer { border-top: 1px solid var(--color-border); padding: 1.5rem; }
.footer-inner { max-width: 1160px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }
.footer-links { display: flex; gap: 1.5rem; }
.copy { font-size: 0.78rem; color: var(--color-text-muted); }
</style>