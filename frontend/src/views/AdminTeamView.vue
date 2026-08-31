<template>
  <div class="app-page">
    <div class="app-page-header">
      <h1>Team</h1>
      <RouterLink v-if="isPersonalPlan" to="/app/account" class="btn-primary">
        Upgrade to Team
      </RouterLink>
      <button
        v-else
        type="button"
        class="btn-primary"
        :disabled="!canAddMembers || writeRestricted"
        :title="writeRestricted ? writeDisabledTitle : canAddMembers ? undefined : teamLimits.limit_message || undefined"
        @click="openAddModal"
      >
        <Plus :size="16" :stroke-width="2" />
        Add team member
      </button>
    </div>

    <p v-if="!isPersonalPlan && teamLimits.limit_message && !canAddMembers" class="notice-line">
      {{ teamLimits.limit_message }}
      <RouterLink to="/app/account">Upgrade →</RouterLink>
    </p>

    <div class="team-tabs" role="tablist" aria-label="Team sections">
      <button
        type="button"
        role="tab"
        :class="['team-tab', { active: activeTab === 'members' }]"
        :aria-selected="activeTab === 'members'"
        @click="activeTab = 'members'"
      >
        Members
      </button>
      <button
        type="button"
        role="tab"
        :class="['team-tab', { active: activeTab === 'workload' }]"
        :aria-selected="activeTab === 'workload'"
        @click="activeTab = 'workload'"
      >
        Workload
      </button>
      <button
        type="button"
        role="tab"
        :class="['team-tab', { active: activeTab === 'performance' }]"
        :aria-selected="activeTab === 'performance'"
        @click="activeTab = 'performance'"
      >
        Performance
      </button>
    </div>

    <template v-if="activeTab === 'members'">
      <p v-if="loading" class="muted-line">Loading team…</p>
      <p v-else-if="error" class="error-line">{{ error }}</p>

      <div v-else-if="rows.length === 0" class="empty-panel">
        <template v-if="isPersonalPlan">
          <p>Personal is for one person. Upgrade to Team to add members.</p>
          <RouterLink to="/app/account" class="btn-primary">Upgrade to Team</RouterLink>
        </template>
        <template v-else>
          <p>Add someone with a name and email — no account needed.</p>
          <button type="button" class="btn-primary" :disabled="!canAddMembers || writeRestricted" :title="writeRestricted ? writeDisabledTitle : undefined" @click="openAddModal">
            <Plus :size="16" :stroke-width="2" />
            Add team member
          </button>
          <p v-if="!canAddMembers && teamLimits.limit_message" class="notice-line" style="margin-top: 0.75rem">
            {{ teamLimits.limit_message }}
            <RouterLink to="/app/account">Upgrade →</RouterLink>
          </p>
        </template>
      </div>

      <ul v-else class="dense-list">
        <li v-for="row in rows" :key="row.key" class="dense-row team-row">
          <span class="avatar avatar--lg" :class="`avatar-tone-${avatarTone(row.seed)}`">
            {{ getInitials(row.name) }}
          </span>
          <div class="dense-row__meta team-meta">
            <span class="dense-row__title">{{ row.name }}</span>
            <span class="team-sub">
              {{ row.role }}{{ row.teamDivision ? ` · ${row.teamDivision}` : '' }}{{ row.company ? ` · ${row.company}` : '' }} · {{ row.email }}
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
            <button
              v-if="row.contactId"
              type="button"
              class="row-icon-btn"
              aria-label="Edit member"
              :disabled="writeRestricted"
              :title="writeRestricted ? writeDisabledTitle : 'Edit member'"
              @click="openEditModal(row)"
            >
              <Pencil :size="14" :stroke-width="1.75" />
            </button>
            <button
              v-if="canDeleteRow(row)"
              type="button"
              class="row-icon-btn row-icon-btn--danger"
              aria-label="Remove member"
              :disabled="writeRestricted || deletingId === row.key"
              :title="writeRestricted ? writeDisabledTitle : 'Remove from team'"
              @click="confirmDeleteMember(row)"
            >
              <Trash2 :size="14" :stroke-width="1.75" />
            </button>
            <span class="dense-row__due">{{ row.meta }}</span>
          </div>
        </li>
      </ul>

      <p v-if="actionError" class="notice-line">{{ actionError }}</p>
      <p v-if="actionSuccess" class="success-line">{{ actionSuccess }}</p>
    </template>

    <template v-else-if="activeTab === 'workload'">
      <div v-if="!canWorkload" class="plan-gate">
        <h2>Member workload view</h2>
        <p class="app-lede">See open, overdue, and completed tasks per team member on Team and Enterprise plans.</p>
        <RouterLink to="/app/account" class="btn-primary">Upgrade plan →</RouterLink>
      </div>
      <template v-else>
        <p v-if="insightsLoading" class="muted-line">Loading workload…</p>
        <p v-else-if="insightsError" class="error-line">{{ insightsError }}</p>
        <div v-else-if="workloadRows.length === 0" class="empty-panel">
          <p>Add team members to see workload breakdowns.</p>
        </div>
        <div v-else class="insights-table-wrap">
          <table class="insights-table">
            <thead>
              <tr>
                <th>Member</th>
                <th>Open</th>
                <th>Overdue</th>
                <th>Completed</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in workloadRows" :key="row.key">
                <td>
                  <span class="insights-name">{{ row.name }}</span>
                  <span class="insights-sub">{{ row.role }}</span>
                </td>
                <td>{{ row.stats.open }}</td>
                <td :class="{ 'cell-alert': row.stats.overdue > 0 }">{{ row.stats.overdue }}</td>
                <td>{{ row.stats.completed }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <section class="priority-section">
          <h2 class="priority-heading">Team priority insights</h2>
          <p v-if="!canTeamPriority" class="priority-upsell">
            Team priority insights are available on Team and Enterprise plans.
            <RouterLink to="/app/account" class="inline-upgrade">Upgrade plan →</RouterLink>
          </p>
          <template v-else>
            <p v-if="insightsLoading" class="muted-line">Loading priority insights…</p>
            <div v-else-if="teamPriorityRows.length === 0" class="empty-panel compact">
              <p>Add team members to see priority insights.</p>
            </div>
            <div v-else class="insights-table-wrap">
              <table class="insights-table priority-table">
                <thead>
                  <tr>
                    <th>Member</th>
                    <th>Top priority task</th>
                    <th>Due</th>
                    <th>Priority</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in teamPriorityRows" :key="`p-${row.key}`">
                    <td>
                      <span class="insights-name">{{ row.name }}</span>
                      <span class="insights-sub">{{ row.role }}</span>
                    </td>
                    <td>
                      <span v-if="row.topTask" :class="{ 'cell-alert': isTaskOverdue(row.topTask) }">
                        {{ row.topTask.title }}
                      </span>
                      <span v-else class="insights-muted">No open tasks</span>
                    </td>
                    <td class="date-cell">{{ formatTaskDue(row.topTask) }}</td>
                    <td>
                      <span v-if="row.topTask" class="priority-pill" :data-p="row.topTask.priority">
                        {{ row.topTask.priority }}
                      </span>
                      <span v-else class="insights-muted">—</span>
                    </td>
                  </tr>
                </tbody>
              </table>
              <p class="insights-footnote">
                Overdue first, then due date, then priority.
              </p>
            </div>
          </template>
        </section>
      </template>
    </template>

    <template v-else-if="activeTab === 'performance'">
      <div v-if="!canPerformance" class="plan-gate">
        <h2>Performance summary</h2>
        <p class="app-lede">Review-style task breakdowns by person — available on Team and Enterprise.</p>
        <RouterLink to="/app/account" class="btn-primary">Upgrade plan →</RouterLink>
      </div>
      <template v-else>
        <div class="perf-toolbar">
          <span class="perf-label">Period</span>
          <div class="perf-filters">
            <button
              type="button"
              :class="['filter-chip', { active: perfRange === 'week' }]"
              @click="perfRange = 'week'"
            >
              This week
            </button>
            <button
              type="button"
              :class="['filter-chip', { active: perfRange === 'month' }]"
              @click="perfRange = 'month'"
            >
              This month
            </button>
          </div>
        </div>
        <p v-if="insightsLoading" class="muted-line">Loading performance summary…</p>
        <p v-else-if="insightsError" class="error-line">{{ insightsError }}</p>
        <div v-else-if="performanceRows.length === 0" class="empty-panel">
          <p>Add team members to build a performance summary.</p>
        </div>
        <div v-else class="insights-table-wrap">
          <table class="insights-table">
            <thead>
              <tr>
                <th>Member</th>
                <th>Completed</th>
                <th>Overdue</th>
                <th>Assigned (open)</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in performanceRows" :key="row.key">
                <td>
                  <span class="insights-name">{{ row.name }}</span>
                  <span class="insights-sub">{{ row.role }}</span>
                </td>
                <td>{{ row.stats.completedInPeriod }}</td>
                <td :class="{ 'cell-alert': row.stats.overdueNow > 0 }">{{ row.stats.overdueNow }}</td>
                <td>{{ row.stats.assignedOpen }}</td>
              </tr>
            </tbody>
          </table>
          <p class="insights-footnote">
            Completed counts tasks marked done in the selected period. Overdue and assigned reflect today.
          </p>
        </div>
      </template>
    </template>

    <div v-if="showEditModal" class="modal-overlay" @click.self="cancelEdit">
      <div class="modal-panel">
        <button type="button" class="modal-close" aria-label="Close" @click="cancelEdit">
          <X :size="18" :stroke-width="1.75" />
        </button>
        <h2>Edit team member</h2>
        <form class="field-stack" @submit.prevent="saveContactEdit">
          <label>
            Full name *
            <input v-model="editForm.name" type="text" required maxlength="200" />
          </label>
          <label>
            Email *
            <input v-model="editForm.email" type="email" required maxlength="150" />
          </label>
          <label>
            Role
            <select v-model="editForm.selectedRole">
              <option v-for="r in roleOptions" :key="r" :value="r">{{ r }}</option>
            </select>
          </label>
          <label v-if="editForm.selectedRole === otherRole">
            Role (other)
            <input v-model="editForm.roleOther" type="text" maxlength="200" placeholder="Describe their role" />
          </label>
          <label>
            Team / Division
            <input v-model="editForm.team_division" type="text" maxlength="200" placeholder="Optional" />
          </label>
          <label>
            Company
            <input v-model="editForm.company" type="text" maxlength="200" placeholder="Optional" />
          </label>
          <label>
            LinkedIn URL
            <input
              v-model="editForm.linkedin_url"
              type="url"
              maxlength="2048"
              placeholder="https://linkedin.com/in/… (optional)"
            />
            <span v-if="editLinkedInError" class="error-line" style="margin-top: 0.25rem">{{ editLinkedInError }}</span>
          </label>
          <p v-if="editFormError" class="notice-line">{{ editFormError }}</p>
          <div class="modal-actions">
            <button type="button" class="btn-outline" :disabled="savingEdit" @click="cancelEdit">Cancel</button>
            <button type="submit" class="btn-primary" :disabled="savingEdit || !!editLinkedInError">
              {{ savingEdit ? 'Saving…' : 'Save changes' }}
            </button>
          </div>
        </form>
      </div>
    </div>

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
            <select v-model="form.selectedRole">
              <option v-for="r in roleOptions" :key="r" :value="r">{{ r }}</option>
            </select>
          </label>
          <label v-if="form.selectedRole === otherRole">
            Role (other)
            <input v-model="form.roleOther" type="text" maxlength="200" placeholder="Describe their role" />
          </label>
          <label>
            Team / Division
            <input v-model="form.team_division" type="text" maxlength="200" placeholder="Optional" />
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
          <p v-if="formError" class="notice-line">{{ formError }}</p>
          <p v-if="!canAddMembers && teamLimits.limit_message" class="notice-line">
            {{ teamLimits.limit_message }}
            <RouterLink to="/app/account">Upgrade →</RouterLink>
          </p>
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
import { Plus, Pencil, Trash2, X } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'

import { apiJson } from '@/api/client'
import { user } from '@/composables/session'
import { useWriteAccess } from '@/composables/useWriteAccess'
import { avatarTone, getInitials } from '@/utils/ui'
import { formatTaskDue } from '@/utils/taskDue'
import {
  DEFAULT_ROLE,
  OTHER_ROLE,
  PROFESSIONAL_ROLES,
  contactRoleFromApi,
  displayProfessionalRole,
} from '@/constants/professionalRoles'
import {
  buildPerformanceRows,
  buildTeamPriorityRows,
  buildTeamRoster,
  buildWorkloadRows,
  canUsePerformanceView,
  canUseTeamPriorityInsights,
  canUseWorkloadView,
  isTaskOverdue,
} from '@/utils/taskInsights'

const roleOptions = PROFESSIONAL_ROLES
const otherRole = OTHER_ROLE

const teamSizeOptions = [
  { value: '1', label: 'Just me' },
  { value: '2-5', label: '2–5' },
  { value: '6-20', label: '6–20' },
  { value: '20+', label: '20+' },
]

const { writeRestricted, writeDisabledTitle } = useWriteAccess()

const contacts = ref([])
const employees = ref([])
const loading = ref(true)
const error = ref('')
const actionError = ref('')
const actionSuccess = ref('')
const deletingId = ref('')
const teamLimits = ref({
  can_add_members: true,
  limit_message: null,
  member_limit: null,
  member_count: 0,
  plan_tier: 'team',
  on_trial: false,
})

const activeTab = ref('members')
const tasks = ref([])
const insightsLoading = ref(false)
const insightsError = ref('')
const perfRange = ref('week')

const showAddModal = ref(false)
const form = ref({
  name: '',
  email: '',
  selectedRole: DEFAULT_ROLE,
  roleOther: '',
  team_division: '',
  company: '',
  linkedin_url: '',
})
const saving = ref(false)
const formError = ref('')

const LINKEDIN_RE = /^(https?:\/\/)?(www\.)?linkedin\.com\/in\/[\w\-.%]+\/?$/i
const formLinkedInError = computed(() => {
  const v = (form.value.linkedin_url || '').trim()
  if (!v) return ''
  return LINKEDIN_RE.test(v) ? '' : 'LinkedIn URL must look like https://linkedin.com/in/your-profile'
})

const showEditModal = ref(false)
const editingContactId = ref(null)
const editForm = ref({
  name: '',
  email: '',
  selectedRole: DEFAULT_ROLE,
  roleOther: '',
  team_division: '',
  company: '',
  linkedin_url: '',
})
const savingEdit = ref(false)
const editFormError = ref('')
const editLinkedInError = computed(() => {
  const v = (editForm.value.linkedin_url || '').trim()
  if (!v) return ''
  return LINKEDIN_RE.test(v) ? '' : 'LinkedIn URL must look like https://linkedin.com/in/your-profile'
})

const canAddMembers = computed(() => teamLimits.value?.can_add_members !== false)
const isPersonalPlan = computed(() => (teamLimits.value?.plan_tier || '').toLowerCase() === 'personal')

const canWorkload = computed(() => canUseWorkloadView(teamLimits.value))
const canPerformance = computed(() => canUsePerformanceView(teamLimits.value))
const canTeamPriority = computed(() => canUseTeamPriorityInsights(teamLimits.value))

const roster = computed(() => buildTeamRoster(contacts.value, employees.value))

const workloadRows = computed(() => buildWorkloadRows(tasks.value, roster.value))
const teamPriorityRows = computed(() => buildTeamPriorityRows(tasks.value, roster.value))

const performanceRows = computed(() => buildPerformanceRows(tasks.value, roster.value, perfRange.value))

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
      role: displayProfessionalRole(c.role, c.role_other),
      teamDivision: c.team_division || '',
      company: c.company || '',
      hasAccount: !!c.user_id,
      userId: c.user_id || null,
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
      userId: emp.id,
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

async function loadTaskInsights() {
  if (!canWorkload.value && !canPerformance.value) return
  insightsLoading.value = true
  insightsError.value = ''
  try {
    const data = await apiJson('/api/v1/tasks')
    tasks.value = Array.isArray(data) ? data : []
  } catch (err) {
    console.error('[AdminTeam] task insights failed', err)
    insightsError.value = err.message || 'Failed to load task data'
    tasks.value = []
  } finally {
    insightsLoading.value = false
  }
}

watch(activeTab, (tab) => {
  if (tab === 'workload' && canWorkload.value && tasks.value.length === 0 && !insightsLoading.value) {
    loadTaskInsights()
  }
  if (tab === 'performance' && canPerformance.value && tasks.value.length === 0 && !insightsLoading.value) {
    loadTaskInsights()
  }
})

watch(canWorkload, (allowed) => {
  if (allowed && activeTab.value === 'workload' && tasks.value.length === 0) loadTaskInsights()
})

watch(canPerformance, (allowed) => {
  if (allowed && activeTab.value === 'performance' && tasks.value.length === 0) loadTaskInsights()
})

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
  if (writeRestricted.value) return
  if (!canAddMembers.value) {
    actionError.value = teamLimits.value?.limit_message || 'Team member limit reached.'
    return
  }
  form.value = {
    name: '',
    email: '',
    selectedRole: DEFAULT_ROLE,
    roleOther: '',
    team_division: '',
    company: '',
    linkedin_url: '',
  }
  formError.value = ''
  showAddModal.value = true
}

