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
          <span class="plan-chip" :data-plan="account.plan_tier">{{ planTierLabel(account.plan_tier) }}</span>
        </div>

        <p v-if="account.on_trial && !account.has_paid_subscription" class="trial-line trial-line--prominent">
          <strong>Free trial</strong>
          <template v-if="account.trial_ends_at">
            — ends {{ formatDate(account.trial_ends_at) }}
            <span v-if="trialDaysLeft != null"> · {{ trialDaysLeft }} day{{ trialDaysLeft === 1 ? '' : 's' }} left</span>
          </template>
        </p>
        <p v-else-if="account.has_paid_subscription" class="muted-line billing-line">
          Billed monthly in {{ account.currency }}.
        </p>
        <p v-else-if="account.restricted" class="warn-line trial-line--prominent">
          {{ account.restriction_message }}
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
        <p v-if="account.plan_tier === 'personal'" class="muted-line usage-hint">
          Personal plan — solo use only (1 member total).
        </p>
        <div class="usage-bar" aria-hidden="true">
          <div class="usage-fill" :style="{ width: usagePct + '%' }" />
        </div>
        <p v-if="account.limit_message" class="limit-line">{{ account.limit_message }}</p>
        <p
          v-if="account.trial_peak_member_count > 1 && account.minimum_subscribable_tier"
          class="muted-line usage-hint"
        >
          Trial peak: {{ account.trial_peak_member_count }} members — minimum plan when subscribing:
          {{ planTierLabel(account.minimum_subscribable_tier) }}.
        </p>
      </section>

      <section class="account-card">
        <h2>{{ account.on_trial && !account.has_paid_subscription ? 'Change trial plan' : 'Upgrade / change plan' }}</h2>
        <p class="app-lede">
          Prices shown in {{ currencyLabel }}.
          <template v-if="account.on_trial && !account.has_paid_subscription">
            Subscribe now on your current plan to pay immediately via Stripe — you do not have to wait until the trial ends.
            You can also switch to a higher trial plan without a card; limits update immediately. Downgrades are not available during trial.
          </template>
          <template v-else-if="account.restricted">
            Subscribe to restore full create and edit access for your {{ account.project_count }} projects and
            {{ account.task_count }} tasks.
          </template>
          <template v-else>
            Checkout stays in Plenvo — you won't be sent to the public pricing page.
          </template>
        </p>

        <ul class="plan-list">
          <li
            v-for="plan in account.plans"
            :key="plan.id"
            class="plan-option"
            :class="{ 'plan-option--current': isCurrentPlan(plan.id) }"
          >
            <div>
              <p class="plan-option-name">
                {{ plan.name }}
                <span v-if="isCurrentPlan(plan.id)" class="current-badge">Current</span>
              </p>
              <p class="plan-option-price">{{ plan.price_display }}<span class="per">/month</span></p>
            </div>
            <button
              v-if="account.can_manage_billing"
              type="button"
              :class="canSubscribeNow(plan.id) || !isCurrentPlan(plan.id) ? 'btn-primary' : 'btn-outline'"
              :disabled="isPlanButtonDisabled(plan.id)"
              :title="planSwitchBlockedTitle(plan.id) || (!plan.checkout_ready ? 'Stripe Price ID not configured' : undefined)"
              @click="startCheckout(plan.id)"
            >
              {{ checkoutBusy === plan.id ? 'Updating…' : planCta(plan.id) }}
            </button>
            <span v-else class="muted-line">Ask an admin to change the plan</span>
          </li>
        </ul>
        <p v-if="checkoutError" class="error-line">{{ checkoutError }}</p>
      </section>

      <section v-if="account.can_manage_billing && account.can_cancel" class="account-card account-card--cancel">
        <h2>Cancel subscription</h2>
        <p class="cancel-lede">We're sorry to see you go.</p>
        <p class="app-lede cancel-copy">
          Your subscription will cancel at the end of the current billing period — you keep full access until then.
        </p>
        <div class="cancel-actions">
          <button
            type="button"
            class="btn-outline danger-btn"
            :disabled="cancelBusy"
            @click="confirmCancel"
          >
            {{ cancelBusy ? 'Cancelling…' : 'Cancel subscription' }}
          </button>
        </div>
        <p v-if="cancelError" class="error-line">{{ cancelError }}</p>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { apiJson } from '@/api/client'
import { CURRENCY_LABELS } from '@/composables/useCurrency'
import { loadPlanAccess } from '@/composables/useWriteAccess'

const route = useRoute()
const router = useRouter()

const TIER_RANK = { personal: 0, team: 1, enterprise: 2 }
const TRIAL_DOWNGRADE_MSG =
  'You can upgrade anytime during your trial. To switch to a lower plan, wait until your trial ends or subscribe.'

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

const currencyLabel = computed(() => {
  const code = account.value?.currency
  if (!code) return 'your organisation currency'
  return CURRENCY_LABELS[code] || code
})

function planTierLabel(tier) {
  const labels = { personal: 'Personal', team: 'Team', enterprise: 'Enterprise' }
  return labels[tier] || tier
}

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

function canSubscribeNow(planId) {
  const a = account.value
  return !!(a?.on_trial && !a?.has_paid_subscription && a.plan_tier === planId)
}

