import { useState } from 'react'
import { disconnect, hasToken, requestScope, SCOPES } from '../services/googleAuthService'
export function useGoogleAuth() {
  const [, setVersion] = useState(0)
  const refresh = () => setVersion(v => v + 1)
  async function connectCalendar() { await requestScope(SCOPES.calendarRead); refresh() }
  async function connectGmail() { await requestScope(SCOPES.gmailRead); refresh() }
  function signOut() { disconnect(); refresh() }
  return { calendarConnected: hasToken(SCOPES.calendarRead), gmailConnected: hasToken(SCOPES.gmailRead), connectCalendar, connectGmail, signOut, refresh }
}
