/** @typedef {{ label: string, url: string }} LabeledLink */

const HAS_PROTOCOL = /^https?:\/\//i
const DOMAIN_LIKE = /^([\w-]+\.)+[\w-]{2,}(\/.*)?$/i

/**
 * Normalize a link URL: prepend https:// only for domain-like values;
 * leave bare references (folder names, internal refs) as-is.
 * @param {string} url
 * @returns {string}
 */
export function normalizeLinkUrl(url) {
  const s = String(url || '').trim()
  if (!s) return ''
  if (HAS_PROTOCOL.test(s)) return s
  if (DOMAIN_LIKE.test(s) || /^www\./i.test(s)) {
    return `https://${s}`
  }
  return s
}

/** @deprecated use normalizeLinkUrl */
export function ensureUrl(url) {
  return normalizeLinkUrl(url)
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
    const normalized = normalizeLinkUrl(url)
    const key = `${label.toLowerCase()}|${normalized.toLowerCase()}`
    if (seen.has(key)) continue
    seen.add(key)
    out.push({ label, url: normalized })
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
