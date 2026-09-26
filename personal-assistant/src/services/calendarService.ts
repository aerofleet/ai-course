import type { CalendarItem, CalendarResults, CreateRequest, DateRange } from '../types'
import { googleFetch } from './api'
type GoogleEvent = { id: string; iCalUID?: string; eventType?: string; summary?: string; location?: string; htmlLink?: string; start?: { dateTime?: string; date?: string }; end?: { dateTime?: string; date?: string } }
type GoogleCalendar = { id: string; summary?: string; summaryOverride?: string; accessRole?: string; primary?: boolean; deleted?: boolean }
function mapEvent(event: GoogleEvent, calendar?: GoogleCalendar): CalendarItem {
  return { id: calendar ? `${calendar.id}:${event.id}` : event.id, title: event.summary || '제목 없는 일정', start: event.start?.dateTime || event.start?.date || '', end: event.end?.dateTime || event.end?.date || '', location: event.location, link: event.htmlLink, calendarName: calendar?.summaryOverride || calendar?.summary, eventType: event.eventType }
}
export async function listEvents(token: string, range: DateRange): Promise<CalendarResults> {
  const start = new Date(range.start), end = new Date(range.end)
  if (!Number.isFinite(start.getTime()) || !Number.isFinite(end.getTime()) || end <= start) throw new Error('조회할 날짜 범위가 올바르지 않아요.')
  const calendars: GoogleCalendar[] = []
  let skippedCalendars = 0
  let pageToken: string | undefined
  do {
    const params = new URLSearchParams({ maxResults: '250', showHidden: 'true', ...(pageToken ? { pageToken } : {}) })
    const result: { items?: GoogleCalendar[]; nextPageToken?: string } = await googleFetch(`https://www.googleapis.com/calendar/v3/users/me/calendarList?${params}`, token)
    calendars.push(...(result.items || []).filter(calendar => !calendar.deleted))
    pageToken = result.nextPageToken
  } while (pageToken && calendars.length < 250)
  const readable = calendars.filter(calendar => calendar.accessRole !== 'freeBusyReader' && calendar.accessRole !== 'none')
  skippedCalendars += calendars.length - readable.length + Math.max(0, readable.length - 50) + (pageToken ? 1 : 0)
  const selectedCalendars = readable.slice(0, 50)
  if (!selectedCalendars.length) throw new Error('조회 가능한 캘린더가 없어요. Google Calendar 공유 권한을 확인해 주세요.')
  const results: CalendarItem[] = []
  const failedCalendars: string[] = []
  let truncated = !!pageToken || readable.length > 50
  let calendarCount = 0
  const seen = new Set<string>()
  // Process every registered calendar before applying the aggregate cap, so a busy
  // primary calendar cannot prevent checking the family calendar.
  for (let index = 0; index < selectedCalendars.length; index += 4) {
    const batch = selectedCalendars.slice(index, index + 4)
    const settled = await Promise.allSettled(batch.map(calendar => calendarEvents(token, range, calendar)))
    for (let i = 0; i < settled.length; i++) {
      const result = settled[i]
      if (result.status === 'rejected') {
        failedCalendars.push(batch[i].summaryOverride || batch[i].summary || '이름 없는 캘린더')
        continue
      }
      calendarCount++
      truncated ||= result.value.truncated
      for (const { event, item } of result.value.records) {
        // Shared copies of the same occurrence are displayed once. Distinct
        // recurring occurrences retain their original start times.
        const key = event.iCalUID ? `${event.iCalUID}:${item.start}` : item.id
        if (!seen.has(key)) { seen.add(key); results.push(item) }
      }
    }
  }
  if (!calendarCount) throw new Error('Google Calendar 조회에 실패했어요. Google 권한과 캘린더 공유 설정을 확인해 주세요.')
  results.sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime() || a.title.localeCompare(b.title))
  return { events: results.slice(0, 2000), truncated: truncated || results.length > 2000, scope: { calendarCount, failedCalendars, skippedCalendars } }
}

async function calendarEvents(token: string, range: DateRange, calendar: GoogleCalendar) {
  const records: { event: GoogleEvent; item: CalendarItem }[] = []
  let pageToken: string | undefined
  do {
    const params = new URLSearchParams({ timeMin: range.start, timeMax: range.end, singleEvents: 'true', orderBy: 'startTime', maxResults: '100', ...(pageToken ? { pageToken } : {}) })
    const result: { items?: GoogleEvent[]; nextPageToken?: string } = await googleFetch(`https://www.googleapis.com/calendar/v3/calendars/${encodeURIComponent(calendar.id)}/events?${params}`, token)
    records.push(...(result.items || []).map(event => ({ event, item: mapEvent(event, calendar) })))
    pageToken = result.nextPageToken
  } while (pageToken && records.length < 500)
  return { records: records.slice(0, 500), truncated: !!pageToken || records.length > 500 }
}
export async function createEvent(token: string, event: CreateRequest): Promise<CalendarItem> {
  const result = await googleFetch<GoogleEvent>('https://www.googleapis.com/calendar/v3/calendars/primary/events', token, { method: 'POST', body: JSON.stringify({ summary: event.title, start: { dateTime: event.start.toISOString() }, end: { dateTime: event.end.toISOString() } }) })
  return mapEvent(result)
}
