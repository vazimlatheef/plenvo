/** Task due date + optional time helpers. */

import { formatShortDate } from '@/utils/ui'
import { effectiveTimezone, getZonedNowParts, todayKeyInTimezone } from '@/utils/timezone'

export function normalizeDueTime(value) {
  if (!value) return ''
  const s = String(value).trim()
  const m = /^(\d{1,2}):(\d{2})/.exec(s)
  if (!m) return ''
  return `${m[1].padStart(2, '0')}:${m[2]}`
}

export function formatTime12h(hhmm) {
  const norm = normalizeDueTime(hhmm)
  if (!norm) return ''
  const [hStr, mStr] = norm.split(':')
  let h = Number(hStr)
  const m = Number(mStr)
  if (Number.isNaN(h) || Number.isNaN(m)) return ''
  const meridiem = h >= 12 ? 'pm' : 'am'
  h = h % 12
  if (h === 0) h = 12
  return m === 0 ? `${h}${meridiem}` : `${h}:${String(m).padStart(2, '0')}${meridiem}`
}

export function formatTaskDue(taskOrDate, dueTime = null, { emptyLabel = 'No due date' } = {}) {
  const dueDate = typeof taskOrDate === 'object' ? taskOrDate?.due_date : taskOrDate
  const time =
    typeof taskOrDate === 'object'
      ? taskOrDate?.due_time
      : dueTime
  if (!dueDate) return emptyLabel
  const dateLabel = formatShortDate(dueDate)
  const t = normalizeDueTime(time)
  if (!t) return dateLabel
  return `${dateLabel} · ${formatTime12h(t)}`
}

export function taskDueSortKey(task) {
  if (!task?.due_date) return '9999-99-99T99:99'
  const date = String(task.due_date).slice(0, 10)
  const time = normalizeDueTime(task.due_time) || '99:99'
  return `${date}T${time}`
}

/**
 * Open work: soonest due first. Done: latest due first.
 * Tasks with no due date always last.
 */
export function sortTasksByDue(tasks, { newestFirst = false } = {}) {
  if (!Array.isArray(tasks)) return []
  return [...tasks].sort((a, b) => {
    const aDated = Boolean(a?.due_date)
    const bDated = Boolean(b?.due_date)
    if (!aDated && !bDated) return (Number(a.id) || 0) - (Number(b.id) || 0)
    if (!aDated) return 1
    if (!bDated) return -1
    const cmp = taskDueSortKey(a).localeCompare(taskDueSortKey(b))
    if (cmp !== 0) return newestFirst ? -cmp : cmp
    return (Number(a.id) || 0) - (Number(b.id) || 0)
  })
}

export function sortStatusTasksByDue(tasks, status) {
  return sortTasksByDue(tasks, { newestFirst: status === 'completed' })
}

export function isTimedTaskOverdue(task, tz = effectiveTimezone.value) {
  if (!task?.due_date || task.status === 'completed') return false
  const dateKey = String(task.due_date).slice(0, 10)
  const todayKey = todayKeyInTimezone(tz)
  if (dateKey < todayKey) return true
  if (dateKey > todayKey) return false
  const dueTime = normalizeDueTime(task.due_time)
  if (!dueTime) return false
  const parts = getZonedNowParts(tz)
  const [h, m] = dueTime.split(':').map(Number)
  const dueMinutes = h * 60 + m
  const nowMinutes = parts.hour * 60 + parts.minute
  return dueMinutes <= nowMinutes
}
