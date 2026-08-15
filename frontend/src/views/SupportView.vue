<template>
  <div class="page">
    <SiteNav />

    <main class="main">
      <div class="content">
        <p class="eyebrow">Support</p>
        <h1>We’re here<br /><em class="accent">to help.</em></h1>

        <section class="contact-card">
          <h2>Contact</h2>
          <p>
            Email <a href="mailto:hi@plenvo.io">hi@plenvo.io</a> with questions about your account,
            billing, or how to use Plenvo.
          </p>
          <p class="note">
            We aim to reply within one to two business days. During busy periods it may take a little longer.
          </p>
          <a href="mailto:hi@plenvo.io" class="btn-primary">Email hi@plenvo.io</a>
        </section>

        <section class="faq">
          <h2>Frequently asked questions</h2>
          <div v-for="item in faqs" :key="item.q" class="faq-item">
            <h3>{{ item.q }}</h3>
            <p>{{ item.a }}</p>
          </div>
        </section>
      </div>
    </main>

    <SiteFooter />
  </div>
</template>

<script setup>
import SiteFooter from '@/components/SiteFooter.vue'
import SiteNav from '@/components/SiteNav.vue'

const faqs = [
  {
    q: 'Can I use Plenvo on my own?',
    a: 'Yes. You can create projects and tasks for your own work without inviting anyone. Team features are available when you need them.',
  },
  {
    q: 'How do I add people to my team?',
    a: 'From Team, add a member with their name and email. You can invite them to Plenvo later so they get an account and can update their own tasks.',
  },
  {
    q: 'What happens if I assign a task to someone without an account?',
    a: 'You can assign work to a lightweight contact. When they accept an invite and create an account, their task history stays linked.',
  },
  {
    q: 'How do I reset my password?',
    a: 'Use Forgot password on the sign-in page. You’ll receive a reset link by email. Password-reset messages are transactional and are sent even if you’ve opted out of marketing email.',
  },
  {
    q: 'Where is my data stored?',
    a: 'Plenvo runs on Render with a PostgreSQL database. Organisation data is isolated per workspace. See the Security page for more detail.',
  },
]
</script>

<style scoped>
.page {
  background: var(--color-bg);
  color: var(--color-text);
  font-family: var(--font-body);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main {
  padding: 5rem 1.5rem 4rem;
  flex: 1;
}

.content {
  max-width: 680px;
  margin: 0 auto;
}

.eyebrow {
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: var(--color-accent);
  margin: 0 0 0.75rem;
  font-weight: 600;
}

h1 {
  font-family: var(--font-display);
  font-size: clamp(2.4rem, 5vw, 3.4rem);
  font-weight: 400;
  line-height: 1.1;
  margin: 0 0 2.5rem;
}

.accent {
  color: var(--color-accent);
  font-style: italic;
}

.contact-card {
  padding: 1.75rem 1.6rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  margin-bottom: 3rem;
}

.contact-card h2 {
  margin: 0 0 0.65rem;
  font-size: 1.35rem;
  font-weight: 400;
}

.contact-card p {
  margin: 0 0 0.85rem;
  font-size: 0.95rem;
  color: var(--color-text-muted);
  line-height: 1.7;
  font-weight: 300;
}

.contact-card a {
  color: var(--color-accent);
}

.note {
  font-size: 0.88rem !important;
}

.btn-primary {
  display: inline-block;
  margin-top: 0.5rem;
  font-weight: 600;
  font-size: 0.9rem;
  padding: 0.7rem 1.4rem;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--color-accent), #a6853a);
  color: #0f1210;
  text-decoration: none;
}

.btn-primary:hover {
  filter: brightness(1.08);
  text-decoration: none;
}

.faq h2 {
  margin: 0 0 1.25rem;
  font-size: 1.5rem;
  font-weight: 400;
}

.faq-item {
  padding: 1.25rem 0;
  border-top: 1px solid var(--color-border);
}

.faq-item:last-child {
  border-bottom: 1px solid var(--color-border);
}

.faq-item h3 {
  margin: 0 0 0.45rem;
  font-family: var(--font-body);
  font-size: 0.95rem;
  font-weight: 600;
}

.faq-item p {
  margin: 0;
  font-size: 0.9rem;
  color: var(--color-text-muted);
  line-height: 1.7;
  font-weight: 300;
}
</style>
