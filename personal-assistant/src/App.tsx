import { useState } from 'react'
import { CalendarCards, MailCards } from './components/ResultCards'
import { useGoogleAuth } from './hooks/useGoogleAuth'
import { createEvent, listEvents } from './services/calendarService'
import { listMessages } from './services/gmailService'
import { getToken, requestScope, SCOPES } from './services/googleAuthService'
import { draftReply, interpret, summarizeMail } from './services/assistantService'
import type { Answer, CalendarItem, CreateRequest, MailItem } from './types'
import { formatDate } from './utils/format'

const suggestions = ['오늘 일정 알려줘', '이번 주 일정 보여줘', '최근 중요한 메일 요약해줘', '내일 오후 2시에 회의 추가해줘']
let nextAnswerId = 0

export default function App() {
  const auth = useGoogleAuth()
  const [input, setInput] = useState('')
  const [answers, setAnswers] = useState<Answer[]>([])
  const [events, setEvents] = useState<CalendarItem[]>([])
  const [mails, setMails] = useState<MailItem[]>([])
  const [pending, setPending] = useState<CreateRequest | null>(null)
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState('')

  function addAnswer(question: string, text: string, kind: Answer['kind'] = 'success') {
    setAnswers(previous => [{ id: ++nextAnswerId, question, text, kind }, ...previous])
  }
  async function connect(kind: 'calendar' | 'gmail') {
    try { setNotice(''); if (kind === 'calendar') await auth.connectCalendar(); else await auth.connectGmail(); setNotice(`${kind === 'calendar' ? 'Calendar' : 'Gmail'} 연결이 완료됐어요.`) }
    catch (error) { setNotice(messageOf(error)) }
  }
  async function run(commandText = input) {
    const question = commandText.trim()
    if (!question || busy) return
    setInput(''); setBusy(true); setPending(null)
    const command = interpret(question)
    try {
      if (command.action === 'calendar_read') {
        if (!auth.calendarConnected) throw new Error('먼저 Google Calendar를 연결해 주세요.')
        const items = await listEvents(getToken(SCOPES.calendarRead), command.period || 'today')
        setEvents(items)
        addAnswer(question, items.length ? `${command.period === 'week' ? '이번 주' : '오늘'} 일정 ${items.length}개를 찾았어요.` : `${command.period === 'week' ? '이번 주' : '오늘'}은 등록된 일정이 없어요.`)
      } else if (command.action === 'calendar_create') {
        if (!auth.calendarConnected) throw new Error('먼저 Google Calendar를 연결해 주세요.')
        if (!command.create) throw new Error('일정 시간을 이해하지 못했어요. “내일 오후 2시에 회의 추가해줘”처럼 입력해 주세요.')
        if (command.create.start.getTime() <= Date.now()) throw new Error('지난 시간에는 일정을 만들 수 없어요. 미래 시간을 입력해 주세요.')
        setPending(command.create)
        addAnswer(question, `“${command.create.title}” 일정을 ${formatDate(command.create.start)}에 1시간으로 만들까요? 아래에서 확인해 주세요.`, 'info')
      } else if (command.action === 'gmail_search' || command.action === 'gmail_summary' || command.action === 'reply_draft') {
        if (!auth.gmailConnected) throw new Error('먼저 Gmail을 연결해 주세요.')
        const query = command.query || ''
        const items = await listMessages(getToken(SCOPES.gmailRead), query, command.action === 'gmail_search' ? 8 : 5)
        setMails(items)
        if (command.action === 'reply_draft') addAnswer(question, items.length ? `가장 최근 메일을 바탕으로 만든 답장 초안입니다. 내용을 확인하고 직접 보내세요.\n\n${draftReply(items[0])}` : '답장할 메일을 찾지 못했어요.')
        else if (command.action === 'gmail_summary') addAnswer(question, summarizeMail(items))
        else addAnswer(question, items.length ? `메일 ${items.length}개를 찾았어요.` : '조건에 맞는 메일이 없어요.')
      } else addAnswer(question, '이 명령은 아직 이해하지 못했어요. 아래 예시 문장을 눌러 시도해 주세요.', 'info')
    } catch (error) { addAnswer(question, messageOf(error), 'error'); auth.refresh() }
    finally { setBusy(false) }
  }
  async function confirmCreate() {
    if (!pending || busy) return
    const requested = pending
    setBusy(true); setPending(null)
    try {
      if (!auth.calendarConnected) throw new Error('Calendar 연결이 만료됐어요. 다시 연결해 주세요.')
      // 권한 요청은 확인 버튼 클릭 이벤트에서 바로 시작합니다.
      await requestScope(SCOPES.calendarWrite)
      const created = await createEvent(getToken(SCOPES.calendarWrite), requested)
      setEvents(previous => [created, ...previous])
      addAnswer('일정 생성 확인', `“${created.title}” 일정을 만들었어요.`)
    } catch (error) { addAnswer('일정 생성 확인', messageOf(error), 'error'); setPending(requested) }
    finally { setBusy(false) }
  }
  function signOut() { auth.signOut(); setEvents([]); setMails([]); setPending(null); setNotice('Google 연결을 해제했어요.') }

  return <div className="app-shell">
    <header className="topbar"><div className="brand"><span className="brand-mark">✦</span><span>하루비서</span></div><span className="top-note">당신의 하루를 가볍게</span></header>
    <main className="layout">
      <section className="hero"><div className="eyebrow">MY DAILY ASSISTANT</div><h1>바쁜 하루,<br/><em>말 한마디로 정리해요.</em></h1><p>일정 확인부터 중요한 메일 정리까지, 필요한 일을 편하게 부탁해 보세요.</p></section>
      <section className="connect-panel" aria-label="Google 서비스 연결"><div><h2>Google 서비스 연결</h2><p>필요한 서비스만 선택해서 연결할 수 있어요.</p></div><div className="connect-actions"><button className={auth.calendarConnected ? 'connected' : ''} onClick={() => void connect('calendar')}>{auth.calendarConnected ? '✓ Calendar 연결됨' : '▦ Calendar 연결'}</button><button className={auth.gmailConnected ? 'connected' : ''} onClick={() => void connect('gmail')}>{auth.gmailConnected ? '✓ Gmail 연결됨' : '✉ Gmail 연결'}</button>{(auth.calendarConnected || auth.gmailConnected) && <button className="text-button" onClick={signOut}>연결 해제</button>}</div></section>
      {notice && <p className="notice" role="status">{notice}</p>}
      <section className="composer" aria-label="비서에게 명령하기"><div className="composer-heading"><span className="assistant-avatar">✦</span><div><h2>무엇을 도와드릴까요?</h2><p>평소 말하듯 편하게 입력해 주세요.</p></div></div><form onSubmit={event => { event.preventDefault(); void run() }}><label className="sr-only" htmlFor="command">명령 입력</label><input id="command" value={input} onChange={event => setInput(event.target.value)} placeholder="예: 오늘 일정 알려줘"/><button type="submit" disabled={busy || !input.trim()}>{busy ? '처리 중' : '보내기'} <span>↗</span></button></form><div className="suggestions">{suggestions.map(suggestion => <button key={suggestion} onClick={() => void run(suggestion)} disabled={busy}>{suggestion}</button>)}</div></section>
      {pending && <section className="confirm-card" role="dialog" aria-label="일정 생성 확인"><div><strong>일정을 추가할까요?</strong><p>{pending.title} · {formatDate(pending.start)} · 1시간</p></div><div><button onClick={() => setPending(null)}>취소</button><button className="primary" onClick={() => void confirmCreate()} disabled={busy}>확인하고 추가</button></div></section>}
      <div className="content-grid"><section className="results panel"><div className="section-title"><span className="section-icon purple">✦</span><div><h2>비서의 답변</h2><p>요청한 내용과 결과를 볼 수 있어요.</p></div></div><div className="answer-list">{answers.length ? answers.map(answer => <article className={`answer ${answer.kind}`} key={answer.id}><small>“{answer.question}”</small><p>{answer.text}</p></article>) : <div className="empty-state"><span>✦</span><p>첫 명령을 입력하면<br/>여기에 답변이 나타나요.</p></div>}</div></section><div className="side-stack"><section className="panel"><div className="section-title"><span className="section-icon blue">▦</span><div><h2>캘린더 일정</h2><p>조회한 일정이 여기에 표시돼요.</p></div></div><CalendarCards items={events}/></section><section className="panel"><div className="section-title"><span className="section-icon coral">✉</span><div><h2>Gmail 메일</h2><p>조회한 메일이 여기에 표시돼요.</p></div></div><MailCards items={mails}/></section></div></div>
      <footer>개인정보는 이 브라우저 화면에서만 처리됩니다. 로그인 권한은 화면을 새로고침하면 사라집니다.</footer>
    </main>
  </div>
}
function messageOf(error: unknown): string { return error instanceof Error ? error.message : '요청을 처리하지 못했어요. 다시 시도해 주세요.' }
