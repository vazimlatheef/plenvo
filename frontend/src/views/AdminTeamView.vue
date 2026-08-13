<template>
  <div class="team-page">
    <div class="page-header">
      <h1>Team Members</h1>
      <button @click="showInviteModal = true" class="btn-primary">+ Invite Employee</button>
    </div>

    <div v-if="loading" class="loading">Loading team...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    
    <div v-else-if="employees.length === 0" class="empty-state">
      <p>No team members yet. Invite your first employee to get started.</p>
    </div>

    <div v-else class="employees-grid">
      <div v-for="emp in employees" :key="emp.id" class="employee-card">
        <div class="emp-header">
          <div class="emp-avatar">{{ getInitials(emp.full_name) }}</div>
          <div class="emp-info">
            <h3>{{ emp.full_name }}</h3>
            <p class="emp-position">{{ emp.position || 'Employee' }}</p>
          </div>
        </div>
        <div class="emp-meta">
          <div class="meta-row">
            <span class="meta-label">Email:</span>
            <span class="meta-value">{{ emp.email }}</span>
          </div>
          <div class="meta-row">
            <span class="meta-label">Joined:</span>
            <span class="meta-value">{{ formatDate(emp.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Invite Employee Modal -->
    <div v-if="showInviteModal" class="modal-overlay" @click.self="showInviteModal = false">
      <div class="modal">
        <h2>Invite Employee</h2>
        <p class="modal-desc">Send an invitation to add a new team member. They'll receive login credentials via email.</p>
        <form @submit.prevent="inviteEmployee">
          <div class="form-group">
            <label for="name">Full Name *</label>
            <input
              id="name"
              v-model="invite.name"
              type="text"
              placeholder="e.g., John Smith"
              required
              maxlength="100"
            />
          </div>
          <div class="form-group">
            <label for="email">Email Address *</label>
            <input
              id="email"
              v-model="invite.email"
              type="email"
              placeholder="e.g., john@company.com"
              required
              maxlength="150"
            />
          </div>
          <div class="form-group">
            <label for="position">Position</label>
            <input
              id="position"
              v-model="invite.position"
              type="text"
              placeholder="e.g., Marketing Manager"
              maxlength="100"
            />
          </div>
          <div class="info-box">
            <p><strong>📧 What happens next:</strong></p>
            <ul>
              <li>Employee receives email with temporary password</li>
              <li>They log in and can view assigned tasks & trainings</li>
              <li>You can assign them tasks from Projects page</li>
            </ul>
          </div>
          <div v-if="inviteError" class="error-msg">{{ inviteError }}</div>
          <div v-if="inviteSuccess" class="success-msg">{{ inviteSuccess }}</div>
          <div class="modal-actions">
            <button type="button" @click="cancelInvite" class="btn-outline">Cancel</button>
            <button type="submit" :disabled="inviting" class="btn-primary">
              {{ inviting ? 'Sending...' : 'Send Invitation' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { getToken } from '@/services/auth'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const employees = ref([])
const loading = ref(true)
const error = ref(null)

const showInviteModal = ref(false)
const invite = ref({ name: '', email: '', position: '' })
const inviting = ref(false)
const inviteError = ref(null)
const inviteSuccess = ref(null)

async function fetchEmployees() {
  try {
    loading.value = true
    error.value = null
    const token = getToken()
    const response = await axios.get(`${API_URL}/api/v1/users?role=employee`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    employees.value = response.data
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to load team members'
  } finally {
    loading.value = false
  }
}

async function inviteEmployee() {
  if (!invite.value.name.trim() || !invite.value.email.trim()) return

  try {
    inviting.value = true
    inviteError.value = null
    inviteSuccess.value = null
    const token = getToken()
    const response = await axios.post(
      `${API_URL}/api/v1/invite`,
      {
        name: invite.value.name.trim(),
        email: invite.value.email.trim().toLowerCase(),
        position: invite.value.position.trim() || null,
      },
      { headers: { Authorization: `Bearer ${token}` } }
    )
    
    // Add new employee to list
    employees.value.unshift(response.data)
    inviteSuccess.value = `Invitation sent to ${invite.value.email}!`
    
    // Clear form after 2 seconds
    setTimeout(() => {
      showInviteModal.value = false
      invite.value = { name: '', email: '', position: '' }
      inviteSuccess.value = null
    }, 2000)
  } catch (err) {
    inviteError.value = err.response?.data?.detail || 'Failed to send invitation'
  } finally {
    inviting.value = false
  }
}

function cancelInvite() {
  showInviteModal.value = false
  invite.value = { name: '', email: '', position: '' }
  inviteError.value = null
  inviteSuccess.value = null
}

function getInitials(name) {
  return name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

function formatDate(dateString) {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

onMounted(() => {
  fetchEmployees()
})
</script>

<style scoped>
.team-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 2rem;
}

.page-header h1 {
  font-size: 1.75rem;
  font-weight: 600;
  margin: 0;
}

.loading, .error, .empty-state {
  text-align: center;
  padding: 3rem;
  color: var(--color-text-muted);
}

.error {
  color: #ef4444;
}

.employees-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.25rem;
}

.employee-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 1.5rem;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.employee-card:hover {
  border-color: var(--color-accent);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.emp-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.emp-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--color-accent);
  color: #0f1210;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1rem;
  flex-shrink: 0;
}

.emp-info h3 {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 0.25rem;
  color: var(--color-text);
}

.emp-position {
  font-size: 0.85rem;
  color: var(--color-text-muted);
  margin: 0;
}

.emp-meta {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.meta-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
}

.meta-label {
  color: var(--color-text-muted);
  font-weight: 500;
}

.meta-value {
  color: var(--color-text);
}

.btn-primary {
  background: var(--color-accent);
  color: #0f1210;
  border: none;
  padding: 0.6rem 1.25rem;
  border-radius: var(--radius);
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: filter 0.2s;
}

.btn-primary:hover {
  filter: brightness(1.1);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-outline {
  background: transparent;
  border: 1px solid var(--color-border);
  color: var(--color-text);
  padding: 0.6rem 1.25rem;
  border-radius: var(--radius);
  font-weight: 500;
  font-size: 0.9rem;
  cursor: pointer;
  transition: border-color 0.2s;
}

.btn-outline:hover {
  border-color: var(--color-accent);
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 1rem;
}

.modal {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 2rem;
  max-width: 500px;
  width: 100%;
}

.modal h2 {
  font-size: 1.4rem;
  font-weight: 600;
  margin: 0 0 0.5rem;
}

.modal-desc {
  font-size: 0.9rem;
  color: var(--color-text-muted);
  margin: 0 0 1.5rem;
  line-height: 1.5;
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  font-size: 0.9rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: var(--color-text);
}

.form-group input {
  width: 100%;
  padding: 0.65rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-bg);
  color: var(--color-text);
  font-family: inherit;
  font-size: 0.9rem;
}

.form-group input:focus {
  outline: none;
  border-color: var(--color-accent);
}

.info-box {
  background: rgba(196, 163, 90, 0.08);
  border: 1px solid rgba(196, 163, 90, 0.2);
  border-radius: var(--radius);
  padding: 1rem;
  margin-bottom: 1.25rem;
}

.info-box p {
  margin: 0 0 0.5rem;
  font-size: 0.85rem;
  color: var(--color-text);
}

.info-box ul {
  margin: 0;
  padding-left: 1.25rem;
}

.info-box li {
  font-size: 0.85rem;
  color: var(--color-text-muted);
  line-height: 1.5;
  margin-bottom: 0.25rem;
}

.error-msg {
  color: #ef4444;
  font-size: 0.85rem;
  margin-bottom: 1rem;
}

.success-msg {
  color: #10b981;
  font-size: 0.85rem;
  margin-bottom: 1rem;
  font-weight: 500;
}

.modal-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}
</style>