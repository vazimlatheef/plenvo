import { ref } from 'vue'

import { fetchMe, getToken, logout as authLogout } from '@/services/auth'

/** Shared session (no Pinia): current user after login or /me. */
export const user = ref(null)
export const loadingUser = ref(false)

export function setSessionUser(u) {
  user.value = u
}

export function clearSessionUser() {
  user.value = null
}

/** Load /me when token exists; clears session on failure. */
export async function loadSessionUser() {
  if (!getToken()) {
    clearSessionUser()
    return null
  }
  if (user.value) return user.value
  loadingUser.value = true
  try {
    user.value = await fetchMe()
    return user.value
  } catch {
    authLogout()
    clearSessionUser()
    return null
  } finally {
    loadingUser.value = false
  }
}

export function appHomeRoute(u = user.value) {
  if (!u) return { name: 'login' }
  return u.role === 'admin' ? { name: 'admin-dashboard' } : { name: 'employee-assignments' }
}

export function logoutAndRedirect(router, dest = { name: 'landing' }) {
  authLogout()
  clearSessionUser()
  router.push(dest)
}
