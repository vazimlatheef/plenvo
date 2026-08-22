import { apiJson } from '@/api/client'
import { getToken } from '@/services/auth'

let overdueCheckStarted = false

/** Fire-and-forget: email user about newly overdue tasks (once per task). */
export async function maybeCheckOverdueTasks() {
  if (overdueCheckStarted || !getToken()) return
  overdueCheckStarted = true
  try {
    await apiJson('/api/v1/users/me/check-overdue-tasks', { method: 'POST' })
  } catch (err) {
    console.warn('[overdue] check failed', err)
    overdueCheckStarted = false
  }
}

export function resetOverdueCheck() {
  overdueCheckStarted = false
}
