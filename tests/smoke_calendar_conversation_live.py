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
for question in ['음력은 양력 날짜로 변경해서 다시 추려줘', '목록만 보여줘']:
    command = interpret_command(question, now=now, context=context)
    assert command['action'] == 'calendar_read' and command['reusePrevious'], command
    assert command['convertLunar'], command
    assert command['range'] == context['calendarCommand']['range'], command
    text, selected = calendar_answer({'command': command, 'events': events})
    father = next(item for item in selected if item['id'] == 'father')
    assert father['start'] == '2026-11-18T10:30:00+09:00', father
    mother = next(item for item in selected if item['id'] == 'mother')
    assert mother['start'] == '2026-12-18' and '변환 보류' not in text, text
    context['calendarCommand'] = command
    print({'lunar_followup': True, 'verified': True})
command = interpret_command('생일 목록을 모두 삭제해줘', now=now, context=context)
assert command['action'] == 'unknown' and command.get('clarification'), command
print({'unsupported_write_blocked': True, 'conversation_cases_passed': 11})
question = '- 2026-11-10 (화) 15:30–16:30 · 장모님 생신(음력) 이거 양력으로 변경해줘'
command = interpret_command(question, now=now, context=context)
assert command['action'] == 'calendar_read' and command['reusePrevious'], command
assert command['inspectTitle'] == '장모님 생신(음력)', command
assert command['range'] == context['calendarCommand']['range'], command
text, selected = calendar_answer({'command': command, 'events': events})
assert [item['id'] for item in selected] == ['mother'], selected
assert selected[0]['start'] == '2026-12-18' and '장인' not in text, text
context['calendarCommand'] = command
command = interpret_command('음력 10월 2일 평달이야', now=now, context=context)
assert command['action'] == 'calendar_read' and command['reusePrevious'], command
assert command['lunarDate'] == {'month': 10, 'day': 2, 'leap': False}, command
text, selected = calendar_answer({'command': command, 'events': events})
assert [item['id'] for item in selected] == ['mother'], selected
assert selected[0]['start'] == '2026-11-10' and '변환 보류' not in text, text
print({'specific_lunar_target_and_parameter_reply': True, 'conversation_cases_passed': 13})
command = interpret_command('앞으로 3개월 일정중 생일과 기념일만 추려주는데 음력 날짜는 양력으로 변경해서 추려줘', now=now, context={})
assert command['action'] == 'calendar_read' and command['convertLunar'], command
assert set(command['categoryFilter']) == {'birthday', 'anniversary'}, command
text, selected = calendar_answer({'command': command, 'events': events})
assert next(item for item in selected if item['id'] == 'mother')['start'] == '2026-12-18', text
assert len(selected) == 5 and '변환 보류' not in text, text
print({'combined_birthday_anniversary_lunar_query': True, 'conversation_cases_passed': 14})
