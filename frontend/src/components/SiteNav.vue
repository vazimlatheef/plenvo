<template>
  <nav class="site-nav" aria-label="Site">
    <div class="nav-inner">
      <RouterLink to="/" class="logo" aria-label="Plenvo">
        <PlenvoLogo tag="span" variant="lockup" />
      </RouterLink>
      <div class="nav-links">
        <RouterLink to="/about" class="nav-link">About</RouterLink>
        <RouterLink to="/security" class="nav-link">Security</RouterLink>
        <RouterLink to="/support" class="nav-link">Support</RouterLink>
        <template v-if="user">
          <SiteAccountMenu />
        </template>
        <template v-else>
          <RouterLink to="/login" class="nav-link nav-link--auth">Sign in</RouterLink>
          <RouterLink to="/signup?plan=team" class="nav-cta">Start for free</RouterLink>
        </template>
      </div>
    </div>
  </nav>
</template>

<script setup>
import SiteAccountMenu from '@/components/SiteAccountMenu.vue'
import PlenvoLogo from '@/components/PlenvoLogo.vue'
import { user } from '@/composables/session'
</script>

<style scoped>
.site-nav {
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
  gap: 1rem;
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
  flex-wrap: wrap;
  gap: 0.75rem 1.5rem;
  justify-content: flex-end;
}

.nav-link {
  font-size: 0.85rem;
  color: var(--color-text-muted);
  text-decoration: none;
  transition: color 0.2s;
}

.nav-link:hover {
  color: var(--color-text);
  text-decoration: none;
}

.nav-link.router-link-active {
  color: var(--color-accent);
}

.nav-cta {
  font-size: 0.85rem;
  font-weight: 600;
  padding: 0.5rem 1.25rem;
  border-radius: 999px;
  background: var(--color-accent);
  color: #0f1210;
  text-decoration: none;
}

.nav-cta:hover {
  filter: brightness(1.1);
  text-decoration: none;
}

@media (max-width: 640px) {
  .nav-links .nav-link:not(.nav-link--auth):not(.router-link-active) {
    display: none;
  }
  .nav-links .nav-link.router-link-active {
    display: inline;
  }
  .nav-link--auth {
    display: inline-flex !important;
  }
}
</style>
