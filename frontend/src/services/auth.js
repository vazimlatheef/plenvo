import { apiJson } from '@/api/client'
import { ACCESS_TOKEN_KEY } from '@/constants'
import { maybeCheckOverdueTasks } from '@/services/overdueNotifications'

export function getToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export function setToken(token) {
  localStorage.setItem(ACCESS_TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
}

/** Current user from GET /me (requires stored token). */
export function fetchMe() {
  return apiJson('/me')
}

/**
 * POST /auth/login, store JWT, then GET /me for role-based redirect.
 * @returns {Promise<{ id: number, email: string, full_name: string, role: string, ... }>}
 */
export async function login(email, password) {
  clearToken()
  const data = await apiJson('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
    skipAuth: true,
  })
  if (!data?.access_token) {
    throw new Error('Invalid login response')
  }
  setToken(data.access_token)
  const me = await fetchMe()
  maybeCheckOverdueTasks()
  return me
}

export function logout() {
  clearToken()
}
