export function isRecurringTask(task) {
  if (!task) return false
  if (task.series_id) return true
  const rec = String(task.recurrence || 'none').toLowerCase()
  return rec === 'weekly' || rec === 'monthly'
}

export function confirmDeleteTask(task) {
  if (isRecurringTask(task)) {
    return window.confirm(
      'This is a repeating task. Deleting it removes every occurrence in the series.',
    )
  }
  return window.confirm('Delete this task?')
}

export function removeDeletedTask(list, task) {
  if (!Array.isArray(list) || !task) return list || []
  if (task.series_id) {
    return list.filter((t) => t.series_id !== task.series_id)
  }
  return list.filter((t) => t.id !== task.id)
}
