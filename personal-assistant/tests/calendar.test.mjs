import { readFile } from 'node:fs/promises'
import assert from 'node:assert/strict'
import { afterEach, test } from 'node:test'
import ts from 'typescript'

const compile = text => ts.transpileModule(text, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 } }).outputText
const uri = code => `data:text/javascript;base64,${Buffer.from(code).toString('base64')}`
const api = uri(compile(await readFile(new URL('../src/services/api.ts', import.meta.url), 'utf8')))
const source = compile(await readFile(new URL('../src/services/calendarService.ts', import.meta.url), 'utf8')).replace("'./api'", JSON.stringify(api))
const { listEvents } = await import(uri(source))
const { formatEventTime } = await import(uri(compile(await readFile(new URL('../src/utils/format.ts', import.meta.url), 'utf8'))))
const originalFetch = globalThis.fetch
afterEach(() => { globalThis.fetch = originalFetch })
const range = { start: '2026-09-26T14:30:00+09:00', end: '2026-12-26T14:30:00+09:00', label: '앞으로 3개월' }
const event = id => ({ id, summary: '다음 달 면접', start: { dateTime: '2026-10-12T14:00:00+09:00' } })
const mockCalendarFetch = handler => {
  globalThis.fetch = async (url, init) => new URL(url).pathname.endsWith('/calendarList')
    ? Response.json({ items: [{ id: 'primary', summary: '기본', accessRole: 'owner' }] }) : handler(url, init)
}

test('three-month range reaches Google unchanged and follows pagination', async () => {
  const urls = []
  mockCalendarFetch(async url => {
    urls.push(new URL(url))
    return Response.json(urls.length === 1 ? { items: [event('1')], nextPageToken: 'page2' } : { items: [event('2')] })
  })
  const result = await listEvents('fake', range)
  assert.equal(urls[0].searchParams.get('timeMin'), range.start)
  assert.equal(urls[0].searchParams.get('timeMax'), range.end)
  assert.equal(urls[1].searchParams.get('pageToken'), 'page2')
  assert.equal(result.events.length, 2)
  assert.equal(result.truncated, false)
})

test('500-event cap reports incomplete lookup', async () => {
  let calls = 0
  mockCalendarFetch(async () => Response.json({ items: Array.from({ length: 100 }, (_, i) => event(`${++calls}-${i}`)), nextPageToken: 'more' }))
  const result = await listEvents('fake', range)
  assert.equal(result.events.length, 500)
  assert.equal(result.truncated, true)
})

test('Google 403 is an error rather than empty calendar', async () => {
  globalThis.fetch = async () => Response.json({ error: 'denied' }, { status: 403 })
  await assert.rejects(listEvents('fake', range), /Google 권한/)
})

test('failure on second page does not return partial results as complete', async () => {
  let calls = 0
  mockCalendarFetch(async () => ++calls === 1 ? Response.json({ items: [event('1')], nextPageToken: 'page2' }) : Response.json({}, { status: 500 }))
  await assert.rejects(listEvents('fake', range), /조회에 실패/)
})

test('reversed range sends no Google request', async () => {
  globalThis.fetch = async () => { throw new Error('must not call') }
  await assert.rejects(listEvents('fake', { ...range, start: range.end, end: range.start }), /날짜 범위/)
})

test('family calendar is scanned even when the primary calendar reaches its cap', async () => {
  globalThis.fetch = async url => {
    const path = new URL(url).pathname
    if (path.endsWith('/calendarList')) return Response.json({ items: [{ id: 'primary', summary: '기본', accessRole: 'owner' }, { id: 'family@example.com', summary: '가족', accessRole: 'reader' }] })
    if (path.includes('family%40example.com')) return Response.json({ items: [{ ...event('father'), summary: '장인생신 음력 10/10' }] })
    return Response.json({ items: Array.from({ length: 100 }, (_, i) => event(`${new URL(url).searchParams.get('pageToken') || 'first'}-${i}`)), nextPageToken: String(Number(new URL(url).searchParams.get('pageToken') || 0) + 1) })
  }
  const result = await listEvents('fake', range)
  assert.equal(result.events.length, 501)
  assert.equal(result.scope.calendarCount, 2)
  assert.equal(result.events.find(item => item.title.includes('장인생신')).calendarName, '가족')
  assert.equal(result.truncated, true)
})

test('calendar list pagination includes unselected and hidden calendars', async () => {
  let listPages = 0
  globalThis.fetch = async url => {
    const parsed = new URL(url)
    if (parsed.pathname.endsWith('/calendarList')) {
      assert.equal(parsed.searchParams.get('showHidden'), 'true')
      return Response.json(++listPages === 1 ? { items: [{ id: 'primary', accessRole: 'owner' }], nextPageToken: 'next' } : { items: [{ id: 'family', summary: '가족', accessRole: 'reader', selected: false, hidden: true }] })
    }
    return Response.json({ items: parsed.pathname.includes('/family/') ? [{ ...event('father'), summary: '장인생신' }] : [] })
  }
  const result = await listEvents('fake', range)
  assert.equal(listPages, 2)
  assert.equal(result.events.length, 1)
  assert.equal(result.events[0].title, '장인생신')
})

test('shared copies deduplicate by UID and occurrence start, not by title', async () => {
  globalThis.fetch = async url => {
    if (new URL(url).pathname.endsWith('/calendarList')) return Response.json({ items: [{ id: 'one' }, { id: 'two' }] })
    return Response.json({ items: [{ ...event('1'), iCalUID: 'shared-uid' }, { ...event('2'), iCalUID: 'shared-uid', start: { dateTime: '2026-11-12T14:00:00+09:00' } }, { ...event('3'), iCalUID: 'separate-uid' }] })
  }
  const result = await listEvents('fake', range)
  assert.equal(result.events.length, 3)
  assert.equal(result.scope.calendarCount, 2)
})

test('one inaccessible calendar is disclosed as partial, never silently omitted', async () => {
  globalThis.fetch = async url => {
    const path = new URL(url).pathname
    if (path.endsWith('/calendarList')) return Response.json({ items: [{ id: 'primary', summary: '기본' }, { id: 'family', summary: '가족' }] })
    return path.includes('/family/') ? Response.json({}, { status: 403 }) : Response.json({ items: [event('1')] })
  }
  const result = await listEvents('fake', range)
  assert.equal(result.events.length, 1)
  assert.deepEqual(result.scope.failedCalendars, ['가족'])
})

test('free/busy-only calendars are not treated as empty calendars', async () => {
  globalThis.fetch = async url => new URL(url).pathname.endsWith('/calendarList')
    ? Response.json({ items: [{ id: 'primary', accessRole: 'owner' }, { id: 'private', accessRole: 'freeBusyReader' }] })
    : Response.json({ items: [] })
  const result = await listEvents('fake', range)
  assert.equal(result.scope.skippedCalendars, 1)
  assert.equal(result.scope.calendarCount, 1)
})

test('all-day cards show only occupied dates, not the exclusive end date', () => {
  assert.equal(formatEventTime('2026-11-26', '2026-11-27'), '2026-11-26 · 하루 종일')
  assert.equal(formatEventTime('2026-11-26', '2026-11-29'), '2026-11-26 ~ 2026-11-28 · 하루 종일')
})

test('multi-day timed cards show both start and end dates', () => {
  const text = formatEventTime('2026-10-10T14:00:00+09:00', '2026-10-12T15:00:00+09:00')
  assert.match(text, /10월 10일/)
  assert.match(text, /10월 12일/)
})
