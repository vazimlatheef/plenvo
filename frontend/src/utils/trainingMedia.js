import { normalizeLinkUrl } from '@/utils/links'
import { extractYoutubeId } from '@/utils/youtube'

/**
 * Accept YouTube (including Shorts) and any other web link.
 * If the user picked YouTube but pasted a normal URL, save it as an external link.
 * If they picked External and pasted a YouTube URL, embed as YouTube when possible.
 */
export function resolveTrainingMedia({ contentType, youtubeInput, externalInput }) {
  const type = contentType || 'youtube'
  const youtubeRaw = String(youtubeInput || '').trim()
  const externalRaw = String(externalInput || '').trim()

  if (type === 'youtube') {
    const id = extractYoutubeId(youtubeRaw)
    if (id) {
      return { content_type: 'youtube', youtube_video_id: id, external_url: null }
    }
    const url = normalizeLinkUrl(youtubeRaw)
    if (url) {
      return { content_type: 'external_link', youtube_video_id: null, external_url: url }
    }
    return { error: 'Enter a YouTube link, video ID, or any web link.' }
  }

  if (type === 'external_link') {
    const id = extractYoutubeId(externalRaw)
    if (id) {
      return { content_type: 'youtube', youtube_video_id: id, external_url: null }
    }
    const url = normalizeLinkUrl(externalRaw)
    if (url) {
      return { content_type: 'external_link', youtube_video_id: null, external_url: url }
    }
    return { error: 'Enter a web link (YouTube, Google Docs, or any URL).' }
  }

  return { error: 'Choose YouTube or an external link.' }
}
