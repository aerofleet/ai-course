"""Calendar facts and selection are rendered from source records, never generated."""
import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from lunar_calendar import convert_events

CATEGORY_LABELS = {
    'birthday': '생일·생신', 'anniversary': '기념일', 'deadline': '마감',
    'meeting': '회의·면접·시험', 'health': '병원·예약', 'payment': '결제', 'travel': '여행',
}
DEFAULT_IMPORTANT = list(CATEGORY_LABELS)
CATEGORY_PATTERNS = {
    'birthday': r'생일|생신|탄신|birthday|b[ -]?day',
    'anniversary': r'기념일|주년|anniversary',
    'deadline': r'마감|제출|접수.*종료|deadline|due date',
    'meeting': r'회의|미팅|면접|시험|발표|meeting|interview|exam',
    'health': r'병원|진료|검진|치과|예약|hospital|doctor|appointment',
    'payment': r'결제|납부|요금|보험료|청구|payment|bill',
    'travel': r'여행|항공|출국|입국|비행|flight|travel',
}


def categories(text):
    return [key for key, pattern in CATEGORY_PATTERNS.items() if re.search(pattern, text, re.I)]


def event_categories(event):
    found = categories(event.get('title', ''))
    if event.get('eventType') == 'birthday' or 'birthday' in categories(event.get('calendarName', '')):
        if 'birthday' not in found:
            found.append('birthday')
    return found


def checked_categories(value):
    if not isinstance(value, list) or len(value) > len(CATEGORY_LABELS) or any(item not in CATEGORY_LABELS for item in value):
        raise ValueError('invalid categories')
    return list(dict.fromkeys(value))


def compact_title(text):
    return re.sub(r'[\W_]+', '', text).casefold()


def omission_title(question):
    # Keep the title, not dates pasted from a result card or the Korean subject suffix.
    prefix = re.split(r'누락|빠졌|빠져|빠진|안\s*보', question, maxsplit=1)[0].strip(' “"‘\'')
    prefix = re.split(r'\s+(?:음력|양력|\d{1,2}(?:/|월))|\s+이게|\s+이\s+일정', prefix, maxsplit=1)[0]
    prefix = re.sub(r'(?:이|가|은|는)\s*$', '', prefix).strip()
    if prefix in ('', '이것', '그것', '이거', '그거', '이게', '그게') or len(prefix) > 100:
        return None
    return prefix


def select_events(events, command):
    if command.get('inspectTitle'):
        target = compact_title(command['inspectTitle'])
        return [event for event in events if target and target in compact_title(event['title'])]
    filters = command.get('categoryFilter', [])
    wanted = filters or (command.get('importantCategories', DEFAULT_IMPORTANT) if command.get('importantOnly') else [])
    return [event for event in events if not wanted or set(event_categories(event)).intersection(wanted)]


def event_start_key(event, zone):
    value = event.get('start', '')
    if len(value) == 10:
        return datetime.combine(date.fromisoformat(value), datetime.min.time(), zone).timestamp()
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('event time needs timezone')
    return parsed.timestamp()


def event_time(event, zone):
    start, end = event['start'], event.get('end')
    if len(start) == 10:
        first = date.fromisoformat(start)
        last = date.fromisoformat(end) - timedelta(days=1) if end and len(end) == 10 else first
        return f'{first.isoformat()} · 하루 종일' if last <= first else f'{first.isoformat()} ~ {last.isoformat()} · 하루 종일'
    first = datetime.fromisoformat(start.replace('Z', '+00:00'))
    if first.tzinfo is None:
        raise ValueError('event time needs timezone')
    first = first.astimezone(zone)
    weekdays = '월화수목금토일'
    result = f'{first:%Y-%m-%d} ({weekdays[first.weekday()]}) {first:%H:%M}'
    if end:
        last = datetime.fromisoformat(end.replace('Z', '+00:00'))
        if last.tzinfo is None:
            raise ValueError('event time needs timezone')
        last = last.astimezone(zone)
        result += f'–{last:%H:%M}' if first.date() == last.date() else f' ~ {last:%Y-%m-%d %H:%M}'
    return result


