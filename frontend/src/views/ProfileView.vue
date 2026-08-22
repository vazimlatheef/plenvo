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
          <label class="phone-field">
            Phone
            <VueTelInput
              v-model="form.phone"
              mode="international"
              :auto-format="true"
              :valid-characters-only="true"
              :disabled="saving"
              :preferred-countries="['gb', 'us', 'ie', 'pt', 'es', 'fr', 'de']"
              :dropdown-options="phoneDropdownOptions"
              :input-options="phoneInputOptions"
              :style-classes="['profile-tel', errors.phone ? 'profile-tel--invalid' : '']"
              @validate="onPhoneValidate"
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

      <section class="profile-section">
        <h2>Notifications</h2>
        <p class="section-lede">Control which emails Plenvo sends you.</p>
        <label class="toggle-row">
          <input
            v-model="form.overdue_email_enabled"
            type="checkbox"
            :disabled="savingOverduePref"
            @change="saveOverduePref"
          />
          <span class="toggle-label">
            Email me when my tasks are overdue
            <span class="toggle-hint">One email per task when it first becomes overdue.</span>
          </span>
        </label>
        <p v-if="overduePrefError" class="error-line">{{ overduePrefError }}</p>
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
import { VueTelInput } from 'vue-tel-input'
import 'vue-tel-input/vue-tel-input.css'

import { apiJson } from '@/api/client'
import { user } from '@/composables/session'

const LINKEDIN_RE = /^(https?:\/\/)?(www\.)?linkedin\.com\/in\/[\w\-.%]+\/?$/i
const E164_RE = /^\+[1-9]\d{6,14}$/

const loading = ref(true)
const loadError = ref('')
const saving = ref(false)
const savingOverduePref = ref(false)
const overduePrefError = ref('')
const saveError = ref('')
const saveSuccess = ref('')

/** E.164 value sent to the API (+countrycode…). */
const phoneE164 = ref('')
const phoneTouched = ref(false)

const form = reactive({
  email: '',
  first_name: '',
  last_name: '',
  is_verified: false,
  job_title: '',
  company_name: '',
  phone: '',
  linkedin_url: '',
  overdue_email_enabled: true,
})

const errors = reactive({
  phone: '',
  linkedin_url: '',
})

const phoneDropdownOptions = {
  showDialCodeInSelection: true,
  showDialCodeInList: true,
  showFlags: true,
  showSearchBox: true,
  searchBoxPlaceholder: 'Search country',
}

const phoneInputOptions = {
  placeholder: 'Phone number',
  showDialCode: true,
  autocomplete: 'tel',
  name: 'phone',
  maxlength: 20,
  styleClasses: 'profile-tel-input',
}

const hasClientErrors = computed(() => !!(errors.phone || errors.linkedin_url))

function nationalDigits(phoneObject) {
  const raw = phoneObject?.nationalNumber ?? ''
  return String(raw).replace(/\D/g, '')
}

function onPhoneValidate(phoneObject) {
  const digits = nationalDigits(phoneObject)
  if (!digits) {
    phoneE164.value = ''
    if (phoneTouched.value) errors.phone = ''
    return
  }
  if (phoneObject?.valid && phoneObject.number) {
    phoneE164.value = phoneObject.number
    errors.phone = ''
    return
  }
  phoneE164.value = ''
  if (phoneTouched.value) {
    errors.phone = 'Enter a valid phone number for the selected country.'
  }
}

function applyUser(u) {
  form.email = u.email || ''
  form.first_name = u.first_name || ''
  form.last_name = u.last_name || ''
  form.is_verified = !!u.is_verified
  form.job_title = u.job_title || ''
  form.company_name = u.company_name || ''
  const existing = (u.phone || u.phone_number || '').trim()
  form.phone = existing
  phoneE164.value = E164_RE.test(existing) ? existing : ''
  phoneTouched.value = false
  errors.phone = ''
  form.linkedin_url = u.linkedin_url || ''
  form.overdue_email_enabled = u.overdue_email_enabled !== false
}

