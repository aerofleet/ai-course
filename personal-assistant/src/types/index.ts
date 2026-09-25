export type Action = 'calendar_read' | 'calendar_create' | 'gmail_search' | 'gmail_summary' | 'reply_draft' | 'unknown'
export type Period = 'today' | 'week'
export interface CalendarItem { id: string; title: string; start: string; end: string; location?: string; link?: string }
export interface MailItem { id: string; from: string; subject: string; snippet: string; date: string }
export interface CreateRequest { title: string; start: Date; end: Date }
export interface Command { action: Action; period?: Period; query?: string; create?: CreateRequest }
export interface Answer { id: number; question: string; text: string; kind: 'success' | 'error' | 'info' }
