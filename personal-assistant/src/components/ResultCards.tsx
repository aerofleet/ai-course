import type { CalendarItem, MailItem } from '../types'
import { formatEventTime } from '../utils/format'

export function CalendarCards({ items }: { items: CalendarItem[] }) {
  return <div className="card-list">{items.length ? items.map(item => <article className="item-card" key={item.id}>
    <span className="item-icon calendar-icon">▦</span><div><h3>{item.title}</h3><p>{formatEventTime(item.start, item.end)}</p>{item.location && <p>장소 · {item.location}</p>}</div>
    {item.link && <a href={item.link} target="_blank" rel="noreferrer" aria-label={`${item.title} Google Calendar에서 열기`}>↗</a>}
  </article>) : <p className="empty">표시할 일정이 없어요.</p>}</div>
}

export function MailCards({ items }: { items: MailItem[] }) {
  return <div className="card-list">{items.length ? items.map(item => <article className="item-card" key={item.id}>
    <span className="item-icon mail-icon">✉</span><div><small>{item.from}</small><h3>{item.subject}</h3><p>{item.snippet}</p></div>
    <a href={`https://mail.google.com/mail/u/0/#all/${encodeURIComponent(item.id)}`} target="_blank" rel="noreferrer" aria-label={`${item.subject} Gmail에서 열기`}>↗</a>
  </article>) : <p className="empty">표시할 메일이 없어요.</p>}</div>
}
