/** Unified assignee keys for users + lightweight contacts: `u:12` / `c:34`. */

export function userAssigneeKey(id) {
  return id == null ? null : `u:${id}`
}

export function contactAssigneeKey(id) {
  return id == null ? null : `c:${id}`
}

export function parseAssigneeKey(key) {
  if (!key) return { assignee_id: null, assignee_contact_id: null }
  const s = String(key)
  if (s.startsWith('c:')) {
    const id = Number(s.slice(2))
    return { assignee_id: null, assignee_contact_id: Number.isFinite(id) ? id : null }
  }
  if (s.startsWith('u:') || s.startsWith('user:')) {
    const id = Number(s.includes(':') ? s.slice(s.indexOf(':') + 1) : s)
    return { assignee_id: Number.isFinite(id) ? id : null, assignee_contact_id: null }
  }
  const id = Number(s)
  return { assignee_id: Number.isFinite(id) ? id : null, assignee_contact_id: null }
}

export function taskAssigneeKey(task) {
  if (!task) return null
  if (task.assignee_id != null) return userAssigneeKey(task.assignee_id)
  if (task.assignee_contact_id != null) return contactAssigneeKey(task.assignee_contact_id)
  return null
}

/** Default create-form assignee: the logged-in user. */
export function currentUserAssigneeKey(currentUser) {
  return currentUser?.id != null ? userAssigneeKey(currentUser.id) : null
}

/**
 * Build dropdown options from org users + contacts.
 * Linked contacts (with user_id) are omitted when that user is already listed.
 */
export function buildAssigneeOptions({ users = [], contacts = [], currentUser = null } = {}) {
  const linkedUserIds = new Set(
    contacts.filter((c) => c.user_id != null).map((c) => c.user_id),
  )
  const options = []

  const byId = new Map()
  for (const u of users) {
    if (u?.id != null) byId.set(u.id, u)
  }
  if (currentUser?.id != null && !byId.has(currentUser.id)) {
    byId.set(currentUser.id, currentUser)
  }

  for (const u of byId.values()) {
    options.push({
      key: userAssigneeKey(u.id),
      kind: 'user',
      id: u.id,
      label: u.full_name || u.email || `User #${u.id}`,
      email: u.email,
      isYou: u.id === currentUser?.id,
    })
  }

  for (const c of contacts) {
    if (c.user_id != null && byId.has(c.user_id)) continue
    options.push({
      key: contactAssigneeKey(c.id),
      kind: 'contact',
      id: c.id,
      label: c.name || c.email || `Contact #${c.id}`,
      email: c.email,
      role: c.role,
      isYou: false,
    })
  }

  return options.sort((a, b) => {
    if (a.isYou) return -1
    if (b.isYou) return 1
    return String(a.label).localeCompare(String(b.label), undefined, { sensitivity: 'base' })
  })
}

export function assigneeOptionLabel(opt) {
  if (!opt) return ''
  const base = opt.label
  if (opt.isYou) return `${base} (you)`
  if (opt.kind === 'contact') return `${base} (contact)`
  return base
}

export function resolveAssigneeName(task, { usersById = {}, contactsById = {}, fallback = 'Unassigned' } = {}) {
  if (!task) return fallback
  if (task.assignee_id != null) {
    const u = usersById[task.assignee_id]
    return u?.full_name || u?.email || `User #${task.assignee_id}`
  }
  if (task.assignee_contact_id != null) {
    const c = contactsById[task.assignee_contact_id]
    return c?.name || c?.email || `Contact #${task.assignee_contact_id}`
  }
  return fallback
}
