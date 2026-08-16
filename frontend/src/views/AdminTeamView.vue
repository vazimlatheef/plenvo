<template>
  <div class="app-page">
    <div class="app-page-header">
      <h1>Team</h1>
      <button
        type="button"
        class="btn-primary"
        :disabled="!canAddMembers"
        :title="canAddMembers ? undefined : teamLimits.limit_message || undefined"
        @click="openAddModal"
      >
        <Plus :size="16" :stroke-width="2" />
        Add team member
      </button>
    </div>

    <p v-if="teamLimits.limit_message && !canAddMembers" class="error-line">
      {{ teamLimits.limit_message }}
      <RouterLink to="/app/account" class="inline-upgrade">Open Account</RouterLink>
    </p>

    <p v-if="loading" class="muted-line">Loading team…</p>
    <p v-else-if="error" class="error-line">{{ error }}</p>

    <div v-else-if="rows.length === 0" class="empty-panel">
      <p>No team members yet — add someone with name and email (no account needed)</p>
      <button type="button" class="btn-primary" :disabled="!canAddMembers" @click="openAddModal">
        <Plus :size="16" :stroke-width="2" />
        Add team member
      </button>
      <p v-if="!canAddMembers && teamLimits.limit_message" class="error-line" style="margin-top: 0.75rem">
        {{ teamLimits.limit_message }}
      </p>
    </div>

    <ul v-else class="dense-list">
      <li v-for="row in rows" :key="row.key" class="dense-row team-row">
        <span
          class="avatar avatar--lg"
          :class="`avatar-tone-${avatarTone(row.seed)}`"
        >
          {{ getInitials(row.name) }}
        </span>
        <div class="dense-row__meta team-meta">
          <span class="dense-row__title">{{ row.name }}</span>
          <span class="team-sub">
            {{ row.role }}{{ row.company ? ` · ${row.company}` : '' }} · {{ row.email }}
          </span>
        </div>
        <div class="team-actions">
          <span v-if="row.hasAccount" class="team-badge">On Plenvo</span>
          <template v-else-if="row.contactId">
            <button
              type="button"
              class="btn-outline btn-sm"
              :disabled="invitingId === row.contactId"
              @click="inviteContact(row)"
            >
              {{ invitingId === row.contactId ? 'Sending…' : 'Invite to Plenvo' }}
            </button>
          </template>
          <span class="dense-row__due">{{ row.meta }}</span>
        </div>
      </li>
    </ul>

    <p v-if="actionError" class="error-line">{{ actionError }}</p>
    <p v-if="actionSuccess" class="success-line">{{ actionSuccess }}</p>

    <div v-if="showAddModal" class="modal-overlay" @click.self="cancelAdd">
      <div class="modal-panel">
        <button type="button" class="modal-close" aria-label="Close" @click="cancelAdd">
          <X :size="18" :stroke-width="1.75" />
        </button>
        <h2>Add team member</h2>
        <p class="app-lede" style="margin-bottom: 1rem">
          Name and email required. Role, company, and LinkedIn are optional — no Plenvo account needed.
        </p>
        <form class="field-stack" @submit.prevent="addContact">
          <label>
            Full name *
            <input v-model="form.name" type="text" required maxlength="200" placeholder="e.g. John Smith" />
          </label>
          <label>
            Email *
            <input v-model="form.email" type="email" required maxlength="150" placeholder="john@company.com" />
          </label>
          <label>
            Role
            <select v-model="form.role">
              <option v-for="r in roleOptions" :key="r" :value="r">{{ r }}</option>
            </select>
          </label>
          <label>
            Company
            <input v-model="form.company" type="text" maxlength="200" placeholder="Optional" />
          </label>
          <label>
            LinkedIn URL
            <input
              v-model="form.linkedin_url"
              type="url"
              maxlength="2048"
              placeholder="https://linkedin.com/in/… (optional)"
            />
            <span v-if="formLinkedInError" class="error-line" style="margin-top: 0.25rem">{{ formLinkedInError }}</span>
          </label>
          <p v-if="formError" class="error-line">{{ formError }}</p>
          <p v-if="!canAddMembers && teamLimits.limit_message" class="error-line">{{ teamLimits.limit_message }}</p>
          <div class="modal-actions">
            <button type="button" class="btn-outline" :disabled="saving" @click="cancelAdd">Cancel</button>
            <button
              type="submit"
              class="btn-primary"
              :disabled="saving || !!formLinkedInError || !canAddMembers"
            >
              {{ saving ? 'Saving…' : 'Add team member' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <div v-if="showTeamSizeModal" class="modal-overlay" @click.self="cancelTeamSize">
      <div class="modal-panel">
        <button type="button" class="modal-close" aria-label="Close" @click="cancelTeamSize">
          <X :size="18" :stroke-width="1.75" />
        </button>
        <h2>How big is your team?</h2>
        <p class="app-lede" style="margin-bottom: 1rem">Asked once, the first time you invite someone.</p>
        <form class="field-stack" @submit.prevent="confirmTeamSizeInvite">
          <div class="radio-row">
            <label v-for="opt in teamSizeOptions" :key="opt.value" class="radio-opt">
              <input v-model="pendingTeamSize" type="radio" :value="opt.value" required />
              {{ opt.label }}
            </label>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-outline" @click="cancelTeamSize">Cancel</button>
            <button type="submit" class="btn-primary" :disabled="!pendingTeamSize || invitingId">
              Continue
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Plus, X } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import { apiJson } from '@/api/client'
import { user } from '@/composables/session'
import { avatarTone, getInitials } from '@/utils/ui'

const roleOptions = ['Member', 'Manager', 'Contractor', 'Client', 'Other']

const teamSizeOptions = [
  { value: '1', label: 'Just me' },
  { value: '2-5', label: '2–5' },
  { value: '6-20', label: '6–20' },
  { value: '20+', label: '20+' },
]

const contacts = ref([])
const employees = ref([])
const loading = ref(true)
const error = ref('')
const actionError = ref('')
const actionSuccess = ref('')
const teamLimits = ref({
  can_add_members: true,
  limit_message: null,
  member_limit: null,
  member_count: 0,
  plan_tier: 'team',
})

const showAddModal = ref(false)
const form = ref({ name: '', email: '', role: 'Member', company: '', linkedin_url: '' })
const saving = ref(false)
const formError = ref('')

const LINKEDIN_RE = /^(https?:\/\/)?(www\.)?linkedin\.com\/in\/[\w\-.%]+\/?$/i
const formLinkedInError = computed(() => {
  const v = (form.value.linkedin_url || '').trim()
  if (!v) return ''
  return LINKEDIN_RE.test(v) ? '' : 'LinkedIn URL must look like https://linkedin.com/in/your-profile'
})

const canAddMembers = computed(() => teamLimits.value?.can_add_members !== false)

const invitingId = ref(null)
const showTeamSizeModal = ref(false)
const pendingInviteContactId = ref(null)
const pendingTeamSize = ref('')

const needsTeamSize = computed(() => !user.value?.team_size)

const rows = computed(() => {
  const list = []
  const contactEmails = new Set()

  for (const c of contacts.value) {
    contactEmails.add((c.email || '').toLowerCase())
    list.push({
      key: `c-${c.id}`,
      contactId: c.id,
      seed: c.id || c.email,
      name: c.name || c.email,
      email: c.email,
      role: c.role || 'Member',
      company: c.company || '',
      hasAccount: !!c.user_id,
      meta: c.user_id
        ? c.invited_at
          ? `Invited ${formatDate(c.invited_at)}`
          : 'Linked account'
        : `Added ${formatDate(c.created_at)}`,
    })
  }

  for (const emp of employees.value) {
    const email = (emp.email || '').toLowerCase()
    if (contactEmails.has(email)) continue
    list.push({
      key: `u-${emp.id}`,
      contactId: null,
      seed: emp.id || emp.email,
      name: emp.full_name || emp.email,
      email: emp.email,
      role: emp.job_title || emp.position || 'Employee',
      company: emp.company_name || '',
      hasAccount: true,
      meta: `Joined ${formatDate(emp.created_at)}`,
    })
  }

  return list
})

function formatDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

async function loadTeamLimits() {
  try {
    const limits = await apiJson('/api/v1/organisations/me/team-limits')
    teamLimits.value = limits || teamLimits.value
  } catch (err) {
    console.error('[AdminTeam] failed to load team limits', err)
  }
}

async function loadTeam() {
  try {
    loading.value = true
    error.value = ''
    const [c, e] = await Promise.all([
      apiJson('/api/v1/contacts'),
      apiJson('/api/v1/users?role=employee').catch(() => []),
      loadTeamLimits(),
    ])
    contacts.value = Array.isArray(c) ? c : []
    employees.value = Array.isArray(e) ? e : []
  } catch (err) {
    console.error('[AdminTeam] load failed', err)
    error.value = err.message || 'Failed to load team members'
  } finally {
    loading.value = false
  }
}

function openAddModal() {
  if (!canAddMembers.value) {
    actionError.value = teamLimits.value?.limit_message || 'Team member limit reached.'
    return
  }
  form.value = { name: '', email: '', role: 'Member', company: '', linkedin_url: '' }
  formError.value = ''
  showAddModal.value = true
}

function cancelAdd() {
  showAddModal.value = false
  formError.value = ''
}

async function addContact() {
  if (!form.value.name.trim() || !form.value.email.trim()) return
  if (formLinkedInError.value) return
  if (!canAddMembers.value) {
    formError.value = teamLimits.value?.limit_message || 'Team member limit reached.'
    return
  }
  saving.value = true
  formError.value = ''
  try {
    const created = await apiJson('/api/v1/contacts', {
      method: 'POST',
      body: JSON.stringify({
        name: form.value.name.trim(),
        email: form.value.email.trim().toLowerCase(),
        role: form.value.role,
        company: form.value.company.trim() || null,
        linkedin_url: form.value.linkedin_url.trim() || null,
      }),
    })
    contacts.value = [created, ...contacts.value.filter((c) => c.id !== created.id)]
    await loadTeamLimits()
    cancelAdd()
    actionSuccess.value = `Added ${created.name}`
    setTimeout(() => {
      actionSuccess.value = ''
    }, 2500)
  } catch (err) {
    console.error('[AdminTeam] add contact failed', err)
    formError.value = err.message || 'Failed to add member'
    await loadTeamLimits()
  } finally {
    saving.value = false
  }
}

function inviteContact(row) {
  actionError.value = ''
  actionSuccess.value = ''
  if (needsTeamSize.value) {
    pendingInviteContactId.value = row.contactId
    pendingTeamSize.value = ''
    showTeamSizeModal.value = true
    return
  }
  sendInvite(row.contactId)
}

function cancelTeamSize() {
  showTeamSizeModal.value = false
  pendingInviteContactId.value = null
  pendingTeamSize.value = ''
}

function confirmTeamSizeInvite() {
  if (!pendingTeamSize.value || !pendingInviteContactId.value) return
  const id = pendingInviteContactId.value
  const teamSize = pendingTeamSize.value
  cancelTeamSize()
  sendInvite(id, teamSize)
}

async function sendInvite(contactId, teamSize = null) {
  invitingId.value = contactId
  actionError.value = ''
  actionSuccess.value = ''
  try {
    const body = {}
    if (teamSize) body.team_size = teamSize
    const updated = await apiJson(`/api/v1/contacts/${contactId}/invite`, {
      method: 'POST',
      body: JSON.stringify(body),
    })
    const idx = contacts.value.findIndex((c) => c.id === contactId)
    if (idx !== -1) contacts.value[idx] = updated
    else contacts.value.unshift(updated)
    if (teamSize && user.value) {
      user.value = { ...user.value, team_size: teamSize }
    }
    actionSuccess.value = `Invitation sent to ${updated.email}`
    setTimeout(() => {
      actionSuccess.value = ''
    }, 2500)
  } catch (err) {
    console.error('[AdminTeam] invite failed', err)
    actionError.value = err.message || 'Failed to send invitation'
  } finally {
    invitingId.value = null
  }
}

onMounted(loadTeam)
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

.team-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.35rem;
}

.team-badge {
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: var(--color-accent, #c4a35a);
}

.btn-sm {
  padding: 0.35rem 0.7rem;
  font-size: 0.78rem;
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
  margin: 0.75rem 0 0;
}

.inline-upgrade {
  margin-left: 0.5rem;
  color: var(--color-accent);
  text-decoration: underline;
  font-weight: 500;
}

.inline-upgrade:hover {
  filter: brightness(1.1);
}
</style>
