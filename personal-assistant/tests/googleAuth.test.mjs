import { readFile } from 'node:fs/promises'
import assert from 'node:assert/strict'
import { test } from 'node:test'
import ts from 'typescript'

const source = ts.transpileModule(await readFile(new URL('../src/services/googleAuthService.ts', import.meta.url), 'utf8'), { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 } }).outputText
test('Gmail and Calendar use their configured OAuth clients and verify granted scopes', async () => {
  const code = source.replaceAll('import.meta.env.VITE_GOOGLE_GMAIL_CLIENT_ID', "'gmail.apps.googleusercontent.com'").replaceAll('import.meta.env.VITE_GOOGLE_CLIENT_ID', "'calendar.apps.googleusercontent.com'")
  const auth = await import(`data:text/javascript;base64,${Buffer.from(code).toString('base64')}`)
  const originalWindow = globalThis.window
  const requests = []
  let deny = false
  globalThis.window = { google: { accounts: { oauth2: { initTokenClient(config) {
    requests.push(config)
    return { requestAccessToken() { config.callback({ access_token: 'fake', expires_in: 300, scope: deny ? 'openid' : config.scope }) } }
  } } } } }
  try {
    await auth.requestScope(auth.SCOPES.calendarRead)
    await auth.requestScope(auth.SCOPES.gmailRead)
    assert.equal(requests[0].client_id, 'calendar.apps.googleusercontent.com')
    assert.equal(requests[1].client_id, 'gmail.apps.googleusercontent.com')
    assert.equal(auth.getToken(auth.SCOPES.gmailRead), 'fake')
    deny = true
    await assert.rejects(auth.requestScope(auth.SCOPES.gmailRead), /권한이 허용되지/)
  } finally { globalThis.window = originalWindow }
})
