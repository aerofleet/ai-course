"""Live assistant workflows. No checkpointing or token-bearing state persistence."""
import hashlib
import re
from datetime import datetime, timezone
from typing import TypedDict
import requests
from langgraph.graph import StateGraph, START, END


class AssistantState(TypedDict, total=False):
    phase: str
    data: dict
    token: str
    identity: str
    plan: dict
    event: dict
    output: dict


def interpret_node(state):
    from assistant_api import interpret_command, model_name
    data = state['data']
    return {'output': {'command': interpret_command(data['question'], data.get('timezone', 'Asia/Seoul'), context=data.get('context')), 'model': model_name(), 'workflow': 'langgraph'}}


def answer_node(state):
    from assistant_api import answer_question, model_name
    from calendar_assistant import calendar_answer
    data = state['data']
    if data.get('command', {}).get('action') == 'calendar_read':
        text, selected = calendar_answer(data)
        return {'output': {'answer': text, 'events': selected, 'workflow': 'langgraph'}}
    return {'output': {'answer': answer_question(data), 'model': model_name(), 'workflow': 'langgraph'}}


def validate_execution(state):
    from assistant_api import AssistantError, checked_emails
    data = state['data']
    if data.get('approved') is not True:
        raise AssistantError('일정과 참석자를 확인한 후 승인해 주세요.')
    operation_id = data.get('operationId', '')
    if not isinstance(operation_id, str) or not re.fullmatch(r'[a-zA-Z0-9-]{16,100}', operation_id):
        raise AssistantError('실행 작업 ID를 확인하지 못했어요.')
    create = data.get('create', {})
    if not isinstance(create, dict) or not isinstance(create.get('title'), str) or not 1 <= len(create['title'].strip()) <= 300:
        raise AssistantError('일정 제목을 확인해 주세요.')
    start, end = datetime.fromisoformat(create['start']), datetime.fromisoformat(create['end'])
    if start.tzinfo is None or end.tzinfo is None or end <= start or (end - start).total_seconds() > 7 * 86400:
        raise AssistantError('시간대가 있는 시작·종료 시간을 확인해 주세요.')
    attendees = checked_emails(create.get('attendees', []))
    event_id = hashlib.sha256((state['identity'] + ':' + operation_id).encode()).hexdigest()
    return {'plan': {'id': event_id, 'summary': create['title'].strip(), 'start': {'dateTime': start.isoformat()}, 'end': {'dateTime': end.isoformat()}, 'attendees': [{'email': email} for email in attendees]}}


def same_event(event, plan):
    try:
        return (event.get('status') != 'cancelled' and event.get('id') == plan['id'] and event.get('summary') == plan['summary']
                and all(datetime.fromisoformat(event[key]['dateTime'].replace('Z', '+00:00')) == datetime.fromisoformat(plan[key]['dateTime']) for key in ('start', 'end'))
                and {person['email'].lower() for person in event.get('attendees', [])} == {person['email'].lower() for person in plan['attendees']})
    except (ValueError, KeyError, TypeError):
        return False


def create_and_share(state):
    from assistant_api import AssistantError
    plan = state['plan']
    url = 'https://www.googleapis.com/calendar/v3/calendars/primary/events'
    headers = {'Authorization': 'Bearer ' + state['token']}
    try:
        # Look up the stable ID first: retries recover without sending another invitation.
        existing = requests.get(url + '/' + plan['id'], headers=headers, timeout=(10, 30))
        if existing.status_code == 200:
            event = existing.json()
            if not same_event(event, plan):
                raise AssistantError('동일 작업 ID에 다른 일정이 있어 실행하지 않았어요.', 409)
            return {'event': event}
        if existing.status_code != 404:
            raise AssistantError('기존 작업 결과를 확인하지 못했어요. Calendar 권한과 연결을 확인해 주세요.', 502)
        if datetime.fromisoformat(plan['start']['dateTime']) <= datetime.now(timezone.utc):
            raise AssistantError('시작 시간이 지난 일정은 생성하지 않아요. 미래 시간을 지정해 주세요.')
        response = requests.post(url, params={'sendUpdates': 'all' if plan['attendees'] else 'none'}, json=plan, headers=headers, timeout=(10, 30))
        if response.status_code == 409:
            response = requests.get(url + '/' + plan['id'], headers=headers, timeout=(10, 30))
        if not response.ok:
            raise AssistantError('일정 생성과 초대 요청을 확인하지 못했어요. 같은 작업으로 재시도해 주세요.', 502)
        event = response.json()
        if not same_event(event, plan):
            raise AssistantError('Google 실행 결과가 계획과 일치하지 않아요. 캘린더를 확인한 후 같은 작업으로 재시도해 주세요.', 502)
        return {'event': event}
    except (requests.RequestException, ValueError):
        raise AssistantError('Google 실행 결과를 확인하지 못했어요. 같은 확인 버튼으로 재시도하면 중복 생성을 방지합니다.', 502)


def report_execution(state):
    event, plan = state['event'], state['plan']
    item = {'id': event['id'], 'title': event['summary'], 'start': event['start']['dateTime'], 'end': event['end']['dateTime'], 'link': event.get('htmlLink')}
    answer = f'“{item["title"]}” 일정을 생성했습니다.'
    if plan['attendees']:
        answer += f' 팀 {len(plan["attendees"])}명에게 캘린더 초대 알림을 요청했습니다. 수신·열람·참석 수락 여부는 아직 확인하지 않았습니다.'
    return {'output': {'event': item, 'answer': answer, 'sharedWith': [person['email'] for person in plan['attendees']], 'workflow': 'langgraph'}}


builder = StateGraph(AssistantState)
builder.add_node('interpret', interpret_node)
builder.add_node('answer', answer_node)
builder.add_node('validate_execution', validate_execution)
builder.add_node('create_and_share', create_and_share)
builder.add_node('report_execution', report_execution)
builder.add_conditional_edges(START, lambda state: state['phase'], {'interpret': 'interpret', 'answer': 'answer', 'execute': 'validate_execution'})
builder.add_edge('interpret', END)
builder.add_edge('answer', END)
builder.add_edge('validate_execution', 'create_and_share')
builder.add_edge('create_and_share', 'report_execution')
builder.add_edge('report_execution', END)
assistant_graph = builder.compile()


def run_assistant(phase, data, token='', identity=''):
    return assistant_graph.invoke({'phase': phase, 'data': data, 'token': token, 'identity': identity})['output']
