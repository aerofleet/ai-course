import type { Command } from '../types'
// LLM 연결 시 분류 함수만 교체하도록 서비스 호출과 분리했습니다.
export function classifyCommand(input: string, now = new Date()): Command {
  const text = input.trim()
  if (!text) return { action: 'unknown' }
  if (/답장|회신/.test(text)) return { action: 'reply_draft', query: extractQuery(text) }
  if (/메일|이메일|편지함/.test(text)) {
    if (/요약|중요|핵심/.test(text)) return { action: 'gmail_summary', query: /중요/.test(text) ? 'is:important newer_than:7d' : 'newer_than:7d' }
    return { action: 'gmail_search', query: extractQuery(text) }
  }
  if (/추가|등록|잡아|만들|생성/.test(text) && /일정|회의|미팅|약속|캘린더/.test(text)) {
    const match = text.match(/(오늘|내일|모레)?\s*(오전|오후)?\s*(\d{1,2})시(?:\s*(\d{1,2})분)?/)
    if (!match) return { action: 'calendar_create' }
    const start = new Date(now)
    start.setDate(start.getDate() + (match[1] === '모레' ? 2 : match[1] === '내일' ? 1 : 0))
    let hour = Number(match[3])
    if (hour > 23 || (match[2] && (hour < 1 || hour > 12))) return { action: 'calendar_create' }
    if (match[2] === '오후' && hour < 12) hour += 12
    if (match[2] === '오전' && hour === 12) hour = 0
    start.setHours(hour, Number(match[4] || 0), 0, 0)
    const end = new Date(start.getTime() + 60 * 60 * 1000)
    const title = text.replace(match[0], '').replace(/^\s*에\s*/, '').replace(/추가해줘|등록해줘|잡아줘|만들어줘|생성해줘|일정|추가|등록|잡아|만들|생성/g, '').trim() || '새 일정'
    return { action: 'calendar_create', create: { title, start, end } }
  }
  if (/일정|캘린더|스케줄/.test(text)) return { action: 'calendar_read', period: /이번\s*주|주간/.test(text) ? 'week' : 'today' }
  return { action: 'unknown' }
}
function extractQuery(text: string): string {
  const quoted = text.match(/["“”']([^"“”']+)["“”']/)
  if (quoted) return quoted[1]
  const about = text.match(/(?:관련|관한|키워드)\s*([^\s]+)|([^\s]+)\s*(?:관련|관한)\s*메일/)
  return about?.[1] || about?.[2] || ''
}
