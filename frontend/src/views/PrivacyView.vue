<template>
  <div class="page">
    <nav class="nav">
      <div class="nav-inner">
        <RouterLink to="/" class="logo">Plenvo</RouterLink>
        <div class="nav-links">
          <RouterLink to="/about" class="nav-link">About</RouterLink>
          <RouterLink to="/security" class="nav-link">Security</RouterLink>
          <RouterLink to="/support" class="nav-link">Support</RouterLink>
          <RouterLink to="/login" class="nav-link">Sign in</RouterLink>
          <RouterLink to="/signup" class="nav-cta">Start for free</RouterLink>
        </div>
      </div>
    </nav>

    <main class="main">
      <div class="content">
        <p class="eyebrow">Privacy Policy</p>
        <h1>How we handle<br /><em class="accent">your data.</em></h1>
        <p class="updated">Last updated: May 5, 2026</p>

        <section class="section">
          <h2>What we collect</h2>
          <p>When you use Plenvo, we collect:</p>
          <ul>
            <li><strong>Account information:</strong> Your name, email address, company name, and position when you sign up.</li>
            <li><strong>Usage data:</strong> Information about how you use Plenvo — projects created, tasks assigned, training completed — to provide the service.</li>
            <li><strong>Payment information:</strong> Handled exclusively by Stripe. We never see or store your card details. Stripe is PCI DSS Level 1 certified.</li>
            <li><strong>Technical data:</strong> IP address, browser type, and device information for security and service improvement.</li>
          </ul>
        </section>

        <section class="section">
          <h2>How we use your data</h2>
          <p>We use your information to:</p>
          <ul>
            <li>Provide and improve Plenvo's features</li>
            <li>Process payments and manage your subscription</li>
            <li>Send important service updates (you can opt out of marketing emails)</li>
            <li>Respond to your support requests</li>
            <li>Detect and prevent fraud or security issues</li>
          </ul>
          <p>We <strong>never sell your data</strong> to third parties. Ever.</p>
        </section>

        <section class="section">
          <h2>Data security</h2>
          <p>Your data is protected with:</p>
          <ul>
            <li><strong>Encryption:</strong> TLS 1.3 in transit, AES-256 at rest</li>
            <li><strong>Complete isolation:</strong> Your organisation's data is never mixed with other organisations</li>
            <li><strong>EU hosting:</strong> All data stored in Frankfurt, Germany (EU-based infrastructure)</li>
            <li><strong>Daily backups:</strong> Automated backups for disaster recovery</li>
          </ul>
        </section>

        <section class="section">
          <h2>Your rights (GDPR)</h2>
          <p>Under GDPR, you have the right to:</p>
          <ul>
            <li><strong>Access:</strong> Request a copy of all data we hold about you</li>
            <li><strong>Correction:</strong> Update or correct inaccurate information</li>
            <li><strong>Deletion:</strong> Request permanent deletion of your account and data</li>
            <li><strong>Export:</strong> Download your data in a portable format</li>
            <li><strong>Object:</strong> Opt out of marketing communications at any time</li>
          </ul>
          <p>To exercise any of these rights, email us at <a href="mailto:hi@plenvo.io">hi@plenvo.io</a>. We'll respond within 30 days.</p>
        </section>

        <section class="section">
          <h2>Cookies</h2>
          <p>Plenvo uses minimal cookies:</p>
          <ul>
            <li><strong>Essential cookies:</strong> Required for login and core functionality (cannot be disabled)</li>
            <li><strong>Analytics cookies:</strong> We do not currently use analytics cookies</li>
          </ul>
        </section>

        <section class="section">
          <h2>Data retention</h2>
          <p>We retain your data:</p>
          <ul>
            <li><strong>Active accounts:</strong> As long as your subscription is active</li>
            <li><strong>Cancelled accounts:</strong> 30 days after cancellation, then permanently deleted</li>
            <li><strong>Legal obligations:</strong> Some data (invoices, payment records) retained for 7 years for tax/accounting compliance</li>
          </ul>
        </section>

        <section class="section">
          <h2>Third-party services</h2>
          <p>We use these trusted partners:</p>
          <ul>
            <li><strong>Stripe:</strong> Payment processing (PCI DSS Level 1 certified)</li>
            <li><strong>Render:</strong> Cloud hosting in Frankfurt, EU</li>
            <li><strong>Anthropic:</strong> AI processing for the AI Terminal feature</li>
          </ul>
          <p>These partners process data only as instructed and under strict data processing agreements.</p>
        </section>

        <section class="section">
          <h2>Children's privacy</h2>
          <p>Plenvo is not intended for anyone under 16 years old. We do not knowingly collect data from children.</p>
        </section>

        <section class="section">
          <h2>Changes to this policy</h2>
          <p>We may update this privacy policy as Plenvo evolves. We'll notify you of significant changes via email. Continued use after changes means you accept the updated policy.</p>
        </section>

        <section class="section">
          <h2>Contact us</h2>
          <p>Questions about privacy? Email <a href="mailto:hi@plenvo.io">hi@plenvo.io</a></p>
          <p class="address">
            Plenvo<br />
            Frankfurt, Germany<br />
            European Union
          </p>
        </section>
      </div>
    </main>

    <footer class="footer">
      <div class="footer-inner">
        <span class="logo small">Plenvo</span>
        <div class="footer-links">
          <RouterLink to="/about">About</RouterLink>
          <RouterLink to="/security">Security</RouterLink>
          <RouterLink to="/support">Support</RouterLink>
          <RouterLink to="/privacy">Privacy</RouterLink>
          <RouterLink to="/terms">Terms</RouterLink>
          <a href="mailto:hi@plenvo.io">hi@plenvo.io</a>
        </div>
        <span class="copy">© 2026 Plenvo</span>
      </div>
    </footer>
  </div>
</template>

<script setup>
// No JavaScript needed for static page
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
h1 { font-family: 'Instrument Serif', serif; font-size: clamp(2.4rem, 5vw, 3.5rem); font-weight: 400; line-height: 1.1; margin: 0 0 0.5rem; }
.accent { color: var(--color-accent); font-style: italic; }
.updated { font-size: 0.85rem; color: var(--color-text-muted); margin: 0 0 3rem; }

.section { margin-bottom: 3rem; }
.section h2 { font-family: 'Instrument Serif', serif; font-size: 1.5rem; font-weight: 400; margin: 0 0 1rem; color: var(--color-text); }
.section p { font-size: 0.95rem; color: var(--color-text-muted); line-height: 1.8; margin: 0 0 1rem; }
.section ul { margin: 1rem 0; padding-left: 1.5rem; }
.section li { font-size: 0.95rem; color: var(--color-text-muted); line-height: 1.8; margin-bottom: 0.75rem; }
.section a { color: var(--color-accent); text-decoration: none; border-bottom: 1px solid rgba(196,163,90,0.3); }
.section a:hover { border-color: var(--color-accent); }
.address { font-size: 0.9rem; line-height: 1.6; margin-top: 1rem; }

.footer { border-top: 1px solid var(--color-border); padding: 1.5rem; }
.footer-inner { max-width: 1160px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }
.footer-links { display: flex; gap: 1.5rem; }
.footer-links a { font-size: 0.85rem; color: var(--color-text-muted); text-decoration: none; transition: color 0.2s; }
.footer-links a:hover { color: var(--color-text); }
.copy { font-size: 0.78rem; color: var(--color-text-muted); }
</style>