function cancelAdd() {
  showAddModal.value = false
  formError.value = ''
}

function openEditModal(row) {
  if (writeRestricted.value || !row.contactId) return
  const contact = contacts.value.find((c) => c.id === row.contactId)
  if (!contact) return
  const parsed = contactRoleFromApi(contact)
  editingContactId.value = contact.id
  editForm.value = {
    name: contact.name || '',
    email: contact.email || '',
    selectedRole: parsed.selectedRole,
    roleOther: parsed.roleOther,
    team_division: contact.team_division || '',
    company: contact.company || '',
    linkedin_url: contact.linkedin_url || '',
  }
  editFormError.value = ''
  showEditModal.value = true
}

function cancelEdit() {
  showEditModal.value = false
  editingContactId.value = null
  editFormError.value = ''
}

function canDeleteRow(row) {
  if (!row) return false
  if (row.userId && row.userId === user.value?.id) return false
  return !!(row.contactId || row.userId)
}

async function confirmDeleteMember(row) {
  if (writeRestricted.value || !canDeleteRow(row)) return
  const ok = window.confirm(
    `Remove ${row.name} from the team? Assigned tasks stay in the workspace, unassigned from this person.`,
  )
  if (!ok) return
  deletingId.value = row.key
  actionError.value = ''
  try {
    if (row.contactId) {
      await apiJson(`/api/v1/contacts/${row.contactId}`, { method: 'DELETE' })
    } else if (row.userId) {
      await apiJson(`/api/v1/users/${row.userId}`, { method: 'DELETE' })
    }
    await Promise.all([loadTeam(), loadTeamLimits()])
    actionSuccess.value = `Removed ${row.name}`
    setTimeout(() => {
      actionSuccess.value = ''
    }, 2500)
  } catch (err) {
    console.error('[AdminTeam] delete member failed', err)
    actionError.value = err.message || 'Failed to remove team member'
  } finally {
    deletingId.value = ''
  }
}

