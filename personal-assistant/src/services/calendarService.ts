import type { CalendarItem, CreateRequest, DateRange } from '../types'
import { googleFetch } from './api'
type GoogleEvent = { id: string; summary?: string; location?: string; htmlLink?: string; start?: { dateTime?: string; date?: string }; end?: { dateTime?: string; date?: string } }
function mapEvent(event: GoogleEvent): CalendarItem {
  return { id: event.id, title: event.summary || '제목 없는 일정', start: event.start?.dateTime || event.start?.date || '', end: event.end?.dateTime || event.end?.date || '', location: event.location, link: event.htmlLink }
}
export async function listEvents(token: string, range: DateRange): Promise<{ events: CalendarItem[]; truncated: boolean }> {
  const start = new Date(range.start), end = new Date(range.end)
  if (!Number.isFinite(start.getTime()) || !Number.isFinite(end.getTime()) || end <= start) throw new Error('조회할 날짜 범위가 올바르지 않아요.')
  const events: CalendarItem[] = []
  let pageToken: string | undefined
  do {
    const params = new URLSearchParams({ timeMin: range.start, timeMax: range.end, singleEvents: 'true', orderBy: 'startTime', maxResults: '100', ...(pageToken ? { pageToken } : {}) })
    const result: { items?: GoogleEvent[]; nextPageToken?: string } = await googleFetch(`https://www.googleapis.com/calendar/v3/calendars/primary/events?${params}`, token)
    events.push(...(result.items || []).map(mapEvent))
    pageToken = result.nextPageToken
  } while (pageToken && events.length < 500)
  return { events: events.slice(0, 500), truncated: !!pageToken || events.length > 500 }
}
export async function createEvent(token: string, event: CreateRequest): Promise<CalendarItem> {
  const result = await googleFetch<GoogleEvent>('https://www.googleapis.com/calendar/v3/calendars/primary/events', token, { method: 'POST', body: JSON.stringify({ summary: event.title, start: { dateTime: event.start.toISOString() }, end: { dateTime: event.end.toISOString() } }) })
  return mapEvent(result)
}
