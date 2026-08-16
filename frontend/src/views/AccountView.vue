<template>
  <div class="app-page account-page">
    <div class="app-page-header">
      <div>
        <h1>Account &amp; Subscription</h1>
        <p class="app-lede">Manage your plan, team capacity, and billing.</p>
      </div>
    </div>

    <p v-if="banner" class="success-line">{{ banner }}</p>
    <p v-if="loading" class="muted-line">Loading account…</p>
    <p v-else-if="error" class="error-line">{{ error }}</p>

    <template v-else-if="account">
      <section class="account-card">
        <h2>Current plan</h2>
        <div class="plan-row">
          <div>
            <p class="plan-name">{{ account.plan_label }}</p>
            <p class="muted-line org-name">{{ account.organisation_name }}</p>
          </div>
          <span class="plan-chip" :data-plan="account.display_plan">{{ account.plan_label }}</span>
        </div>

        <p v-if="account.on_trial && account.trial_ends_at" class="trial-line">
          Trial ends {{ formatDate(account.trial_ends_at) }}
          <span v-if="trialDaysLeft != null"> · {{ trialDaysLeft }} day{{ trialDaysLeft === 1 ? '' : 's' }} left</span>
        </p>

        <p v-if="account.cancel_at_period_end && account.access_ends_at" class="warn-line">
          Cancellation scheduled — access continues until {{ formatDate(account.access_ends_at) }}.
        </p>
      </section>

      <section class="account-card">
        <h2>Team members</h2>
        <p class="usage-line">
          <strong>{{ account.member_count }}</strong>
          <template v-if="account.member_limit != null">
            / {{ account.member_limit }}
          </template>
          <template v-else> · Unlimited</template>
          used
        </p>
        <div class="usage-bar" aria-hidden="true">
          <div class="usage-fill" :style="{ width: usagePct + '%' }" />
        </div>
        <p v-if="account.limit_message" class="error-line">{{ account.limit_message }}</p>
      </section>

      <section class="account-card">
        <h2>Upgrade / change plan</h2>
        <p class="app-lede">
          Prices shown in your organisation currency ({{ account.currency }}). Checkout stays in Plenvo —
          you won’t be sent to the public pricing page.
        </p>

        <ul class="plan-list">
          <li v-for="plan in account.plans" :key="plan.id" class="plan-option">
            <div>
              <p class="plan-option-name">{{ plan.name }}</p>
              <p class="plan-option-price">{{ plan.price_display }}<span class="per">/month</span></p>
            </div>
            <button
              v-if="account.can_manage_billing"
              type="button"
              class="btn-primary"
              :disabled="checkoutBusy || isCurrentPaidPlan(plan.id) || !plan.checkout_ready"
              :title="!plan.checkout_ready ? 'Stripe Price ID not configured' : undefined"
              @click="startCheckout(plan.id)"
            >
              {{ checkoutBusy === plan.id ? 'Redirecting…' : planCta(plan.id) }}
            </button>
            <span v-else class="muted-line">Ask an admin to change the plan</span>
          </li>
        </ul>
        <p v-if="checkoutError" class="error-line">{{ checkoutError }}</p>
      </section>

      <section v-if="account.can_manage_billing && account.can_cancel" class="account-card account-card--danger">
        <h2>Cancel subscription</h2>
        <p class="app-lede">
          Cancels at the end of the current billing period — you keep access until then, then the org
          moves to Personal.
        </p>
        <button
          type="button"
          class="btn-outline danger-btn"
          :disabled="cancelBusy"
          @click="confirmCancel"
        >
          {{ cancelBusy ? 'Cancelling…' : 'Cancel subscription' }}
        </button>
        <p v-if="cancelError" class="error-line">{{ cancelError }}</p>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { apiJson } from '@/api/client'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const error = ref('')
const banner = ref('')
const account = ref(null)
const checkoutBusy = ref('')
const checkoutError = ref('')
const cancelBusy = ref(false)
const cancelError = ref('')

const trialDaysLeft = computed(() => {
  const iso = account.value?.trial_ends_at
  if (!iso) return null
  const end = new Date(iso)
  const ms = end.getTime() - Date.now()
  if (Number.isNaN(ms)) return null
  return Math.max(0, Math.ceil(ms / (1000 * 60 * 60 * 24)))
})

const usagePct = computed(() => {
  const a = account.value
  if (!a || a.member_limit == null || a.member_limit <= 0) return a?.member_count ? 8 : 0
  return Math.min(100, Math.round((a.member_count / a.member_limit) * 100))
})

function formatDate(iso) {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  } catch {
    return iso
  }
}

