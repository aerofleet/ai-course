"""Explicit live OpenAI smoke check; not part of offline unit discovery."""
from assistant_api import answer_question, interpret_command
from datetime import datetime, timedelta

question = '앞으로 남은 3개월내에 있을 중요한 일정이 있는지 확인해줘'
command = interpret_command(question)
assert command['action'] == 'calendar_read', command
assert command['range']['label'] == '앞으로 3개월', command
assert command['importantOnly'], command
fixture_start = datetime.fromisoformat(command['range']['start']) + timedelta(days=30)
fixture_date = fixture_start.date().isoformat()
fixture_end = (fixture_start + timedelta(days=1)).date().isoformat()
answer = answer_question({'question': question, 'command': command, 'truncated': False,
                         'events': [{'id': 'fixture', 'title': '검증용 면접', 'start': fixture_date, 'end': fixture_end}]})
assert '면접' in answer, answer
assert '오늘은 등록된 일정이 없어요' not in answer, answer
print({'provider': 'openai', 'range': command['range'], 'fixture_answer_verified': True})
