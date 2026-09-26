import { readFile } from 'node:fs/promises'
import assert from 'node:assert/strict'
import { afterEach, test } from 'node:test'
import ts from 'typescript'

const compile = text => ts.transpileModule(text, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 } }).outputText
const uri = code => `data:text/javascript;base64,${Buffer.from(code).toString('base64')}`
const api = uri(compile(await readFile(new URL('../src/services/api.ts', import.meta.url), 'utf8')))
const source = compile(await readFile(new URL('../src/services/calendarService.ts', import.meta.url), 'utf8')).replace("'./api'", JSON.stringify(api))
const { listEvents } = await import(uri(source))
const originalFetch = globalThis.fetch
afterEach(() => { globalThis.fetch = originalFetch })
const range = { start: '2026-09-26T14:30:00+09:00', end: '2026-12-26T14:30:00+09:00', label: '앞으로 3개월' }
const event = id => ({ id, summary: '다음 달 면접', start: { dateTime: '2026-10-12T14:00:00+09:00' } })

test('three-month range reaches Google unchanged and follows pagination', async () => {
  const urls = []
  globalThis.fetch = async url => {
    urls.push(new URL(url))
    return Response.json(urls.length === 1 ? { items: [event('1')], nextPageToken: 'page2' } : { items: [event('2')] })
  }
  const result = await listEvents('fake', range)
  assert.equal(urls[0].searchParams.get('timeMin'), range.start)
  assert.equal(urls[0].searchParams.get('timeMax'), range.end)
  assert.equal(urls[1].searchParams.get('pageToken'), 'page2')
  assert.equal(result.events.length, 2)
  assert.equal(result.truncated, false)
})

test('500-event cap reports incomplete lookup', async () => {
  let calls = 0
  globalThis.fetch = async () => Response.json({ items: Array.from({ length: 100 }, (_, i) => event(`${++calls}-${i}`)), nextPageToken: 'more' })
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
  globalThis.fetch = async () => ++calls === 1 ? Response.json({ items: [event('1')], nextPageToken: 'page2' }) : Response.json({}, { status: 500 })
  await assert.rejects(listEvents('fake', range), /HTTP 500/)
})

test('reversed range sends no Google request', async () => {
  globalThis.fetch = async () => { throw new Error('must not call') }
  await assert.rejects(listEvents('fake', { ...range, start: range.end, end: range.start }), /날짜 범위/)
})
