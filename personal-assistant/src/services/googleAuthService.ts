export const SCOPES = {
  calendarRead: 'https://www.googleapis.com/auth/calendar.readonly',
  calendarWrite: 'https://www.googleapis.com/auth/calendar.events',
  gmailRead: 'https://www.googleapis.com/auth/gmail.readonly',
} as const
type TokenResponse = { access_token?: string; expires_in?: number; scope?: string; error?: string }
type TokenClient = { callback: (response: TokenResponse) => void; error_callback?: (error: { type: string }) => void; requestAccessToken: (options?: { prompt?: string }) => void }
type GoogleWindow = Window & { google?: { accounts: { oauth2: { initTokenClient: (config: { client_id: string; scope: string; callback: (response: TokenResponse) => void }) => TokenClient; revoke: (token: string, callback: () => void) => void } } } }
const tokens = new Map<string, { value: string; expiresAt: number }>()
const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined

export function hasToken(scope: string): boolean {
  const token = tokens.get(scope)
  return !!token && Date.now() < token.expiresAt
}
export function getToken(scope: string): string {
  const token = tokens.get(scope)
  if (!token || Date.now() >= token.expiresAt) {
    tokens.delete(scope)
    throw new Error('접속 권한이 만료됐어요. Google 연결 버튼을 다시 눌러주세요.')
  }
  return token.value
}
export async function requestScope(scope: string): Promise<void> {
  if (!clientId || clientId.includes('your-web-oauth')) throw new Error('Google Client ID가 설정되지 않았어요. README의 설정 방법을 확인해 주세요.')
  const google = (window as GoogleWindow).google
  if (!google?.accounts.oauth2) throw new Error('Google 로그인 도구를 불러오지 못했어요. 인터넷 연결을 확인하고 새로고침해 주세요.')
  await new Promise<void>((resolve, reject) => {
    const client = google.accounts.oauth2.initTokenClient({ client_id: clientId, scope, callback: response => {
      if (response.error || !response.access_token) { reject(new Error('Google 권한 동의가 완료되지 않았어요. 다시 시도해 주세요.')); return }
      if (!response.scope?.split(' ').includes(scope)) { reject(new Error('요청한 Google 권한이 허용되지 않았어요.')); return }
      tokens.set(scope, { value: response.access_token, expiresAt: Date.now() + (Number(response.expires_in) || 3600) * 1000 - 60000 })
      resolve()
    } })
    client.error_callback = () => reject(new Error('Google 로그인 창이 닫혔거나 차단됐어요. 팝업 허용 후 다시 시도해 주세요.'))
    client.requestAccessToken({ prompt: '' })
  })
}
export function disconnect(): void {
  const google = (window as GoogleWindow).google
  for (const { value } of tokens.values()) google?.accounts.oauth2.revoke(value, () => {})
  tokens.clear()
}
