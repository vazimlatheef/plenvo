<template>
  <div class="shell" :class="{ 'shell--admin': isAdmin }">
    <AdminSidebar v-if="isAdmin" :mobile-open="sidebarOpen" @close="sidebarOpen = false" />

    <div class="shell-body">
      <PlanRestrictionBanner v-if="user" />
      <header v-if="isAdmin" class="admin-topbar">
        <button type="button" class="menu-btn" aria-label="Open menu" @click="sidebarOpen = true">
          <Menu :size="20" :stroke-width="1.75" />
        </button>
        <RouterLink to="/" class="topbar-brand" aria-label="Plenvo home">
          <PlenvoLogo tag="span" variant="icon" compact />
        </RouterLink>
        <span class="topbar-title">{{ pageTitle }}</span>
      </header>
      <AppHeader v-else />

      <main class="main" :class="{ 'main--admin': isAdmin }">
        <router-view v-slot="{ Component }">
          <Transition name="page" mode="out-in">
            <component :is="Component" />
          </Transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup>
import { Menu } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import AdminSidebar from '@/components/AdminSidebar.vue'
import AppHeader from '@/components/AppHeader.vue'
import PlanRestrictionBanner from '@/components/PlanRestrictionBanner.vue'
import PlenvoLogo from '@/components/PlenvoLogo.vue'
import { loadPlanAccess } from '@/composables/useWriteAccess'
import { user } from '@/composables/session'
import { maybeCheckOverdueTasks } from '@/services/overdueNotifications'
import { maybeCheckTrialWarning } from '@/services/trialNotifications'

const route = useRoute()
const sidebarOpen = ref(false)

const isAdmin = computed(() => user.value?.role === 'admin')

const pageTitle = computed(() => route.meta?.title || 'Plenvo')

watch(
  () => route.fullPath,
  () => {
    sidebarOpen.value = false
  },
)

onMounted(() => {
  maybeCheckOverdueTasks()
  maybeCheckTrialWarning()
  if (user.value) loadPlanAccess()
})
</script>

<style scoped>
.shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: radial-gradient(120% 80% at 10% 0%, rgba(196, 163, 90, 0.08), transparent 45%),
    var(--color-bg);
}

.shell--admin {
  flex-direction: row;
  align-items: stretch;
}

.shell-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.admin-topbar {
  display: none;
  align-items: center;
  gap: 0.75rem;
  padding: 0.85rem 1.1rem;
  border-bottom: 1px solid var(--color-border);
  background: rgba(15, 18, 16, 0.92);
  position: sticky;
  top: 0;
  z-index: 20;
}

.menu-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text);
  cursor: pointer;
}

.topbar-brand {
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
}

.topbar-title {
  font-family: var(--font-display);
  font-size: 1.15rem;
  color: var(--color-text);
}

.main {
  flex: 1;
  width: 100%;
  max-width: 1120px;
  margin: 0 auto;
  padding: 1.5rem 1.25rem 3rem;
}

.main--admin {
  max-width: 1180px;
  padding: 1.75rem 1.5rem 3rem;
}

@media (max-width: 900px) {
  .shell--admin .admin-topbar {
    display: flex;
  }
}
</style>
