<template>
  <div class="page">
    <nav class="nav">
      <div class="nav-inner">
        <RouterLink to="/" class="logo" aria-label="Plenvo">
          <PlenvoLogo tag="span" variant="lockup" />
        </RouterLink>
        <div class="nav-links">
          <RouterLink to="/about" class="nav-link">About</RouterLink>
          <RouterLink to="/security" class="nav-link">Security</RouterLink>
          <RouterLink to="/support" class="nav-link">Support</RouterLink>
          <SiteAccountMenu v-if="user" />
          <template v-else>
            <RouterLink to="/login" class="nav-link">Sign in</RouterLink>
            <RouterLink to="/signup" class="nav-cta">Start for free</RouterLink>
          </template>
        </div>
      </div>
    </nav>

    <main class="main">
      <div class="content">
        <p class="eyebrow">Terms of Service</p>
        <h1>The legal stuff<br /><em class="accent">made clear.</em></h1>
        <p class="updated">Last updated: May 5, 2026</p>

        <section class="section">
          <h2>Agreement</h2>
          <p>By using Plenvo, you agree to these Terms of Service. If you don't agree, don't use the service.</p>
          <p>We may update these terms occasionally. We'll notify you of significant changes via email. Continued use after changes means you accept the updated terms.</p>
        </section>

        <section class="section">
          <h2>Your account</h2>
          <p>When you create an account:</p>
          <ul>
            <li>You must provide accurate information</li>
            <li>You're responsible for keeping your password secure</li>
            <li>You're responsible for all activity under your account</li>
            <li>You must be at least 16 years old</li>
            <li>One person per account — no sharing login credentials</li>
          </ul>
          <p>If you believe your account has been compromised, contact us immediately at <a href="mailto:hi@plenvo.io">hi@plenvo.io</a></p>
        </section>

        <section class="section">
          <h2>Free trial</h2>
          <p>New accounts get a 14-day free trial:</p>
          <ul>
            <li><strong>No credit card required</strong> to start — you can explore Plenvo without adding payment details</li>
            <li>Card collection happens only if you explicitly upgrade to a paid plan</li>
            <li>Cancel anytime during the trial — no charge, no questions asked</li>
            <li>One trial per organisation</li>
          </ul>
        </section>

        <section class="section">
          <h2>Subscription & payment</h2>
          <p><strong>Billing:</strong></p>
          <ul>
            <li>Subscriptions are billed monthly or annually (depending on your plan)</li>
            <li>Prices are shown in your local currency (GBP, EUR, USD, or INR) and exclude VAT where applicable</li>
            <li>Payment is processed via Stripe — we never store your card details</li>
            <li>Failed payments may result in service suspension after 7 days</li>
          </ul>
          <p><strong>Cancellation:</strong></p>
          <ul>
            <li>Cancel anytime from your account settings</li>
            <li>No refunds for partial months — you keep access until the billing period ends</li>
            <li>After cancellation, your data is retained for 30 days, then permanently deleted</li>
          </ul>
          <p><strong>Plan changes:</strong></p>
          <ul>
            <li>Upgrades take effect immediately — you're charged a prorated amount</li>
            <li>Downgrades take effect at the next billing cycle</li>
          </ul>
        </section>

        <section class="section">
          <h2>Acceptable use</h2>
          <p>You may NOT use Plenvo to:</p>
          <ul>
            <li>Violate laws or regulations</li>
            <li>Infringe on intellectual property rights</li>
            <li>Distribute malware, spam, or harmful content</li>
            <li>Harass, abuse, or harm others</li>
            <li>Attempt to access other users' data</li>
            <li>Reverse engineer or copy our software</li>
            <li>Resell or redistribute Plenvo without permission</li>
          </ul>
          <p>We reserve the right to suspend or terminate accounts that violate these terms.</p>
        </section>

        <section class="section">
          <h2>Your data & content</h2>
          <p><strong>Ownership:</strong></p>
          <ul>
            <li>You own all data you put into Plenvo</li>
            <li>We don't claim any rights to your content</li>
            <li>You grant us permission to store and process your data to provide the service</li>
          </ul>
          <p><strong>Responsibility:</strong></p>
          <ul>
            <li>You're responsible for the accuracy and legality of your data</li>
            <li>You're responsible for complying with data protection laws (e.g., GDPR) when using Plenvo</li>
            <li>Back up important data — we provide backups, but you're ultimately responsible</li>
          </ul>
        </section>

        <section class="section">
          <h2>Service availability</h2>
          <p>We work hard to keep Plenvo running smoothly, but:</p>
          <ul>
            <li>We don't guarantee 100% uptime (no one can)</li>
            <li>We may perform maintenance that temporarily limits access — we'll notify you in advance when possible</li>
            <li>We're not liable for losses due to service interruptions</li>
          </ul>
          <p>Current uptime and incidents: We'll add a status page soon.</p>
        </section>

        <section class="section">
          <h2>Intellectual property</h2>
          <p>Plenvo's software, design, and branding are owned by us and protected by copyright and trademark laws. You may not:</p>
          <ul>
            <li>Copy, modify, or redistribute our code</li>
            <li>Use our trademarks without permission</li>
            <li>Remove copyright notices from the service</li>
          </ul>
        </section>

        <section class="section">
          <h2>Limitation of liability</h2>
          <p>To the maximum extent permitted by law:</p>
          <ul>
            <li>Plenvo is provided "as is" without warranties of any kind</li>
            <li>We're not liable for indirect, incidental, or consequential damages</li>
            <li>Our total liability is limited to the amount you paid in the past 12 months</li>
            <li>This doesn't limit liability for gross negligence, fraud, or death/injury caused by us</li>
          </ul>
          <p>Some jurisdictions don't allow liability limitations — if yours doesn't, the above may not apply.</p>
        </section>

        <section class="section">
          <h2>Disputes & governing law</h2>
          <p>These terms are governed by the laws of Germany. Any disputes will be resolved in Frankfurt, Germany courts.</p>
          <p>We prefer to resolve issues informally — contact us first at <a href="mailto:hi@plenvo.io">hi@plenvo.io</a> before pursuing legal action.</p>
        </section>

        <section class="section">
          <h2>Termination</h2>
          <p>We may suspend or terminate your account if:</p>
          <ul>
            <li>You violate these terms</li>
            <li>You fail to pay (after 7-day grace period)</li>
            <li>We're required to by law</li>
            <li>We discontinue the service (with 30 days' notice)</li>
          </ul>
          <p>Upon termination, you lose access immediately. Data is retained for 30 days, then permanently deleted.</p>
        </section>

        <section class="section">
          <h2>Contact</h2>
          <p>Questions about these terms? Email <a href="mailto:hi@plenvo.io">hi@plenvo.io</a></p>
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
        <span class="logo small" aria-label="Plenvo">
          <PlenvoLogo tag="span" variant="lockup" compact />
        </span>
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
import PlenvoLogo from '@/components/PlenvoLogo.vue'
import SiteAccountMenu from '@/components/SiteAccountMenu.vue'
import { user } from '@/composables/session'
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Instrument+Serif:ital@0;1&display=swap');

.page { background: var(--color-bg); color: var(--color-text); font-family: 'Inter', sans-serif; min-height: 100vh; }

.nav { position: sticky; top: 0; z-index: 50; border-bottom: 1px solid var(--color-border); background: rgba(15,18,16,0.95); backdrop-filter: blur(20px); }
.nav-inner { max-width: 1160px; margin: 0 auto; padding: 0.9rem 1.5rem; display: flex; align-items: center; justify-content: space-between; }
.logo { display: inline-flex; align-items: center; text-decoration: none; }
.logo:hover { text-decoration: none; }
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