/**
 * Accepts a raw 11-char ID or any youtube.com / youtu.be URL
 * (watch, shorts, live, embed, mobile, music).
 * Returns empty string if no valid ID found.
 */
const ID_RE = /^[\w-]{11}$/

function youtubeHost(hostname) {
  const host = (hostname || '').replace(/^www\./, '').toLowerCase()
  return (
    host === 'youtu.be' ||
    host === 'youtube.com' ||
    host === 'm.youtube.com' ||
    host === 'music.youtube.com' ||
    host === 'youtube-nocookie.com'
  )
}

function idFromPath(pathname) {
  const parts = String(pathname || '')
    .split('/')
    .filter(Boolean)
  if (!parts.length) return ''
  // youtu.be/ID  or  /shorts/ID  /embed/ID  /live/ID  /v/ID
  const first = parts[0].toLowerCase()
  const candidate = ['shorts', 'embed', 'live', 'v', 'watch'].includes(first) ? parts[1] : parts[0]
  const id = (candidate || '').slice(0, 11)
  return ID_RE.test(id) ? id : ''
}

export function extractYoutubeId(input) {
  if (input == null || input === '') return ''
  const s = String(input).trim()
  if (ID_RE.test(s)) return s
  try {
    const u = new URL(s.startsWith('http') ? s : `https://${s}`)
    if (youtubeHost(u.hostname)) {
      const v = u.searchParams.get('v')
      if (v && ID_RE.test(v)) return v
      const fromPath = idFromPath(u.pathname)
      if (fromPath) return fromPath
    }
  } catch {
    /* ignore */
  }
  const m = s.match(/(?:v=|youtu\.be\/|\/shorts\/|\/embed\/|\/live\/|\/v\/)([\w-]{11})/)
  return m ? m[1] : ''
}

export function youtubeEmbedUrl(videoId) {
  return `https://www.youtube-nocookie.com/embed/${videoId}`
}