def calendar_answer(data):
    command, events = data['command'], data['events']
    zone = ZoneInfo(command.get('timezone', 'Asia/Seoul'))
    if not isinstance(events, list) or len(events) > 2000:
        raise ValueError('invalid events')
    for event in events:
        if not isinstance(event, dict) or not isinstance(event.get('title'), str) or not isinstance(event.get('start'), str):
            raise ValueError('invalid event')
    filtered, notes = select_events(events, command), []
    if command.get('convertLunar'):
        filtered, notes = convert_events(filtered, command, zone)
    selected = sorted(filtered, key=lambda event: (event_start_key(event, zone), event['title'], event.get('id', '')))
    if command.get('inspectTitle') and command.get('convertLunar') and len(selected) == 1 and selected[0].get('conversionNote', '').startswith('변환 보류'):
        event = selected[0]
        return (f'“{event["title"]}”의 등록일은 {event_time(event, zone)}입니다. 이 날짜가 이미 변환된 양력 날짜인지, 음력 날짜를 그대로 등록한 것인지 제목만으로는 알 수 없어요.\n'
                '실제 음력 생신 월·일을 알려 주세요. 예: “음력 10월 2일 평달이야”. 이 일정만 같은 조회 기간에서 변환해 드릴게요. 캘린더 원본은 변경하지 않습니다.'), selected
    scope = data.get('scope', {})
    partial = data.get('truncated') or scope.get('failedCalendars') or scope.get('skippedCalendars')
    lines = [f'조회 기간: {command["range"]["label"]} · 시간대: {zone.key}']
    if command['range'].get('start') and command['range'].get('end'):
        first = datetime.fromisoformat(command['range']['start']).astimezone(zone)
        last = datetime.fromisoformat(command['range']['end']).astimezone(zone)
        if last.time() == datetime.min.time():
            last -= timedelta(microseconds=1)
        lines.append(f'{first:%Y-%m-%d} ~ {last:%Y-%m-%d}')
    if command.get('inspectTitle'):
        lines.append(f'“{command["inspectTitle"]}”을 조회한 캘린더에서 {"찾았습니다" if selected else "찾지 못했습니다"}.')
    elif not events:
        lines.append('조회한 캘린더에서 등록된 일정을 찾지 못했습니다.' if partial else '조회한 캘린더에 등록된 일정이 없습니다.')
    elif not selected:
        lines.append(f'조회한 일정 {len(events)}개 중 요청한 기준에 해당하는 일정은 없습니다.')
    else:
        lines.append(f'조건에 맞는 일정 {len(selected)}개입니다.')
    if command.get('importantOnly') and not command.get('listOnly'):
        chosen = command.get('categoryFilter') or command.get('importantCategories', DEFAULT_IMPORTANT)
        lines.append('중요 일정 기준: ' + ', '.join(CATEGORY_LABELS[key] for key in chosen))
    for event in selected:
        lines.append(f'- {event_time(event, zone)} · {event["title"]}')
        if event.get('conversionNote'):
            lines.append('  ' + event['conversionNote'])
        if not command.get('listOnly'):
            if event.get('calendarName'):
                lines.append(f'  캘린더: {event["calendarName"]}')
            if event.get('location'):
                lines.append(f'  장소: {event["location"]}')
    if command.get('convertLunar'):
        lines.append('음력 표기 일정은 제목의 월·일을 사용하고, 월·일이 없으면 등록일의 월·일을 음력으로 해석했습니다. Google Calendar 원본은 변경하지 않았습니다.')
        lines.extend(notes)
    if scope.get('calendarCount'):
        lines.append(f'조회한 캘린더: {scope["calendarCount"]}개')
    if partial:
        lines.append('일부 일정 또는 캘린더를 확인하지 못했으므로 전체 결과로 단정할 수 없습니다.')
        if scope.get('failedCalendars'):
            lines.append('조회 실패: ' + ', '.join(scope['failedCalendars']))
    if command.get('inspectTitle') and not selected:
        lines.append('일정이 있는 캘린더의 공유 권한과 조회 기간을 확인해 주세요.')
    return '\n'.join(lines), selected
