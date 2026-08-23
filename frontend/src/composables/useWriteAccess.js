import { computed, ref } from 'vue'

import { apiJson } from '@/api/client'
import { getToken } from '@/services/auth'

const accessState = ref(null)
const loadingAccess = ref(false)
let loadPromise = null

const DEFAULT_RESTRICTION_HINT =
  'Your trial has ended. Upgrade in Account & Subscription to keep creating and editing.'

export async function loadPlanAccess({ force = false } = {}) {
  if (!getToken()) {
    accessState.value = null
    return null
  }
  if (!force && accessState.value) return accessState.value
  if (loadPromise && !force) return loadPromise

  loadingAccess.value = true
  loadPromise = (async () => {
    try {
      accessState.value = await apiJson('/api/v1/billing/account')
      return accessState.value
    } catch {
      accessState.value = null
      return null
    } finally {
      loadingAccess.value = false
      loadPromise = null
    }
  })()
  return loadPromise
}

export function clearPlanAccess() {
  accessState.value = null
  loadPromise = null
}

export function useWriteAccess() {
  const writeRestricted = computed(() => Boolean(accessState.value?.restricted))
  const restrictionMessage = computed(
    () => accessState.value?.restriction_message || DEFAULT_RESTRICTION_HINT,
  )
  const writeDisabledTitle = computed(() =>
    writeRestricted.value ? restrictionMessage.value : undefined,
  )
  const projectCount = computed(() => accessState.value?.project_count ?? 0)
  const taskCount = computed(() => accessState.value?.task_count ?? 0)

  return {
    accessState,
    loadingAccess,
    writeRestricted,
    restrictionMessage,
    writeDisabledTitle,
    projectCount,
    taskCount,
    loadPlanAccess,
    clearPlanAccess,
  }
}
