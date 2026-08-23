<template>
  <aside class="sidebar" :class="{ 'sidebar--open': mobileOpen }">
    <div class="sidebar-brand">
      <RouterLink to="/" class="brand-link" @click="closeMobile">
        <PlenvoLogo tag="span" variant="lockup" />
      </RouterLink>
      <button type="button" class="sidebar-close" aria-label="Close menu" @click="closeMobile">
        <X :size="18" :stroke-width="1.75" />
      </button>
    </div>

    <nav class="sidebar-nav" aria-label="Main">
      <template v-for="item in navItems" :key="item.to">
        <div
          v-if="isTeamNavItem(item) && isPersonalPlan"
          class="nav-item nav-item--locked"
          aria-disabled="true"
        >
          <component :is="item.icon" class="nav-icon" :size="18" :stroke-width="1.75" />
          <div class="nav-locked-body">
            <span class="nav-locked-label">{{ item.label }}</span>
            <RouterLink to="/app/account" class="nav-upgrade-hint" @click="closeMobile">
              Upgrade to Team to add members, see performance, and assign training/tasks
            </RouterLink>
          </div>
        </div>
        <RouterLink
          v-else
          :to="item.to"
          class="nav-item"
          :class="{ 'router-link-active': isNavActive(item) }"
          active-class=""
          @click="closeMobile"
        >
          <component :is="item.icon" class="nav-icon" :size="18" :stroke-width="1.75" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </template>
    </nav>

    <div class="sidebar-section">
      <p class="section-label">Quick actions</p>
      <div
        v-if="writeRestricted"
        class="nav-item nav-item--action nav-item--locked"
        aria-disabled="true"
        :title="writeDisabledTitle"
      >
        <FolderPlus class="nav-icon" :size="18" :stroke-width="1.75" />
        <span>New Project</span>
      </div>
      <RouterLink v-else to="/app/projects" class="nav-item nav-item--action" @click="closeMobile">
        <FolderPlus class="nav-icon" :size="18" :stroke-width="1.75" />
        <span>New Project</span>
      </RouterLink>
      <RouterLink to="/app/team" class="nav-item nav-item--action" @click="closeMobile">
        <UserPlus class="nav-icon" :size="18" :stroke-width="1.75" />
        <span>Add Team Member</span>
      </RouterLink>
      <RouterLink to="/app/admin/ai-terminal" class="nav-item nav-item--action" @click="closeMobile">
        <Zap class="nav-icon" :size="18" :stroke-width="1.75" />
        <span>Plenvo AI</span>
      </RouterLink>
    </div>

    <div class="sidebar-footer">
      <RouterLink to="/app/profile" class="nav-item" @click="closeMobile">
        <UserRound class="nav-icon" :size="18" :stroke-width="1.75" />
        <span>Profile</span>
      </RouterLink>
      <RouterLink to="/app/account" class="nav-item" @click="closeMobile">
        <CreditCard class="nav-icon" :size="18" :stroke-width="1.75" />
        <span>Account &amp; Subscription</span>
      </RouterLink>
      <RouterLink to="/support" class="nav-item" @click="closeMobile">
        <CircleHelp class="nav-icon" :size="18" :stroke-width="1.75" />
        <span>Help</span>
      </RouterLink>
      <button type="button" class="nav-item nav-item--btn" @click="onLogout">
        <LogOut class="nav-icon" :size="18" :stroke-width="1.75" />
        <span>Log out</span>
      </button>
      <p v-if="user" class="sidebar-user">{{ user.first_name || user.email }}</p>
    </div>
  </aside>

  <div v-if="mobileOpen" class="sidebar-backdrop" @click="closeMobile" />
</template>

<script setup>
import {
  CalendarDays,
  CircleHelp,
  CreditCard,
  FolderKanban,
  FolderPlus,
  GraduationCap,
  Home,
  LayoutDashboard,
  LogOut,
  Sparkles,
  UserPlus,
  UserRound,
  Users,
  X,
  Zap,
} from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { apiJson } from '@/api/client'
import { logoutAndRedirect, user } from '@/composables/session'
import { useWriteAccess } from '@/composables/useWriteAccess'
import PlenvoLogo from '@/components/PlenvoLogo.vue'

