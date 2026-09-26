"""Offline lunar conversion of copies of source calendar records."""
import re
import unicodedata
from datetime import date, datetime, timedelta
from korean_lunar_calendar import KoreanLunarCalendar


def convert_events(events, command, zone):
    first = datetime.fromisoformat(command['range']['start']).astimezone(zone)
    last = datetime.fromisoformat(command['range']['end']).astimezone(zone)
    result, notes = [], []
    for source in events:
        event = dict(source)
        text = unicodedata.normalize('NFKC', source['title'])
        text = re.sub(r'음\s+력', '음력', text)
        override = command.get('lunarDate') if command.get('inspectTitle') else None
        if '음력' not in text and not override:
            result.append(event)
            continue
        match = re.search(r'음력[\s():：\[\]{}]*\s*(윤달|윤|평달|평)?\s*(\d{1,2})\s*(?:/|월|\.)\s*(\d{1,2})', text)
        registered_basis = not match and not override
        old = date.fromisoformat(source['start']) if len(source['start']) == 10 else datetime.fromisoformat(source['start'].replace('Z', '+00:00')).astimezone(zone).date()
        if override:
            month, day = override['month'], override['day']
            if not isinstance(month, int) or not isinstance(day, int) or not 1 <= month <= 12 or not 1 <= day <= 30 or override.get('leap') not in (True, False, None):
                raise ValueError('invalid lunar date')
            explicit, leap = override.get('leap') is not None, override.get('leap') is True
        elif match:
            word, month, day = match.groups()
            explicit = bool(word) or bool(re.search(r'윤달|평달', text))
            leap = bool((word and word.startswith('윤')) or '윤달' in text)
        else:
            month, day = old.month, old.day
            explicit = bool(re.search(r'윤달|평달', text))
            leap = '윤달' in text
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
        if registered_basis:
            event['conversionNote'] += f' · 제목의 음력 표기에 따라 등록일 {old.month}/{old.day}을 음력 월·일로 사용했습니다.'
        result.append(event)
    return result, notes
