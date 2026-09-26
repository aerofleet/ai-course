"""Explicit live OpenAI evaluation using synthetic calendars and a fixed clock."""
from datetime import datetime
from zoneinfo import ZoneInfo

from assistant_api import interpret_command
from calendar_assistant import DEFAULT_IMPORTANT, calendar_answer

now = datetime(2026, 9, 26, 14, 30, tzinfo=ZoneInfo('Asia/Seoul'))
events = [
    {'id': 'father', 'title': '장인생신 음력 10/10', 'start': '2026-10-10T01:30:00Z', 'end': '2026-10-10T02:30:00Z'},
    {'id': 'mother', 'title': '장모님 생신(음력)', 'start': '2026-11-10', 'end': '2026-11-11'},
    {'id': 'birthday', 'title': 'Happy birthday!', 'start': '2026-11-26', 'end': '2026-11-27'},
    {'id': 'nephew', 'title': '검증용 생일', 'start': '2026-12-18', 'end': '2026-12-19'},
    {'id': 'anniversary', 'title': '결혼기념일', 'start': '2026-12-21T06:30:00Z', 'end': '2026-12-21T07:30:00Z'},
    {'id': 'payment', 'title': 'KT통신요금', 'start': '2026-11-26T16:00:00Z', 'end': '2026-11-26T17:00:00Z'},
]
context = {'importantCategories': DEFAULT_IMPORTANT, 'lastTopic': 'calendar'}
questions = [
    '앞으로 3개월 내 중요한 일정 확인해줘',
    '장인생신 음력 10/10 10월 10일 (토) 오전 10:30 – 오전 11:30 이게 앞에 뽑아준 중요 후보에서 누락이 되었어',
    '장인생신이 누락 되어 있어',
    '앞으로 3개월 내에 있는 생일과 기념일 확인해줘',
    '생일과 기념일 목록만 추려줘',
    '생일과 기념일이 나한테는 중요 일정이야',
    '앞으로 3개월 내 중요한 일정 확인해줘',
    '앞으로 3개월 내 중요한 일정 확인해줘',
]
answers = []
for index, question in enumerate(questions):
    command = interpret_command(question, now=now, context=context)
    if index == 5:
        assert command['action'] == 'preference_update', command
        assert command['importantCategories'] == ['birthday', 'anniversary'], command
        context['importantCategories'] = command['importantCategories']
    else:
        assert command['action'] == 'calendar_read', command
        assert command['range']['start'] == '2026-09-26T14:30:00+09:00', command
        assert command['range']['end'] == '2026-12-26T14:30:00+09:00', command
        assert not command.get('clarification'), command
        answer, selected = calendar_answer({'command': command, 'events': events})
        ids = [item['id'] for item in selected]
        assert 'father' in ids, ids
        if index in (1, 2):
            assert ids == ['father'], ids
            assert '10:30–11:30' in answer, answer
        if index in (3, 4, 6, 7):
            assert ids == ['father', 'mother', 'birthday', 'nephew', 'anniversary'], ids
        if index == 4:
            assert command['listOnly'] and command['reusePrevious'], command
        context.update(calendarCommand=command, lastTopic='calendar')
        answers.append(answer)
    print({'case': index + 1, 'action': command['action'], 'verified': True})
assert answers[-1] == answers[-2], 'Repeated query changed the answer'
print({'provider': 'openai', 'conversation_cases_passed': 8, 'source_dates_verified': True})
