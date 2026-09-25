export function formatDate(value: string | Date): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return new Intl.DateTimeFormat('ko-KR', { month: 'long', day: 'numeric', weekday: 'short', hour: 'numeric', minute: '2-digit' }).format(date)
}
export function formatEventTime(start: string, end: string): string {
  if (start.length === 10) return `${start} · 하루 종일`
  return `${formatDate(start)} – ${new Intl.DateTimeFormat('ko-KR', { hour: 'numeric', minute: '2-digit' }).format(new Date(end))}`
}
