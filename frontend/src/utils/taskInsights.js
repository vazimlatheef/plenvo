const PRIORITY_RANK = { high: 0, medium: 1, low: 2 }

export function startOfToday() {
  const d = new Date()
  d.setHours(0, 0, 0, 0)
  return d
}

export function parseInstant(value) {
  if (!value) return null
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? null : d
}

export function isTaskCompleted(task) {
  return task?.status === 'completed'
}

export function isTaskOpen(task) {
  return !isTaskCompleted(task)
}

export function isTaskOverdue(task, today = startOfToday()) {
  if (!isTaskOpen(task) || !task?.due_date) return false
  const due = parseInstant(task.due_date)
  if (!due) return false
  due.setHours(0, 0, 0, 0)
  return due < today
}

export function canUseWorkloadView({ plan_tier: tier, on_trial: onTrial } = {}) {
  if (onTrial) return true
  const t = (tier || '').toLowerCase()
  return t === 'team' || t === 'enterprise'
}

export function canUsePerformanceView({ plan_tier: tier } = {}) {
  return (tier || '').toLowerCase() === 'enterprise'
}

export function canUseTeamPriorityInsights({ plan_tier: tier } = {}) {
  return (tier || '').toLowerCase() === 'enterprise'
}

/** Roster rows aligned with Team page (contacts + employees not duplicated by email). */
export function buildTeamRoster(contacts = [], employees = []) {
  const list = []
  const contactEmails = new Set()

  for (const c of contacts) {
    contactEmails.add((c.email || '').toLowerCase())
    list.push({
      key: `c-${c.id}`,
      name: c.name || c.email,
      email: c.email,
      role: c.role || 'Member',
      company: c.company || '',
      userId: c.user_id || null,
      contactId: c.id,
    })
  }

  for (const emp of employees) {
    const email = (emp.email || '').toLowerCase()
    if (contactEmails.has(email)) continue
    list.push({
      key: `u-${emp.id}`,
      name: emp.full_name || emp.email,
      email: emp.email,
      role: emp.job_title || emp.position || 'Employee',
      company: emp.company_name || '',
      userId: emp.id,
      contactId: null,
    })
  }

  return list
}

export function taskMatchesMember(task, member) {
  if (!task || !member) return false
  if (member.userId != null && task.assignee_id === member.userId) return true
  if (member.contactId != null && task.assignee_contact_id === member.contactId) return true
  return false
}

export function aggregateMemberWorkload(tasks, member) {
  const matched = tasks.filter((t) => taskMatchesMember(t, member))
  return {
    open: matched.filter(isTaskOpen).length,
    overdue: matched.filter((t) => isTaskOverdue(t)).length,
    completed: matched.filter(isTaskCompleted).length,
  }
}

export function buildWorkloadRows(tasks, roster) {
  return roster.map((member) => ({
    ...member,
    stats: aggregateMemberWorkload(tasks, member),
  }))
}

export function getPerformanceRange(preset) {
  const end = new Date()
  const start = new Date(end)
  start.setHours(0, 0, 0, 0)

  if (preset === 'week') {
    const day = start.getDay()
    const mondayOffset = day === 0 ? 6 : day - 1
    start.setDate(start.getDate() - mondayOffset)
  } else if (preset === 'month') {
    start.setDate(1)
  }

  return { start, end }
}

function completedInRange(task, start, end) {
  if (!isTaskCompleted(task)) return false
  const at = parseInstant(task.completed_at) || parseInstant(task.updated_at)
  if (!at) return false
  return at >= start && at <= end
}

export function aggregateMemberPerformance(tasks, member, rangePreset = 'week') {
  const { start, end } = getPerformanceRange(rangePreset)
  const matched = tasks.filter((t) => taskMatchesMember(t, member))
  return {
    completedInPeriod: matched.filter((t) => completedInRange(t, start, end)).length,
    overdueNow: matched.filter((t) => isTaskOverdue(t)).length,
    assignedOpen: matched.filter(isTaskOpen).length,
    rangeStart: start,
    rangeEnd: end,
  }
}

export function buildPerformanceRows(tasks, roster, rangePreset) {
  return roster.map((member) => ({
    ...member,
    stats: aggregateMemberPerformance(tasks, member, rangePreset),
  }))
}

export function taskAssignedToUser(task, userId, contactId = null) {
  if (!task || isTaskCompleted(task)) return false
  if (userId != null && task.assignee_id === userId) return true
  if (contactId != null && task.assignee_contact_id === contactId) return true
  return false
}

export function sortFocusTasks(tasks) {
  const today = startOfToday()
  return [...tasks].sort((a, b) => {
    const aOver = isTaskOverdue(a, today) ? 0 : 1
    const bOver = isTaskOverdue(b, today) ? 0 : 1
    if (aOver !== bOver) return aOver - bOver

    const aDue = parseInstant(a.due_date)
    const bDue = parseInstant(b.due_date)
    if (aDue && bDue && aDue.getTime() !== bDue.getTime()) return aDue - bDue
    if (aDue && !bDue) return -1
    if (!aDue && bDue) return 1

    const ap = PRIORITY_RANK[a.priority] ?? 1
    const bp = PRIORITY_RANK[b.priority] ?? 1
    if (ap !== bp) return ap - bp

    return (a.id || 0) - (b.id || 0)
  })
}

export function focusTasksForUser(tasks, userId, contactId = null, limit = 3) {
  const mine = tasks.filter((t) => taskAssignedToUser(t, userId, contactId))
  return sortFocusTasks(mine).slice(0, limit)
}

export function focusTaskForMember(tasks, member) {
  const mine = tasks.filter((t) => taskMatchesMember(t, member) && isTaskOpen(t))
  return sortFocusTasks(mine)[0] || null
}

export function buildTeamPriorityRows(tasks, roster) {
  return roster.map((member) => ({
    ...member,
    topTask: focusTaskForMember(tasks, member),
  }))
}
