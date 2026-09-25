import { classifyCommand } from './aiService'
import type { Command, MailItem } from '../types'
export function interpret(input: string): Command { return classifyCommand(input) }
export function summarizeMail(messages: MailItem[]): string {
  if (!messages.length) return '조건에 맞는 메일이 없어요.'
  return `${messages.length}개의 메일을 찾았어요. ${messages.slice(0, 3).map(m => `${m.subject}: ${m.snippet}`).join(' / ')}`
}
export function draftReply(message: MailItem): string {
  const subject = message.subject.replace(/^Re:\s*/i, '')
  return `제목: Re: ${subject}\n\n안녕하세요. 메일 확인했습니다.\n\n말씀해 주신 내용 검토 후 다시 연락드리겠습니다.\n\n감사합니다.`
}
