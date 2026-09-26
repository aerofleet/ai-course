import type { CalendarItem, Command, MailItem } from '../types'
import { getToken, hasToken, SCOPES } from './googleAuthService'

async function assistantFetch<T>(path: string, data: unknown): Promise<T> {
  const scope = hasToken(SCOPES.calendarRead) ? SCOPES.calendarRead : SCOPES.gmailRead
  if (!hasToken(scope)) throw new Error('먼저 Google Calendar 또는 Gmail을 연결해 주세요.')
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), 90000)
  try {
    const response = await fetch(`/pipeline/api/assistant/${path}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken(scope)}` },
      body: JSON.stringify(data), signal: controller.signal,
    })
    if (!response.headers.get('Content-Type')?.includes('application/json')) throw new Error('비서 API에 연결하지 못했어요. 서버 배포 설정을 확인해 주세요.')
    const result = await response.json()
    if (!response.ok) throw new Error(result.error || 'AI 요청에 실패했어요. 잠시 뒤 다시 시도해 주세요.')
    return result as T
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw new Error('AI 응답 시간이 초과됐어요. 다시 시도해 주세요.')
    if (error instanceof TypeError) throw new Error('비서 서버에 연결하지 못했어요. 인터넷 연결을 확인해 주세요.')
    throw error
  } finally { window.clearTimeout(timeout) }
}

export async function interpret(question: string): Promise<Command> {
  type WireCommand = Omit<Command, 'create'> & { create?: { title: string; start: string; end: string } }
  const { command } = await assistantFetch<{ command: WireCommand }>('interpret', {
    question, timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  })
  return { ...command, create: command.create ? { ...command.create, start: new Date(command.create.start), end: new Date(command.create.end) } : undefined }
}

export async function answerQuestion(question: string, command: Command, results: { events?: CalendarItem[]; mails?: MailItem[]; truncated?: boolean }): Promise<string> {
  const { answer } = await assistantFetch<{ answer: string }>('answer', { question, command, ...results })
  return answer
}
