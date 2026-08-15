<template>
  <div class="page">
    <SiteNav />

    <main class="main">
      <div class="content">
        <p class="eyebrow">Security</p>
        <h1>How we protect<br /><em class="accent">your data.</em></h1>
        <p class="lead">
          A factual overview of how Plenvo handles encryption, access, hosting, and privacy.
          We avoid claims we cannot substantiate.
        </p>

        <div class="sec-list">
          <article v-for="s in sections" :key="s.title" class="sec-item">
            <h3>{{ s.title }}</h3>
            <p>{{ s.desc }}</p>
          </article>
        </div>

        <section class="contact-block">
          <h2>Security questions</h2>
          <p>Email <a href="mailto:hi@plenvo.io">hi@plenvo.io</a> and we will respond as promptly as we can.</p>
        </section>
      </div>
    </main>

    <SiteFooter />
  </div>
</template>

<script setup>
import SiteFooter from '@/components/SiteFooter.vue'
import SiteNav from '@/components/SiteNav.vue'

const sections = [
  {
    title: 'Encryption in transit',
    desc: 'Traffic between your browser and Plenvo is protected with TLS. API requests are authenticated with short-lived tokens.',
  },
  {
    title: 'Encryption at rest',
    desc: 'Application data is stored in a managed PostgreSQL database with encryption at rest provided by the hosting platform.',
  },
  {
    title: 'Organisation-level isolation',
    desc: 'Each organisation’s projects, tasks, team members, and notes are scoped to that organisation. Users can only access data for organisations they belong to.',
  },
  {
    title: 'Hosting',
    desc: 'Plenvo’s application and database run on Render with PostgreSQL. Infrastructure security controls (network isolation, platform monitoring, and backups) follow Render’s standard practices for those services.',
  },
  {
    title: 'GDPR',
    desc: 'We process personal data to provide the Plenvo service. You can request access, correction, or deletion of your account data by contacting hi@plenvo.io. We do not sell personal data. For details, see our Privacy Policy.',
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
  max-width: 720px;
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
  margin: 0 0 1.25rem;
}

.accent {
  color: var(--color-accent);
  font-style: italic;
}

.lead {
  font-size: 1rem;
  color: var(--color-text-muted);
  line-height: 1.75;
  margin: 0 0 2.75rem;
  font-weight: 300;
  max-width: 560px;
}

.sec-list {
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  overflow: hidden;
  margin-bottom: 3rem;
}

.sec-item {
  padding: 1.5rem 1.6rem;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface);
}

.sec-item:last-child {
  border-bottom: none;
}

.sec-item h3 {
  margin: 0 0 0.45rem;
  font-family: var(--font-body);
  font-size: 0.95rem;
  font-weight: 600;
}

.sec-item p {
  margin: 0;
  font-size: 0.9rem;
  color: var(--color-text-muted);
  line-height: 1.7;
  font-weight: 300;
}

.contact-block {
  padding: 2rem;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  text-align: center;
}

.contact-block h2 {
  margin: 0 0 0.5rem;
  font-size: 1.5rem;
  font-weight: 400;
}

.contact-block p {
  margin: 0;
  font-size: 0.9rem;
  color: var(--color-text-muted);
}

.contact-block a {
  color: var(--color-accent);
}
</style>
