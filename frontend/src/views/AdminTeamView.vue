<template>
  <div class="app-page">
    <div class="app-page-header">
      <h1>Team</h1>
      <button type="button" class="btn-primary" @click="showInviteModal = true">+ Invite</button>
    </div>

    <p v-if="loading" class="muted-line">Loading team…</p>
    <p v-else-if="error" class="error-line">{{ error }}</p>

    <div v-else-if="employees.length === 0" class="empty-panel">
      <p>No team members yet — invite the first one</p>
      <button type="button" class="btn-primary" @click="showInviteModal = true">Invite employee</button>
    </div>

    <ul v-else class="dense-list">
      <li v-for="emp in employees" :key="emp.id" class="dense-row team-row">
        <span
          class="avatar avatar--lg"
          :class="`avatar-tone-${avatarTone(emp.id || emp.email)}`"
        >
          {{ getInitials(emp.full_name || emp.email) }}
        </span>
        <div class="dense-row__meta team-meta">
          <span class="dense-row__title">{{ emp.full_name }}</span>
          <span class="team-sub">{{ emp.position || 'Employee' }} · {{ emp.email }}</span>
        </div>
        <span class="dense-row__due">Joined {{ formatDate(emp.created_at) }}</span>
      </li>
    </ul>

    <div v-if="showInviteModal" class="modal-overlay" @click.self="cancelInvite">
      <div class="modal-panel">
        <h2>Invite employee</h2>
        <p class="app-lede" style="margin-bottom: 1rem">
          They'll receive login credentials by email.
        </p>
        <form class="field-stack" @submit.prevent="inviteEmployee">
          <div v-if="needsTeamSize" class="team-size-block">
            <span class="team-size-label">How big is your team? *</span>
            <p class="field-hint">Asked once, the first time you invite someone.</p>
            <div class="radio-row">
              <label v-for="opt in teamSizeOptions" :key="opt.value" class="radio-opt">
                <input v-model="invite.team_size" type="radio" :value="opt.value" required />
                {{ opt.label }}
              </label>
            </div>
          </div>
          <label>
            Full name *
            <input v-model="invite.name" type="text" required maxlength="100" placeholder="e.g. John Smith" />
          </label>
          <label>
            Email *
            <input v-model="invite.email" type="email" required maxlength="150" placeholder="john@company.com" />
          </label>
          <label>
            Position
            <input v-model="invite.position" type="text" maxlength="100" placeholder="e.g. Marketing Manager" />
          </label>
          <p v-if="inviteError" class="error-line">{{ inviteError }}</p>
          <p v-if="inviteSuccess" class="success-line">{{ inviteSuccess }}</p>
          <div class="modal-actions">
            <button type="button" class="btn-outline" :disabled="inviting" @click="cancelInvite">Cancel</button>
            <button
              type="submit"
              class="btn-primary"
              :disabled="inviting || (needsTeamSize && !invite.team_size)"
            >
              {{ inviting ? 'Sending…' : 'Send invitation' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

import { apiJson } from '@/api/client'
import { user } from '@/composables/session'
import { avatarTone, getInitials } from '@/utils/ui'

const teamSizeOptions = [
  { value: '1', label: 'Just me' },
  { value: '2-5', label: '2–5' },
  { value: '6-20', label: '6–20' },
  { value: '20+', label: '20+' },
]

const employees = ref([])
const loading = ref(true)
const error = ref('')

const showInviteModal = ref(false)
const invite = ref({ name: '', email: '', position: '', team_size: '' })
const inviting = ref(false)
const inviteError = ref('')
const inviteSuccess = ref('')

const needsTeamSize = computed(() => !user.value?.team_size)

function formatDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

async function fetchEmployees() {
  try {
    loading.value = true
    error.value = ''
    employees.value = await apiJson('/api/v1/users?role=employee')
  } catch (err) {
    console.error('[AdminTeam] load failed', err)
    error.value = err.message || 'Failed to load team members'
  } finally {
    loading.value = false
  }
}

async function inviteEmployee() {
  if (!invite.value.name.trim() || !invite.value.email.trim()) return
  if (needsTeamSize.value && !invite.value.team_size) return

  try {
    inviting.value = true
    inviteError.value = ''
    inviteSuccess.value = ''
    const body = {
      name: invite.value.name.trim(),
      email: invite.value.email.trim().toLowerCase(),
      position: invite.value.position.trim() || null,
    }
    if (needsTeamSize.value) body.team_size = invite.value.team_size

    const created = await apiJson('/api/v1/invite', {
      method: 'POST',
      body: JSON.stringify(body),
    })
    employees.value.unshift(created)
    if (needsTeamSize.value && user.value) {
      user.value = { ...user.value, team_size: invite.value.team_size }
    }
    inviteSuccess.value = `Invitation sent to ${invite.value.email}`
    setTimeout(() => cancelInvite(), 1600)
  } catch (err) {
    console.error('[AdminTeam] invite failed', err)
    inviteError.value = err.message || 'Failed to send invitation'
  } finally {
    inviting.value = false
  }
}

function cancelInvite() {
  showInviteModal.value = false
  invite.value = { name: '', email: '', position: '', team_size: '' }
  inviteError.value = ''
  inviteSuccess.value = ''
}

onMounted(fetchEmployees)
</script>

<style scoped>
.team-row {
  grid-template-columns: 36px minmax(0, 1fr) auto;
}

.team-meta {
  flex-direction: column;
  align-items: flex-start;
  gap: 0.15rem;
}

.team-sub {
  font-size: 0.78rem;
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.team-size-block {
  margin-bottom: 0.25rem;
}

.team-size-label {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--color-text-muted);
}

.field-hint {
  margin: 0.25rem 0 0.5rem;
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.radio-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.radio-opt {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.9rem;
  color: var(--color-text);
  text-transform: none;
  letter-spacing: normal;
}

.success-line {
  color: var(--status-done);
  font-size: 0.9rem;
  margin: 0;
}
</style>