defineProps({
  mobileOpen: { type: Boolean, default: false },
})

const emit = defineEmits(['close'])
const router = useRouter()
const route = useRoute()

const planTier = ref(null)
const { writeRestricted, writeDisabledTitle } = useWriteAccess()

const isPersonalPlan = computed(() => planTier.value === 'personal')

const navItems = [
  { to: '/', label: 'Home', icon: Home },
  { to: '/app/admin', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/app/projects', label: 'Projects', icon: FolderKanban },
  { to: '/app/calendar', label: 'Calendar', icon: CalendarDays },
  { to: '/app/team', label: 'Team', icon: Users },
  {
    to: '/app/admin/trainings',
    label: 'Training',
    icon: GraduationCap,
    matchPrefix: '/app/admin/trainings',
  },
  { to: '/app/admin/ai-terminal', label: 'Plenvo AI', icon: Sparkles },
]

function isTeamNavItem(item) {
  return item.to === '/app/team'
}

async function loadPlanTier() {
  try {
    const limits = await apiJson('/api/v1/organisations/me/team-limits')
    planTier.value = limits?.plan_tier || null
  } catch {
    planTier.value = null
  }
}

onMounted(() => {
  loadPlanTier()
})

function isNavActive(item) {
  const path = route.path
  if (item.matchPrefix) {
    return path === item.matchPrefix || path.startsWith(`${item.matchPrefix}/`)
  }
  if (item.to === '/app/admin') {
    return path === item.to
  }
  return path === item.to || path.startsWith(`${item.to}/`)
}

function closeMobile() {
  emit('close')
}

function onLogout() {
  closeMobile()
  logoutAndRedirect(router)
}
</script>

<style scoped>
.sidebar {
  width: 248px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  padding: 1.1rem 0.85rem 1.25rem;
  background: var(--color-bg-elevated);
  border-right: 1px solid var(--color-border);
  min-height: 100vh;
  position: sticky;
  top: 0;
  align-self: flex-start;
  z-index: 40;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.35rem 0.55rem 1rem;
}

.brand-link {
  text-decoration: none;
  color: inherit;
  display: inline-flex;
}

.brand-link:hover {
  text-decoration: none;
}

.sidebar-close {
  display: none;
  width: 32px;
  height: 32px;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.sidebar-section {
  margin-top: 1.1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.section-label {
  margin: 0 0 0.45rem;
  padding: 0 0.55rem;
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.sidebar-footer {
  margin-top: auto;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.55rem 0.65rem;
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  text-decoration: none;
  font-size: 0.88rem;
  font-weight: 500;
  border: none;
  background: transparent;
  width: 100%;
  text-align: left;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.15s, color 0.15s;
}

.nav-item:hover {
  background: rgba(196, 163, 90, 0.1);
  color: var(--color-text);
  text-decoration: none;
}

.nav-item.router-link-active {
  background: rgba(196, 163, 90, 0.16);
  color: var(--color-accent);
}

.nav-item--action {
  color: var(--color-text);
}

.nav-item--locked {
  opacity: 0.55;
  cursor: default;
  align-items: flex-start;
}

.nav-item--locked:hover {
  background: transparent;
  color: var(--color-text-muted);
}

.nav-locked-body {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  min-width: 0;
}

.nav-locked-label {
  color: var(--color-text-muted);
  font-weight: 500;
}

.nav-upgrade-hint {
  font-size: 0.72rem;
  line-height: 1.35;
  font-weight: 400;
  color: var(--color-accent);
  text-decoration: none;
}

.nav-upgrade-hint:hover {
  text-decoration: underline;
  color: var(--color-accent);
}

.nav-icon {
  flex-shrink: 0;
  opacity: 0.9;
}

.sidebar-user {
  margin: 0.65rem 0.55rem 0;
  font-size: 0.78rem;
  color: var(--color-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-backdrop {
  display: none;
}

@media (max-width: 900px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    transform: translateX(-105%);
    transition: transform 0.2s ease;
    box-shadow: var(--shadow);
    min-height: 100%;
  }

  .sidebar--open {
    transform: translateX(0);
  }

  .sidebar-close {
    display: inline-flex;
  }

  .sidebar-backdrop {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.55);
    z-index: 35;
  }
}
</style>
