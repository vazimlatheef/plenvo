<template>
  <footer class="site-footer">
    <div class="footer-inner">
      <RouterLink to="/" class="logo">Plenvo</RouterLink>
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
</template>

<style scoped>
.site-footer {
  border-top: 1px solid var(--color-border);
  padding: 1.5rem;
  margin-top: auto;
}

.footer-inner {
  max-width: 1160px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.logo {
  font-family: var(--font-display);
  font-size: 1.2rem;
  color: var(--color-accent);
  text-decoration: none;
  letter-spacing: 0.04em;
}

.logo:hover {
  color: var(--color-accent);
  text-decoration: none;
}

.footer-links {
  display: flex;
  flex-wrap: wrap;
  gap: 1.25rem 1.5rem;
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

.footer-links a.router-link-active {
  color: var(--color-accent);
}

.copy {
  font-size: 0.78rem;
  color: var(--color-text-muted);
}
</style>
