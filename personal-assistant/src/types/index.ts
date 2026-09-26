export type Action = 'calendar_read' | 'calendar_create' | 'gmail_search' | 'gmail_summary' | 'reply_draft' | 'preference_update' | 'unknown'
export type CalendarCategory = 'birthday' | 'anniversary' | 'deadline' | 'meeting' | 'health' | 'payment' | 'travel'
export interface DateRange { start: string; end: string; label: string }
export interface CalendarItem { id: string; title: string; start: string; end: string; location?: string; link?: string; calendarName?: string; eventType?: string }
export interface MailItem { id: string; from: string; subject: string; snippet: string; date: string }
export interface CreateRequest { title: string; start: Date; end: Date }
export interface Command { action: Action; range?: DateRange; importantOnly?: boolean; clarification?: string | null; query?: string; create?: CreateRequest; categoryFilter?: CalendarCategory[]; importantCategories?: CalendarCategory[]; timezone?: string; reusePrevious?: boolean; listOnly?: boolean; inspectTitle?: string | null }
export interface CalendarScope { calendarCount: number; failedCalendars: string[]; skippedCalendars: number }
export interface CalendarResults { events: CalendarItem[]; truncated: boolean; scope: CalendarScope }
export interface ConversationContext { calendarCommand?: Command; importantCategories?: CalendarCategory[]; lastTopic?: 'calendar' | 'mail' }
export interface CalendarSnapshot { command: Command; results: CalendarResults }
export interface Answer { id: number; question: string; text: string; kind: 'success' | 'error' | 'info' }
export interface Command { convertLunar?: boolean; lunarDate?: { month: number; day: number; leap: boolean | null } | null }
export interface CalendarItem { originalStart?: string; conversionNote?: string }