function validateField(field) {
  if (field === 'phone') {
    phoneTouched.value = true
    const display = (form.phone || '').trim()
    const digitsOnly = display.replace(/[^\d]/g, '')
    // Dial-code-only / empty → clear
    if (!display || digitsOnly.length <= 3) {
      phoneE164.value = ''
      errors.phone = ''
      return
    }
    if (phoneE164.value && E164_RE.test(phoneE164.value)) {
      errors.phone = ''
      return
    }
    errors.phone = 'Enter a valid phone number for the selected country.'
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

async function saveOverduePref() {
  overduePrefError.value = ''
  savingOverduePref.value = true
  try {
    const updated = await apiJson('/api/v1/users/me', {
      method: 'PATCH',
      body: JSON.stringify({ overdue_email_enabled: form.overdue_email_enabled }),
    })
    applyUser(updated)
    if (user.value) user.value = { ...user.value, ...updated }
  } catch (err) {
    console.error('[Profile] overdue pref save failed', err)
    overduePrefError.value = err.message || 'Failed to save notification preference'
    form.overdue_email_enabled = !form.overdue_email_enabled
  } finally {
    savingOverduePref.value = false
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
        phone: phoneE164.value || null,
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

.phone-field :deep(.vue-tel-input.profile-tel) {
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  box-shadow: none;
}

.phone-field :deep(.vue-tel-input.profile-tel:focus-within) {
  border-color: var(--color-accent);
}

.phone-field :deep(.vue-tel-input.profile-tel--invalid) {
  border-color: var(--color-danger);
}

.phone-field :deep(.vti__dropdown) {
  background: var(--color-bg);
  border-radius: var(--radius-sm) 0 0 var(--radius-sm);
  padding: 0 0.35rem 0 0.5rem;
}

.phone-field :deep(.vti__dropdown:hover),
.phone-field :deep(.vti__dropdown.open) {
  background: var(--color-surface);
}

.phone-field :deep(.vti__selection) {
  font-size: 0.9rem;
  color: var(--color-text);
  gap: 0.35rem;
}

.phone-field :deep(.vti__dropdown-arrow) {
  color: var(--color-text-muted);
  border-top-color: var(--color-text-muted);
}

.phone-field :deep(.vti__dropdown-list) {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text);
  max-height: 240px;
  z-index: 30;
}

.phone-field :deep(.vti__dropdown-item) {
  color: var(--color-text);
  padding: 0.45rem 0.75rem;
}

.phone-field :deep(.vti__dropdown-item.highlighted),
.phone-field :deep(.vti__dropdown-item:hover) {
  background: rgba(196, 163, 90, 0.14);
}

.phone-field :deep(.vti__search_box) {
  margin: 0.5rem;
  width: calc(100% - 1rem);
  box-sizing: border-box;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  color: var(--color-text);
  padding: 0.45rem 0.55rem;
  font-family: var(--font-body);
  font-size: 0.88rem;
}

.phone-field :deep(.vti__input),
.phone-field :deep(.profile-tel-input) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  color: var(--color-text) !important;
  font-family: var(--font-body);
  font-size: 0.95rem;
  padding: 0.55rem 0.65rem !important;
}

.phone-field :deep(.vti__input::placeholder) {
  color: var(--color-text-muted);
}

.toggle-row {
  display: flex;
  align-items: flex-start;
  gap: 0.65rem;
  cursor: pointer;
  font-size: 0.92rem;
  color: var(--color-text);
}

.toggle-row input {
  margin-top: 0.2rem;
  accent-color: var(--color-accent);
  flex-shrink: 0;
}

.toggle-label {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.toggle-hint {
  font-size: 0.78rem;
  color: var(--color-text-muted);
  font-weight: 400;
}
</style>
