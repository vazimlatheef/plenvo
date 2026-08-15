<template>
  <div class="page">
    <SiteNav />

    <main class="main">
      <div class="content">
        <p class="eyebrow">About</p>
        <h1>Work and life,<br /><em class="accent">in one place.</em></h1>

        <div class="story">
          <p>
            Plenvo brings your work and life into one place. Track your own projects and goals, or
            manage a team's — tasks, deadlines, and progress, without the status-chasing meetings or
            scattered tools. Use it solo to stay organized, or invite your team to see what's assigned,
            what's done, and what's stuck, all in one view.
          </p>
        </div>

        <section class="info-block">
          <h2>What it does</h2>
          <p>
            Plan projects, assign tasks, and follow progress in a single workspace. Optional AI
            helpers turn notes into structured work. Invite teammates when you need shared visibility —
            or keep using Plenvo on your own.
          </p>
        </section>

        <section class="info-block">
          <h2>Who it’s for</h2>
          <p>
            Professionals — individuals organising their own work, and managers or team leads who need
            a clear view of assignments and delivery without adding process for its own sake.
          </p>
        </section>

        <section class="contact-block">
          <h2>Contact</h2>
          <p>Questions about Plenvo? Email us and we’ll get back to you.</p>
          <a href="mailto:hi@plenvo.io" class="btn-primary">hi@plenvo.io</a>
        </section>
      </div>
    </main>

    <SiteFooter />
  </div>
</template>

<script setup>
import SiteFooter from '@/components/SiteFooter.vue'
import SiteNav from '@/components/SiteNav.vue'
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

.story {
  margin-bottom: 2.75rem;
}

.story p {
  font-size: 1.05rem;
  color: var(--color-text-muted);
  line-height: 1.85;
  margin: 0;
  font-weight: 300;
}

.info-block {
  margin-bottom: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--color-border);
}

.info-block h2 {
  margin: 0 0 0.65rem;
  font-size: 1.35rem;
  font-weight: 400;
}

.info-block p {
  margin: 0;
  font-size: 0.95rem;
  color: var(--color-text-muted);
  line-height: 1.75;
  font-weight: 300;
}

.contact-block {
  margin-top: 3rem;
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
  margin: 0 0 1.25rem;
  font-size: 0.9rem;
  color: var(--color-text-muted);
}

.btn-primary {
  display: inline-block;
  font-weight: 600;
  font-size: 0.9rem;
  padding: 0.75rem 1.5rem;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--color-accent), #a6853a);
  color: #0f1210;
  text-decoration: none;
}

.btn-primary:hover {
  filter: brightness(1.08);
  text-decoration: none;
}
</style>
