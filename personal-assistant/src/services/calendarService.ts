import type { CalendarItem, CreateRequest, Period } from '../types'
import { googleFetch } from './api'
type GoogleEvent = { id: string; summary?: string; location?: string; htmlLink?: string; start?: { dateTime?: string; date?: string }; end?: { dateTime?: string; date?: string } }
function mapEvent(event: GoogleEvent): CalendarItem {
  return { id: event.id, title: event.summary || '제목 없는 일정', start: event.start?.dateTime || event.start?.date || '', end: event.end?.dateTime || event.end?.date || '', location: event.location, link: event.htmlLink }
}
export async function listEvents(token: string, period: Period): Promise<CalendarItem[]> {
  const start = new Date(); start.setHours(0, 0, 0, 0)
  const end = new Date(start)
  if (period === 'today') end.setDate(end.getDate() + 1)
  else { start.setDate(start.getDate() - ((start.getDay() + 6) % 7)); end.setTime(start.getTime()); end.setDate(end.getDate() + 7) }
  const params = new URLSearchParams({ timeMin: start.toISOString(), timeMax: end.toISOString(), singleEvents: 'true', orderBy: 'startTime', maxResults: '50' })
  const result = await googleFetch<{ items?: GoogleEvent[] }>(`https://www.googleapis.com/calendar/v3/calendars/primary/events?${params}`, token)
  return (result.items || []).map(mapEvent)
}
export async function createEvent(token: string, event: CreateRequest): Promise<CalendarItem> {
  const result = await googleFetch<GoogleEvent>('https://www.googleapis.com/calendar/v3/calendars/primary/events', token, { method: 'POST', body: JSON.stringify({ summary: event.title, start: { dateTime: event.start.toISOString() }, end: { dateTime: event.end.toISOString() } }) })
  return mapEvent(result)
}
