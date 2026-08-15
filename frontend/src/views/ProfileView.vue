<template>
  <div class="app-page profile-page">
    <div class="app-page-header">
      <h1>Profile</h1>
    </div>

    <p v-if="loading" class="muted-line">Loading profile…</p>
    <p v-else-if="loadError" class="error-line">{{ loadError }}</p>

    <form v-else class="profile-form" @submit.prevent="saveProfile">
      <section class="profile-section">
        <h2>Basic info</h2>
        <p class="section-lede">Your account identity on Plenvo.</p>
        <div class="field-stack">
          <label>
            First name
            <input
              v-model="form.first_name"
              type="text"
              required
              maxlength="100"
              :disabled="saving"
              placeholder="First name"
            />
          </label>
          <label>
            Last name
            <input
              v-model="form.last_name"
              type="text"
              maxlength="100"
              :disabled="saving"
              placeholder="Last name"
            />
          </label>
          <label>
            Email
            <span class="email-row">
              <input :value="form.email" type="email" readonly class="input-readonly" />
              <span v-if="form.is_verified" class="verified-badge" title="Email verified">Verified</span>
              <span v-else class="unverified-badge" title="Email not verified">Unverified</span>
            </span>
          </label>
        </div>
      </section>

      <section class="profile-section">
        <h2>Professional</h2>
        <p class="section-lede">Optional context for your team. Leave blank if not needed.</p>
        <div class="field-stack">
          <label>
            Role
            <input
              v-model="form.job_title"
              type="text"
              maxlength="200"
              placeholder="e.g. Product Manager"
              :disabled="saving"
            />
          </label>
          <label>
            Company
            <input
              v-model="form.company_name"
              type="text"
              maxlength="200"
              placeholder="e.g. Acme Ltd"
              :disabled="saving"
            />
          </label>
          <label>
            Phone
            <input
              v-model="form.phone"
              type="tel"
              maxlength="64"
              placeholder="e.g. +44 7700 900123"
              :disabled="saving"
              :class="{ 'input-invalid': !!errors.phone }"
              @blur="validateField('phone')"
            />
            <span v-if="errors.phone" class="field-error">{{ errors.phone }}</span>
          </label>
          <label>
            LinkedIn URL
            <input
              v-model="form.linkedin_url"
              type="url"
              maxlength="2048"
              placeholder="https://linkedin.com/in/your-profile"
              :disabled="saving"
              :class="{ 'input-invalid': !!errors.linkedin_url }"
              @blur="validateField('linkedin_url')"
            />
            <span v-if="errors.linkedin_url" class="field-error">{{ errors.linkedin_url }}</span>
          </label>
        </div>
      </section>

      <p v-if="saveError" class="error-line">{{ saveError }}</p>
      <p v-if="saveSuccess" class="success-line">{{ saveSuccess }}</p>

      <div class="profile-actions">
        <button type="submit" class="btn-primary" :disabled="saving || hasClientErrors">
          {{ saving ? 'Saving…' : 'Save profile' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import { apiJson } from '@/api/client'
import { user } from '@/composables/session'

const PHONE_RE = /^\+?[\d\s().-]{7,32}$/
const LINKEDIN_RE = /^(https?:\/\/)?(www\.)?linkedin\.com\/in\/[\w\-.%]+\/?$/i

const loading = ref(true)
const loadError = ref('')
const saving = ref(false)
const saveError = ref('')
const saveSuccess = ref('')

const form = reactive({
  email: '',
  first_name: '',
  last_name: '',
  is_verified: false,
  job_title: '',
  company_name: '',
  phone: '',
  linkedin_url: '',
})

const errors = reactive({
  phone: '',
  linkedin_url: '',
})

const hasClientErrors = computed(() => !!(errors.phone || errors.linkedin_url))

function applyUser(u) {
  form.email = u.email || ''
  form.first_name = u.first_name || ''
  form.last_name = u.last_name || ''
  form.is_verified = !!u.is_verified
  form.job_title = u.job_title || ''
  form.company_name = u.company_name || ''
  form.phone = u.phone || u.phone_number || ''
  form.linkedin_url = u.linkedin_url || ''
}

function validateField(field) {
  if (field === 'phone') {
    const v = form.phone.trim()
    errors.phone = !v || PHONE_RE.test(v) ? '' : 'Enter a valid phone number (international formats accepted).'
  }
  if (field === 'linkedin_url') {
    const v = form.linkedin_url.trim()
    errors.linkedin_url =
      !v || LINKEDIN_RE.test(v) ? '' : 'LinkedIn URL must look like https://linkedin.com/in/your-profile'
  }
}

function validateAll() {
  validateField('phone')
  validateField('linkedin_url')
  return !hasClientErrors.value
}

async function loadProfile() {
  loading.value = true
  loadError.value = ''
  try {
    const me = await apiJson('/api/v1/users/me')
    applyUser(me)
    if (user.value) user.value = { ...user.value, ...me }
  } catch (err) {
    console.error('[Profile] load failed', err)
    loadError.value = err.message || 'Failed to load profile'
  } finally {
    loading.value = false
  }
}

async function saveProfile() {
  saveError.value = ''
  saveSuccess.value = ''
  if (!validateAll()) return

  saving.value = true
  try {
    const updated = await apiJson('/api/v1/users/me', {
      method: 'PATCH',
      body: JSON.stringify({
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim() || '',
        job_title: form.job_title.trim() || null,
        company_name: form.company_name.trim() || null,
        phone: form.phone.trim() || null,
        linkedin_url: form.linkedin_url.trim() || null,
      }),
    })
    applyUser(updated)
    if (user.value) user.value = { ...user.value, ...updated }
    saveSuccess.value = 'Profile saved'
    setTimeout(() => {
      saveSuccess.value = ''
    }, 2500)
  } catch (err) {
    console.error('[Profile] save failed', err)
    saveError.value = err.message || 'Failed to save profile'
  } finally {
    saving.value = false
  }
}

onMounted(loadProfile)
</script>

<style scoped>
.profile-page {
  max-width: 560px;
}

.profile-form {
  display: flex;
  flex-direction: column;
  gap: 1.75rem;
}

.profile-section {
  padding: 1.35rem 1.4rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-surface);
}

.profile-section h2 {
  margin: 0 0 0.35rem;
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 400;
  color: var(--color-text);
}

.section-lede {
  margin: 0 0 1.1rem;
  font-size: 0.88rem;
  color: var(--color-text-muted);
}

.email-row {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.email-row input {
  flex: 1;
  min-width: 0;
}

.input-readonly {
  opacity: 0.85;
  cursor: default;
}

.input-invalid {
  border-color: var(--color-danger) !important;
}

.verified-badge,
.unverified-badge {
  flex-shrink: 0;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.03em;
  padding: 0.28rem 0.55rem;
  border-radius: var(--radius-sm);
}

.verified-badge {
  color: #0f1210;
  background: linear-gradient(135deg, var(--color-accent), #a6853a);
}

.unverified-badge {
  color: var(--color-text-muted);
  border: 1px solid var(--color-border);
}

.field-error {
  font-size: 0.78rem;
  color: var(--color-danger);
  margin-top: 0.2rem;
}

.profile-actions {
  display: flex;
  justify-content: flex-start;
}

.success-line {
  color: var(--status-done);
  font-size: 0.9rem;
  margin: 0;
}
</style>
