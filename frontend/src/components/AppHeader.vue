<template>
  <header class="header">
    <div class="inner">
      <RouterLink :to="homeLink" class="brand">
        <span class="mark">TeamOS</span>
        <span class="tagline">
          <span class="tag">Training</span>
          <span class="sub">See who’s done · Less chasing</span>
        </span>
      </RouterLink>
      <nav v-if="user" class="nav" aria-label="Main">
        <RouterLink v-for="link in navLinks" :key="link.to" :to="link.to" class="nav-link">
          {{ link.label }}
        </RouterLink>
      </nav>
      <div class="right">
        <span v-if="user" class="who">{{ user.full_name || user.email }}</span>
        <button v-if="user" type="button" class="logout" @click="onLogout">Log out</button>
        <RouterLink v-else to="/login" class="signin">Sign in</RouterLink>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import { logoutAndRedirect, user } from '@/composables/session'

const router = useRouter()

const homeLink = computed(() => (user.value?.role === 'admin' ? '/admin' : '/assignments'))

const navLinks = computed(() => {
  if (!user.value) return []
  if (user.value.role === 'admin') {
    return [
      { to: '/admin', label: 'Dashboard' },
      { to: '/admin/trainings/new', label: 'New training' },
      { to: '/admin/assign', label: 'Assign' },
      { to: '/assignments', label: 'All assignments' },
    ]
  }
  return [{ to: '/assignments', label: 'My assignments' }]
})

function onLogout() {
  logoutAndRedirect(router)
}
</script>

<style scoped>
.header {
  border-bottom: 1px solid var(--color-border);
  background: rgba(15, 18, 16, 0.85);
  backdrop-filter: blur(12px);
  position: sticky;
  top: 0;
  z-index: 10;
}

.inner {
  max-width: 1120px;
  margin: 0 auto;
  padding: 0.85rem 1.25rem;
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.brand {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  text-decoration: none;
  color: var(--color-text);
}

.brand:hover {
  text-decoration: none;
}

.mark {
  font-family: var(--font-display);
  font-size: 1.35rem;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.tagline {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.tagline .tag {
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: var(--color-accent);
  font-weight: 500;
}

.sub {
  font-size: 0.62rem;
  font-weight: 300;
  color: var(--color-text-muted);
  letter-spacing: 0.03em;
  line-height: 1.3;
}

.nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem 1rem;
  flex: 1;
}

.nav-link {
  font-size: 0.875rem;
  font-weight: 400;
  color: var(--color-text-muted);
  text-decoration: none;
}

.nav-link:hover {
  color: var(--color-text);
  text-decoration: none;
}

.nav-link.router-link-active {
  color: var(--color-accent);
}

.right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.who {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.logout {
  font-family: var(--font-body);
  font-size: 0.8rem;
  font-weight: 500;
  padding: 0.4rem 0.85rem;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  background: transparent;
  color: var(--color-text);
  cursor: pointer;
}

.logout:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.signin {
  font-size: 0.8rem;
  font-weight: 500;
  padding: 0.4rem 0.85rem;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  color: var(--color-text);
  text-decoration: none;
}

.signin:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
  text-decoration: none;
}
</style>
