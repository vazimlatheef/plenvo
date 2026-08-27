import { onMounted, ref, watch } from 'vue'

const STORAGE_KEY = 'plenvo.taskViewMode'

export function useTaskViewMode(defaultMode = 'kanban') {
  const viewMode = ref(defaultMode)

  onMounted(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored === 'list' || stored === 'kanban') {
        viewMode.value = stored
      }
    } catch {
      /* ignore */
    }
  })

  watch(viewMode, (mode) => {
    try {
      localStorage.setItem(STORAGE_KEY, mode)
    } catch {
      /* ignore */
    }
  })

  return { viewMode }
}