async function saveContactEdit() {
  if (!editingContactId.value || !editForm.value.name.trim() || !editForm.value.email.trim()) return
  if (editLinkedInError.value) return
  savingEdit.value = true
  editFormError.value = ''
  try {
    const updated = await apiJson(`/api/v1/contacts/${editingContactId.value}`, {
      method: 'PATCH',
      body: JSON.stringify({
        name: editForm.value.name.trim(),
        email: editForm.value.email.trim().toLowerCase(),
        role: editForm.value.selectedRole,
        role_other:
          editForm.value.selectedRole === otherRole ? editForm.value.roleOther.trim() || null : null,
        team_division: editForm.value.team_division.trim() || null,
        company: editForm.value.company.trim() || null,
        linkedin_url: editForm.value.linkedin_url.trim() || null,
      }),
    })
    contacts.value = contacts.value.map((c) => (c.id === updated.id ? { ...c, ...updated } : c))
    cancelEdit()
    actionSuccess.value = `Updated ${updated.name}`
    setTimeout(() => {
      actionSuccess.value = ''
    }, 2500)
  } catch (err) {
    console.error('[AdminTeam] edit contact failed', err)
    editFormError.value = err.message || 'Failed to update member'
  } finally {
    savingEdit.value = false
  }
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
        role: form.value.selectedRole,
        role_other: form.value.selectedRole === otherRole ? form.value.roleOther.trim() || null : null,
        team_division: form.value.team_division.trim() || null,
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

onMounted(async () => {
  await loadTeam()
  if (canWorkload.value || canPerformance.value) {
    await loadTaskInsights()
  }
})
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

.team-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin: 0 0 1.25rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--color-border);
}

