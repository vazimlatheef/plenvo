import { ACCESS_TOKEN_KEY } from '@/constants'

const BASE = import.meta.env.VITE_API_URL ?? ''
console.log('API BASE URL:', BASE)

function formatErrorDetail(data, res) {
  const d = data?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) return d.map((x) => x.msg || JSON.stringify(x)).join(', ')
  if (d && typeof d === 'object') return JSON.stringify(d)
  return res.statusText || 'Request failed'
}

export async function apiFetch(path, options = {}) {
  const { skipAuth = false, headers: initHeaders, ...rest } = options
  const headers = new Headers(initHeaders || {})

  if (!skipAuth) {
    const token = localStorage.getItem(ACCESS_TOKEN_KEY)
    if (token) headers.set('Authorization', `Bearer ${token}`)
  }

  if (rest.body != null && !(rest.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const url = `${BASE}${path}`
  return fetch(url, { ...rest, headers })
}

export async function apiJson(path, options = {}) {
  const res = await apiFetch(path, options)
  if (res.status === 204) return null
  const text = await res.text()
  let data = null
  try {
    data = text ? JSON.parse(text) : null
  } catch {
    data = null
  }
  if (!res.ok) {
    throw new Error(formatErrorDetail(data, res))
  }
  return data
}

export { BASE as apiBaseUrl }