function isCurrentPaidPlan(planId) {
  const a = account.value
  if (!a || (a.on_trial && !a.has_paid_subscription)) return false
  return a.has_paid_subscription && a.plan_tier === planId && !a.cancel_at_period_end
}

function planCta(planId) {
  if (isCurrentPaidPlan(planId)) return 'Current plan'
  if (account.value?.has_paid_subscription) return 'Switch plan'
  return 'Upgrade'
}

async function loadAccount() {
  loading.value = true
  error.value = ''
  try {
    account.value = await apiJson('/api/v1/billing/account')
  } catch (err) {
    error.value = err.message || 'Failed to load account'
  } finally {
    loading.value = false
  }
}

async function startCheckout(planId) {
  checkoutError.value = ''
  checkoutBusy.value = planId
  try {
    const result = await apiJson('/api/v1/billing/create-checkout-session', {
      method: 'POST',
      body: JSON.stringify({ plan: planId }),
    })
    if (result?.url) {
      window.location.assign(result.url)
      return
    }
    if (result?.updated) {
      banner.value = `Plan updated to ${String(result.plan_tier || planId).replace(/^\w/, (c) => c.toUpperCase())}.`
      await loadAccount()
      return
    }
    throw new Error('No checkout URL returned')
  } catch (err) {
    checkoutError.value = err.message || 'Could not start checkout'
  } finally {
    checkoutBusy.value = ''
  }
}

async function confirmCancel() {
  cancelError.value = ''
  if (!window.confirm('Cancel your subscription at the end of the billing period?')) return
  cancelBusy.value = true
  try {
    const result = await apiJson('/api/v1/billing/cancel-subscription', { method: 'POST' })
    banner.value = result.access_ends_at
      ? `Subscription will end on ${formatDate(result.access_ends_at)}. You keep access until then.`
      : 'Subscription cancellation scheduled.'
    await loadAccount()
  } catch (err) {
    cancelError.value = err.message || 'Could not cancel subscription'
  } finally {
    cancelBusy.value = false
  }
}

onMounted(async () => {
  const checkout = route.query.checkout
  if (checkout === 'success') {
    banner.value = 'Payment successful — your plan will update shortly.'
  } else if (checkout === 'cancel') {
    banner.value = 'Checkout cancelled — no changes were made.'
  }
  if (checkout) {
    router.replace({ path: '/app/account', query: {} })
  }
  await loadAccount()
})
</script>

<style scoped>
.account-card {
  margin-bottom: 1.25rem;
  padding: 1.25rem 1.35rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-bg-elevated);
}

.account-card h2 {
  margin: 0 0 0.75rem;
  font-family: var(--font-display);
  font-size: 1.35rem;
  font-weight: 400;
}

.plan-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
}

.plan-name {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 600;
}

.org-name {
  margin: 0.25rem 0 0;
}

.plan-chip {
  flex-shrink: 0;
  padding: 0.3rem 0.7rem;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  background: var(--color-accent-soft);
  color: var(--color-accent);
  border: 1px solid rgba(196, 163, 90, 0.35);
}

.trial-line,
.warn-line {
  margin: 0.85rem 0 0;
  font-size: 0.9rem;
  color: var(--color-text-muted);
}

.warn-line {
  color: #e8b86d;
}

.usage-line {
  margin: 0 0 0.65rem;
  font-size: 0.95rem;
}

.usage-bar {
  height: 6px;
  border-radius: 999px;
  background: rgba(232, 228, 216, 0.1);
  overflow: hidden;
}

.usage-fill {
  height: 100%;
  background: var(--color-accent);
  border-radius: 999px;
  transition: width 0.25s ease;
}

.plan-list {
  list-style: none;
  margin: 1rem 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.plan-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.9rem 0;
  border-top: 1px solid var(--color-border);
}

.plan-option:first-child {
  border-top: none;
  padding-top: 0;
}

.plan-option-name {
  margin: 0;
  font-weight: 600;
}

.plan-option-price {
  margin: 0.2rem 0 0;
  font-size: 0.95rem;
  color: var(--color-text-muted);
}

.per {
  font-size: 0.8rem;
  opacity: 0.8;
}

.account-card--danger h2 {
  color: var(--color-danger);
}

.danger-btn {
  color: var(--color-danger);
  border-color: rgba(248, 113, 113, 0.45);
}

.danger-btn:hover:not(:disabled) {
  border-color: var(--color-danger);
}

.success-line {
  margin: 0 0 1rem;
  font-size: 0.9rem;
  color: var(--status-done);
}
</style>
