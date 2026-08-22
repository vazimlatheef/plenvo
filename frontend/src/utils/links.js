/** @typedef {{ label: string, url: string }} LabeledLink */

const URL_PREFIX = /^https?:\/\//i

/**
 * @param {string} url
 * @returns {string}
 */
export function ensureUrl(url) {
  const s = String(url || '').trim()
  if (!s) return ''
  return URL_PREFIX.test(s) ? s : `https://${s}`
}

/**
 * @param {unknown} links
 * @returns {LabeledLink[]}
 */
export function normalizeLinks(links) {
  if (!Array.isArray(links)) return []
  const out = []
  const seen = new Set()
  for (const item of links) {
    const label = String(item?.label || '').trim()
    const url = String(item?.url || '').trim()
    if (!label || !url) continue
    const key = `${label.toLowerCase()}|${ensureUrl(url).toLowerCase()}`
    if (seen.has(key)) continue
    seen.add(key)
    out.push({ label, url: ensureUrl(url) })
  }
  return out
}

/**
 * @returns {LabeledLink[]}
 */
export function emptyLinkRow() {
  return { label: '', url: '' }
}

/**
 * @param {LabeledLink[]} links
 * @returns {LabeledLink[] | null}
 */
export function linksForApi(links) {
  const normalized = normalizeLinks(links)
  return normalized.length ? normalized : null
}
