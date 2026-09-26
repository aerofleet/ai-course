"""Offline lunar conversion of copies of source calendar records."""
import re
from datetime import date, datetime, timedelta
from korean_lunar_calendar import KoreanLunarCalendar


def convert_events(events, command, zone):
    first = datetime.fromisoformat(command['range']['start']).astimezone(zone)
    last = datetime.fromisoformat(command['range']['end']).astimezone(zone)
    result, notes = [], []
    for source in events:
        event = dict(source)
        text = source['title']
        if '음력' not in text:
            result.append(event)
            continue
        match = re.search(r'음력\s*[(:：]?\s*(윤달|윤|평달|평)?\s*(\d{1,2})\s*(?:/|월|\.)\s*(\d{1,2})', text)
        if not match:
            event['conversionNote'] = '변환 보류: 음력 월·일과 평달/윤달을 알려 주세요. 등록일을 유지했습니다.'
            result.append(event)
            continue
        word, month, day = match.groups()
        explicit = bool(word) or bool(re.search(r'윤달|평달', text))
        leap = bool((word and word.startswith('윤')) or '윤달' in text)
        candidates, ambiguous = [], False
        for year in range(first.year - 1, last.year + 1):
            dates = []
            for intercalation in ([leap] if explicit else [False, True]):
                calendar = KoreanLunarCalendar()
                if calendar.setLunarDate(year, int(month), int(day), intercalation):
                    solar = date.fromisoformat(calendar.SolarIsoFormat())
                    dates.append((solar, intercalation))
            if not explicit and len(dates) > 1 and any(first.date() <= solar <= last.date() for solar, _ in dates):
                ambiguous = True
            candidates.extend((solar, year, intercalation) for solar, intercalation in dates if first.date() <= solar <= last.date())
        if ambiguous or len(candidates) > 1 or first.year < 1000 or last.year > 2050:
            event['conversionNote'] = '변환 보류: 평달/윤달 또는 지원 연도(1000~2050)를 확인해 주세요. 등록일을 유지했습니다.'
            result.append(event)
            continue
        if not candidates:
            notes.append(f'“{text}”: 유효한 음력 날짜가 조회 기간에 없어 변환 목록에서 제외했습니다.')
            continue
        solar, year, intercalation = candidates[0]
        old = date.fromisoformat(source['start']) if len(source['start']) == 10 else datetime.fromisoformat(source['start'].replace('Z', '+00:00')).astimezone(zone).date()
        delta = timedelta(days=(solar - old).days)
        for key in ('start', 'end'):
            value = source.get(key)
            if value:
                event[key] = (date.fromisoformat(value) + delta).isoformat() if len(value) == 10 else (datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(zone) + delta).isoformat()
        stamp = datetime.combine(solar, datetime.min.time(), zone) if len(event['start']) == 10 else datetime.fromisoformat(event['start'])
        if not first <= stamp < last:
            notes.append(f'“{text}”: 변환 시각이 조회 기간 밖이어서 제외했습니다.')
            continue
        event['originalStart'] = source['start']
        event['conversionNote'] = f'음력 {year}-{int(month):02d}-{int(day):02d} ({"윤달" if intercalation else "평달"}) → 양력 {solar}' + (' · 이미 양력 등록일과 같습니다.' if old == solar else ' · 표시 날짜만 변환했습니다.')
        result.append(event)
    return result, notes
