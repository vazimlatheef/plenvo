<template>
  <div v-if="user" class="account-wrap">
    <RouterLink :to="workspaceTo" class="open-app">Open workspace</RouterLink>
    <div class="user-menu" ref="menuRoot">
      <button
        type="button"
        class="user-trigger"
        :aria-expanded="menuOpen"
        aria-haspopup="menu"
        @click="menuOpen = !menuOpen"
      >
        <span class="who">{{ user.first_name || user.email }}</span>
        <span class="chev" aria-hidden="true">▾</span>
      </button>
      <div v-if="menuOpen" class="user-dropdown" role="menu">
        <RouterLink :to="workspaceTo" class="menu-item" role="menuitem" @click="menuOpen = false">
          Dashboard
        </RouterLink>
        <RouterLink to="/app/profile" class="menu-item" role="menuitem" @click="menuOpen = false">
          Profile
        </RouterLink>
        <RouterLink to="/app/account" class="menu-item" role="menuitem" @click="menuOpen = false">
          Account &amp; Subscription
        </RouterLink>
        <RouterLink to="/support" class="menu-item" role="menuitem" @click="menuOpen = false">
          Help
        </RouterLink>
        <button type="button" class="menu-item menu-item--btn" role="menuitem" @click="onLogout">
          Log out
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { appHomeRoute, logoutAndRedirect, user } from '@/composables/session'

const router = useRouter()
const menuOpen = ref(false)
const menuRoot = ref(null)

const workspaceTo = computed(() => appHomeRoute())

function onDocumentClick(event) {
  if (!menuOpen.value || !menuRoot.value) return
  if (!menuRoot.value.contains(event.target)) menuOpen.value = false
}

function onLogout() {
  menuOpen.value = false
  logoutAndRedirect(router)
}

onMounted(() => document.addEventListener('click', onDocumentClick))
onBeforeUnmount(() => document.removeEventListener('click', onDocumentClick))
</script>

<style scoped>
.account-wrap {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.open-app {
  font-size: 0.85rem;
  font-weight: 600;
  padding: 0.5rem 1.15rem;
  border-radius: 999px;
  background: var(--color-accent);
  color: #0f1210;
  text-decoration: none;
  white-space: nowrap;
}

.open-app:hover {
  filter: brightness(1.1);
  text-decoration: none;
}

.user-menu {
  position: relative;
}

.user-trigger {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  max-width: 10rem;
  padding: 0.4rem 0.7rem;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font-family: inherit;
}

.user-trigger:hover {
  border-color: var(--color-accent);
}

.who {
  font-size: 0.82rem;
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chev {
  font-size: 0.65rem;
  color: var(--color-text-muted);
}

.user-dropdown {
  position: absolute;
  right: 0;
  top: calc(100% + 0.4rem);
  min-width: 200px;
  padding: 0.35rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.35);
  z-index: 60;
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

@media (max-width: 640px) {
  .open-app {
    padding: 0.45rem 0.85rem;
    font-size: 0.8rem;
  }
}
</style>
