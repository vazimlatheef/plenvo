/** Shared UI helpers for authenticated app views. */

export const STATUS_OPTIONS = [
  { value: 'pending', label: 'To Do' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'completed', label: 'Done' },
]

export const STATUS_GROUPS = STATUS_OPTIONS.map((s) => ({
  key: s.value,
  label: s.label,
}))

export function statusLabel(status) {
  return STATUS_OPTIONS.find((s) => s.value === status)?.label || status
}

export function getInitials(nameOrEmail) {
  const raw = (nameOrEmail || '').trim()
  if (!raw) return '?'
  if (raw.includes('@')) {
    return raw.slice(0, 2).toUpperCase()
  }
  const parts = raw.split(/\s+/).filter(Boolean)
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
}

/** Stable 1–5 tone class for avatar backgrounds. */
export function avatarTone(seed) {
  const s = String(seed || '')
  let hash = 0
  for (let i = 0; i < s.length; i += 1) {
    hash = (hash * 31 + s.charCodeAt(i)) >>> 0
  }
  return (hash % 5) + 1
}

export function formatShortDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })
}
