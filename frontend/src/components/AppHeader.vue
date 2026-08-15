<template>
  <header class="header">
    <div class="inner">
      <RouterLink :to="homeLink" class="brand">
        <span class="mark">Plenvo</span>
        <span class="tagline">
          <span class="tag">Training</span>
          <span class="sub">See who's done · Less chasing</span>
        </span>
      </RouterLink>
      <nav v-if="user" class="nav" aria-label="Main">
        <RouterLink v-for="link in navLinks" :key="link.to" :to="link.to" class="nav-link">
          {{ link.label }}
        </RouterLink>
      </nav>
      <div class="right">
        <div v-if="user" class="user-menu" ref="menuRoot">
          <button
            type="button"
            class="user-trigger"
            :aria-expanded="menuOpen"
            aria-haspopup="menu"
            @click="menuOpen = !menuOpen"
          >
            <span class="who">{{ user.full_name || user.email }}</span>
            <span class="chev" aria-hidden="true">▾</span>
          </button>
          <div v-if="menuOpen" class="user-dropdown" role="menu">
            <RouterLink to="/app/profile" class="menu-item" role="menuitem" @click="menuOpen = false">
              Profile
            </RouterLink>
            <RouterLink to="/support" class="menu-item" role="menuitem" @click="menuOpen = false">
              Help
            </RouterLink>
            <button type="button" class="menu-item menu-item--btn" role="menuitem" @click="onLogout">
              Log out
            </button>
          </div>
        </div>
        <RouterLink v-else to="/login" class="signin">Sign in</RouterLink>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { logoutAndRedirect, user } from '@/composables/session'

const router = useRouter()
const menuOpen = ref(false)
const menuRoot = ref(null)

const homeLink = computed(() => (user.value?.role === 'admin' ? '/app/admin' : '/app/assignments'))

const navLinks = computed(() => {
  if (!user.value) return []
  if (user.value.role === 'admin') {
    return [
      { to: '/app/admin', label: 'Dashboard' },
      { to: '/app/projects', label: 'Projects' },
      { to: '/app/team', label: 'Team' },
      { to: '/app/admin/ai-terminal', label: 'AI Terminal' },
    ]
  }
  return [
    { to: '/app/assignments', label: 'My assignments' },
    { to: '/app/tasks', label: 'My tasks' },
  ]
})

function onDocumentClick(event) {
  if (!menuOpen.value || !menuRoot.value) return
  if (!menuRoot.value.contains(event.target)) menuOpen.value = false
}

function onLogout() {
  menuOpen.value = false
  logoutAndRedirect(router)
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick)
})
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

.user-menu {
  position: relative;
}

.user-trigger {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  max-width: 200px;
  padding: 0.4rem 0.7rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: transparent;
  color: var(--color-text);
  cursor: pointer;
  font-family: inherit;
}

.user-trigger:hover {
  border-color: var(--color-accent);
}

.who {
  font-size: 0.8rem;
  color: var(--color-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chev {
  font-size: 0.7rem;
  color: var(--color-text-muted);
}

.user-dropdown {
  position: absolute;
  right: 0;
  top: calc(100% + 0.4rem);
  min-width: 160px;
  padding: 0.35rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.35);
  z-index: 30;
}

.menu-item {
  display: block;
  width: 100%;
  padding: 0.55rem 0.7rem;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--color-text);
  font-size: 0.85rem;
  text-align: left;
  text-decoration: none;
  cursor: pointer;
  font-family: inherit;
}

.menu-item:hover {
  background: rgba(196, 163, 90, 0.12);
  color: var(--color-accent);
  text-decoration: none;
}

.menu-item--btn {
  color: var(--color-text-muted);
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
