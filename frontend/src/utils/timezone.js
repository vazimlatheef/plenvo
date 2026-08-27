import { computed } from 'vue'

import { user } from '@/composables/session'
import { getBrowserTimezone } from '@/services/timezoneSync'

/** User profile timezone, else browser, else UTC. */
export const effectiveTimezone = computed(
  () => user.value?.timezone || getBrowserTimezone() || 'UTC',
)

export function getZonedNowParts(tz = effectiveTimezone.value) {
  const fmt = new Intl.DateTimeFormat('en-GB', {
    timeZone: tz,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
  const parts = Object.fromEntries(fmt.formatToParts(new Date()).map((p) => [p.type, p.value]))
  return {
    year: parts.year,
    month: parts.month,
    day: parts.day,
    hour: Number(parts.hour),
    minute: Number(parts.minute),
  }
}

export function todayKeyInTimezone(tz = effectiveTimezone.value) {
  const p = getZonedNowParts(tz)
  return `${p.year}-${p.month}-${p.day}`
}

export function formatTimezoneLabel(tz = effectiveTimezone.value) {
  if (!tz) return 'UTC'
  try {
    const fmt = new Intl.DateTimeFormat('en-GB', {
      timeZone: tz,
      timeZoneName: 'shortOffset',
    })
    const parts = fmt.formatToParts(new Date())
    const offset = parts.find((p) => p.type === 'timeZoneName')?.value || ''
    return offset ? `${tz} (${offset})` : tz
  } catch {
    return tz
  }
}
