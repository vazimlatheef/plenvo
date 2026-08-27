import { apiJson } from '@/api/client'
import { setSessionUser, user } from '@/composables/session'

/** IANA timezone from the browser (e.g. Europe/London). */
export function getBrowserTimezone() {
  try {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone
    return typeof tz === 'string' && tz.trim() ? tz.trim() : null
  } catch {
    return null
  }
}

/**
 * Persist browser timezone when it differs from the stored user profile.
 * Returns the updated user object when synced, otherwise the current user.
 */
export async function syncUserTimezone() {
  const tz = getBrowserTimezone()
  if (!tz || !user.value) return user.value

  if (user.value.timezone === tz) return user.value

  try {
    const updated = await apiJson('/api/v1/users/me/sync-timezone', {
      method: 'POST',
      body: JSON.stringify({ timezone: tz }),
    })
    setSessionUser(updated)
    return updated
  } catch (err) {
    console.warn('[timezone] sync failed', err)
    return user.value
  }
}
