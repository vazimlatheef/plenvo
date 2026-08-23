import { apiJson } from '@/api/client'
import { getToken } from '@/services/auth'

let trialWarningCheckStarted = false

/** Fire-and-forget: email admin when trial ends within 3 days (once per org). */
export async function maybeCheckTrialWarning() {
  if (trialWarningCheckStarted || !getToken()) return
  trialWarningCheckStarted = true
  try {
    await apiJson('/api/v1/users/me/check-trial-warning', { method: 'POST' })
  } catch (err) {
    console.warn('[trial-warning] check failed', err)
    trialWarningCheckStarted = false
  }
}

export function resetTrialWarningCheck() {
  trialWarningCheckStarted = false
}