.team-tab {
  font-family: inherit;
  font-size: 0.85rem;
  font-weight: 500;
  padding: 0.45rem 0.9rem;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
}

.team-tab.active {
  border-color: rgba(196, 163, 90, 0.45);
  background: rgba(196, 163, 90, 0.12);
  color: var(--color-accent);
}

.plan-gate {
  padding: 2rem 1.5rem;
  border: 1px dashed var(--color-border);
  border-radius: var(--radius);
  text-align: center;
  max-width: 420px;
}

.plan-gate h2 {
  font-family: var(--font-display);
  font-weight: 400;
  margin: 0 0 0.5rem;
}

.insights-table-wrap {
  overflow-x: auto;
}

.insights-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
}

.insights-table th,
.insights-table td {
  padding: 0.65rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}

.insights-table th {
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-muted);
  font-weight: 600;
}

.insights-name {
  display: block;
  font-weight: 500;
  color: var(--color-text);
}

.insights-sub {
  display: block;
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.cell-alert {
  color: #f87171;
  font-weight: 600;
}

.perf-toolbar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.perf-label {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-muted);
  font-weight: 600;
}

.perf-filters {
  display: flex;
  gap: 0.4rem;
}

.filter-chip {
  font-family: inherit;
  font-size: 0.8rem;
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  border: 1px solid var(--color-border);
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
}

