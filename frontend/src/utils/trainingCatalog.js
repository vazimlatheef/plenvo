import { apiJson } from '@/api/client'

const LAST_KEY = 'Plenvo_last_training'

/** Persist last created training for pickers before any assignments exist. */
export function rememberLastTraining({ id, title }) {
  try {
    sessionStorage.setItem(LAST_KEY, JSON.stringify({ id, title: title || 'Training' }))
  } catch {
    /* ignore */
  }
}

export function readLastTraining() {
  try {
    const raw = sessionStorage.getItem(LAST_KEY)
    if (!raw) return null
    const o = JSON.parse(raw)
    if (o && typeof o.id === 'number' && o.title) return o
    return null
  } catch {
    return null
  }
}

/**
 * Trainings for pickers: admin list API first, then assignments, then last-created.
 * @returns {Promise<{ id: number, title: string }[]>}
 */
export async function fetchTrainingOptions() {
  const map = new Map()
  try {
    const list = await apiJson('/api/v1/trainings')
    if (Array.isArray(list)) {
      for (const t of list) {
        if (t?.id != null && t.title) {
          map.set(t.id, { id: t.id, title: t.title })
        }
      }
    }
  } catch {
    /* not admin or network — try assignments */
  }
  if (!map.size) {
    try {
      const res = await apiJson('/api/v1/assignments')
      for (const it of res.items || []) {
        const tid = it.training_id
        if (tid != null && !map.has(tid)) {
          map.set(tid, {
            id: tid,
            title: it.training_title || 'Training',
          })
        }
      }
    } catch {
      /* ignore */
    }
  }
  const last = readLastTraining()
  if (last && !map.has(last.id)) {
    map.set(last.id, { id: last.id, title: last.title })
  }
  return [...map.values()].sort((a, b) => a.id - b.id)
}