function isCurrentPlan(planId) {
  const a = account.value
  if (!a || a.plan_tier !== planId) return false
  if (a.cancel_at_period_end) return false
  // Paid subscriber on this tier, or active trial on this tier.
  if (a.has_paid_subscription) return true
  if (a.on_trial && !a.has_paid_subscription) return true
  return false
}

function planCta(planId) {
  if (canSubscribeNow(planId)) return 'Subscribe now'
  if (isCurrentPlan(planId)) return 'Current plan'
  const a = account.value
  if (isTrialDowngrade(planId)) return 'Upgrade only during trial'
  if (isBelowMinimumTier(planId)) return 'Below trial peak'
  if (a?.on_trial && !a?.has_paid_subscription) return 'Switch to this plan'
  if (a?.has_paid_subscription) return 'Switch plan'
  return 'Subscribe'
}

function tierRank(planId) {
  return TIER_RANK[planId] ?? 0
}

function isTrialDowngrade(planId) {
  const a = account.value
  if (!a?.on_trial || a.has_paid_subscription) return false
  return tierRank(planId) < tierRank(a.plan_tier)
}

function isBelowMinimumTier(planId) {
  const a = account.value
  if (!a?.minimum_subscribable_tier) return false
  if (a.on_trial && !a.has_paid_subscription) return false
  return tierRank(planId) < tierRank(a.minimum_subscribable_tier)
}

function isPlanSwitchBlocked(planId) {
  return isTrialDowngrade(planId) || isBelowMinimumTier(planId)
}

function isPlanButtonDisabled(planId) {
  if (checkoutBusy.value) return true
  const plan = account.value?.plans?.find((p) => p.id === planId)
  if (plan && !plan.checkout_ready) return true
  if (isPlanSwitchBlocked(planId)) return true
  if (isCurrentPlan(planId) && !canSubscribeNow(planId)) return true
  return false
}

function planSwitchBlockedTitle(planId) {
  if (isTrialDowngrade(planId)) return TRIAL_DOWNGRADE_MSG
  const a = account.value
  if (isBelowMinimumTier(planId) && a) {
    const peak = a.trial_peak_member_count ?? a.member_count
    return `Your trial peaked at ${peak} team member${peak === 1 ? '' : 's'}. Minimum plan: ${planTierLabel(a.minimum_subscribable_tier)}.`
  }
  return ''
}

async function loadAccount() {
  loading.value = true
  error.value = ''
  try {
    account.value = await apiJson('/api/v1/billing/account')
    await loadPlanAccess({ force: true })
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
      body: JSON.stringify({
        plan: planId,
        subscribe: canSubscribeNow(planId),
      }),
    })
    if (result?.url) {
      window.location.assign(result.url)
      return
    }
    if (result?.updated) {
      const name = String(result.plan_tier || planId).replace(/^\w/, (c) => c.toUpperCase())
      if (result.on_trial) {
        banner.value = `Trial plan updated to ${name}. New limits apply immediately.`
      } else {
        banner.value = `Plan updated to ${name}.`
      }
      await loadAccount()
      return
    }
    throw new Error('No checkout URL returned')
  } catch (err) {
    checkoutError.value = err.message || 'Could not update plan'
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
.warn-line,
.billing-line {
  margin: 0.85rem 0 0;
  font-size: 0.9rem;
  color: var(--color-text-muted);
}

.trial-line--prominent {
  color: var(--color-accent);
}

.warn-line {
  color: #e8b86d;
}

.usage-line {
  margin: 0 0 0.35rem;
  font-size: 0.95rem;
}

.usage-hint {
  margin: 0 0 0.65rem;
  font-size: 0.82rem;
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

.plan-option--current {
  background: rgba(196, 163, 90, 0.04);
  margin: 0 -0.5rem;
  padding-left: 0.5rem;
  padding-right: 0.5rem;
  border-radius: var(--radius-sm);
}

.plan-option:first-child {
  border-top: none;
  padding-top: 0;
}

.plan-option-name {
  margin: 0;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.current-badge {
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  padding: 0.15rem 0.45rem;
  border-radius: 999px;
  background: var(--color-accent-soft);
  color: var(--color-accent);
  border: 1px solid rgba(196, 163, 90, 0.35);
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

.account-card--cancel {
  margin-top: 0.5rem;
}

.account-card--cancel h2 {
  color: var(--color-text);
}

.cancel-lede {
  margin: 0 0 0.35rem;
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--color-text-muted);
}

.cancel-copy {
  margin-bottom: 1.25rem;
}

.cancel-actions {
  margin-top: 0.25rem;
}

.limit-line {
  margin: 0.65rem 0 0;
  padding: 0.55rem 0.7rem;
  font-size: 0.85rem;
  line-height: 1.45;
  color: #e8b86d;
  background: rgba(232, 184, 109, 0.08);
  border: 1px solid rgba(232, 184, 109, 0.22);
  border-radius: var(--radius-sm);
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

@media (max-width: 640px) {
  .plan-option {
    flex-direction: column;
    align-items: flex-start;
  }

  .plan-option .btn-primary,
  .plan-option .btn-outline {
    width: 100%;
    justify-content: center;
  }
}
</style>