.filter-chip.active {
  border-color: var(--color-accent);
  color: var(--color-accent);
  background: rgba(196, 163, 90, 0.1);
}

.insights-footnote {
  margin: 0.75rem 0 0;
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.priority-section {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--color-border);
}

.priority-heading {
  font-family: var(--font-display);
  font-size: 1.2rem;
  font-weight: 400;
  margin: 0 0 0.75rem;
}

.priority-upsell {
  margin: 0;
  font-size: 0.88rem;
  color: var(--color-text-muted);
  line-height: 1.5;
}

.empty-panel.compact {
  padding: 1.25rem;
}

.insights-muted {
  color: var(--color-text-muted);
  font-size: 0.85rem;
}

.date-cell {
  white-space: nowrap;
  font-size: 0.85rem;
}

.priority-pill {
  display: inline-block;
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: 0.2rem 0.45rem;
  border-radius: 4px;
  border: 1px solid var(--color-border);
}

.priority-pill[data-p='high'],
.priority-pill[data-p='critical'] {
  color: var(--color-accent);
  border-color: rgba(196, 163, 90, 0.35);
}

.priority-pill[data-p='medium'] {
  color: var(--color-accent);
  border-color: rgba(196, 163, 90, 0.35);
}

.priority-pill[data-p='low'] {
  color: var(--color-text-muted);
}
</style>
