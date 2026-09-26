export function formatDate(value: string | Date): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return new Intl.DateTimeFormat('ko-KR', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'short', hour: 'numeric', minute: '2-digit' }).format(date)
}
export function formatEventTime(start: string, end: string): string {
  if (start.length === 10) {
    const last = end.length === 10 ? new Date(new Date(`${end}T00:00:00Z`).getTime() - 86400000).toISOString().slice(0, 10) : start
    return `${last > start ? `${start} ~ ${last}` : start} · 하루 종일`
  }
  if (!end) return formatDate(start)
  if (new Date(start).toDateString() !== new Date(end).toDateString()) return `${formatDate(start)} – ${formatDate(end)}`
  return `${formatDate(start)} – ${new Intl.DateTimeFormat('ko-KR', { hour: 'numeric', minute: '2-digit' }).format(new Date(end))}`
}
