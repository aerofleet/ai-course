import { readFile } from 'node:fs/promises'
import assert from 'node:assert/strict'
import { test } from 'node:test'
import ts from 'typescript'

const uri = code => `data:text/javascript;base64,${Buffer.from(code).toString('base64')}`
const source = ts.transpileModule(await readFile(new URL('../src/services/assistantService.ts', import.meta.url), 'utf8'), { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 } }).outputText
const scopes = { calendarRead: 'calendar.read', calendarWrite: 'calendar.write', gmailRead: 'gmail.read' }
const load = allowed => import(uri(source.replace("'./googleAuthService'", JSON.stringify(uri(`export const SCOPES=${JSON.stringify(scopes)}; export const hasToken=scope=>${allowed ? 'true' : "scope!==SCOPES.calendarWrite"}; export const getToken=scope=>scope;`)))))

test('approved creation sends attendees and the same retry ID with the write token', async () => {
  const originalFetch = globalThis.fetch, originalWindow = globalThis.window
  const requests = []
  globalThis.window = { setTimeout, clearTimeout }
  globalThis.fetch = async (url, init) => { requests.push({ url, init, body: JSON.parse(init.body) }); return Response.json({ event: { id: 'event' }, answer: '생성' }) }
  try {
    const { executeCreate } = await load(true)
    const plan = { title: '회의', start: new Date('2027-01-01T10:00:00+09:00'), end: new Date('2027-01-01T11:00:00+09:00'), attendees: ['team@example.com'], operationId: 'same-operation-id' }
    await executeCreate(plan)
    await executeCreate(plan)
    assert.equal(requests[0].url, '/pipeline/api/assistant/execute')
    assert.equal(requests[0].init.headers.Authorization, 'Bearer calendar.write')
    assert.equal(requests[0].body.approved, true)
    assert.deepEqual(requests[0].body.create.attendees, ['team@example.com'])
    assert.equal(requests[0].body.operationId, requests[1].body.operationId)
  } finally { globalThis.fetch = originalFetch; globalThis.window = originalWindow }
})

test('read scopes cannot authorize the execute request', async () => {
  const { executeCreate } = await load(false)
  await assert.rejects(executeCreate({ title: '회의', start: new Date(), end: new Date(), operationId: 'same-operation-id' }), /연결/)
})
