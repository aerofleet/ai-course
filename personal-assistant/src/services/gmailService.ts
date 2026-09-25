import type { MailItem } from '../types'
import { googleFetch } from './api'
type Message = { id: string; snippet?: string; payload?: { headers?: { name: string; value: string }[] } }
function header(message: Message, name: string): string { return message.payload?.headers?.find(h => h.name.toLowerCase() === name)?.value || '' }
export async function listMessages(token: string, query = '', maxResults = 8): Promise<MailItem[]> {
  const params = new URLSearchParams({ maxResults: String(maxResults), ...(query ? { q: query } : {}) })
  const result = await googleFetch<{ messages?: { id: string }[] }>(`https://gmail.googleapis.com/gmail/v1/users/me/messages?${params}`, token)
  if (!result.messages?.length) return []
  return Promise.all(result.messages.map(async ({ id }) => {
    const message = await googleFetch<Message>(`https://gmail.googleapis.com/gmail/v1/users/me/messages/${encodeURIComponent(id)}?format=metadata&metadataHeaders=From&metadataHeaders=Subject&metadataHeaders=Date`, token)
    return { id, from: header(message, 'From') || '보낸 사람 미상', subject: header(message, 'Subject') || '(제목 없음)', date: header(message, 'Date'), snippet: message.snippet || '미리보기 내용이 없습니다.' }
  }))
}
