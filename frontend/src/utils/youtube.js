/**
 * Accepts a raw 11-char ID or a pasted youtube.com / youtu.be URL.
 * Returns empty string if no valid ID found.
 */
export function extractYoutubeId(input) {
  if (input == null || input === '') return ''
  const s = String(input).trim()
  if (/^[\w-]{11}$/.test(s)) return s
  try {
    const u = new URL(s.startsWith('http') ? s : `https://${s}`)
    if (u.hostname === 'youtu.be') {
      const id = u.pathname.replace(/^\//, '').slice(0, 11)
      return /^[\w-]{11}$/.test(id) ? id : ''
    }
    if (u.hostname.includes('youtube.com')) {
      const v = u.searchParams.get('v')
      if (v && /^[\w-]{11}$/.test(v)) return v
      const embed = u.pathname.match(/\/embed\/([\w-]{11})/)
      if (embed) return embed[1]
    }
  } catch {
    /* ignore */
  }
  const m = s.match(/(?:v=|youtu\.be\/|embed\/)([\w-]{11})/)
  return m ? m[1] : ''
}

export function youtubeEmbedUrl(videoId) {
  return `https://www.youtube-nocookie.com/embed/${videoId}`
}
