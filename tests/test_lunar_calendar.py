import copy
import unittest
from korean_lunar_calendar import KoreanLunarCalendar
import test_calendar_context as context_tests
from calendar_assistant import calendar_answer


class LunarTests(unittest.TestCase):
    setUp = context_tests.CalendarContextTests.setUp
    model = context_tests.CalendarContextTests.model
    interpret = context_tests.CalendarContextTests.interpret
    data = context_tests.CalendarContextTests.data
    def test_korean_reference_dates(self):
        calendar = KoreanLunarCalendar()
        self.assertTrue(calendar.setLunarDate(2026, 1, 1, False))
        self.assertEqual(calendar.SolarIsoFormat(), '2026-02-17')
        self.assertTrue(calendar.setLunarDate(1956, 1, 21, False))
        self.assertEqual(calendar.SolarIsoFormat(), '1956-03-03')
        self.assertFalse(calendar.setLunarDate(2026, 10, 10, True))

    def test_conversion_preserves_source_and_duration(self):
        source = copy.deepcopy(self.events)
        command = self.interpret('음력은 양력 날짜로 변경해서 다시 추려줘', self.model(convertLunar=True, reusePrevious=True))
        text, selected = calendar_answer(self.data(command))
        father = next(item for item in selected if item['id'] == 'father')
        self.assertEqual(father['start'], '2026-11-18T10:30:00+09:00')
        self.assertEqual(father['end'], '2026-11-18T11:30:00+09:00')
        self.assertIn('변환 보류', text)
        self.assertEqual(self.events, source)
        self.assertEqual(calendar_answer(self.data(command)), (text, selected))

    def test_followup_remembers_conversion(self):
        self.previous['convertLunar'] = True
        command = self.interpret('목록만 추려줘')
        self.assertTrue(command['convertLunar'])
        self.assertEqual(command['range'], self.previous['range'])

    def test_already_solar_is_not_shifted_twice(self):
        self.events[0]['start'] = '2026-11-18T10:30:00+09:00'
        self.events[0]['end'] = '2026-11-18T11:30:00+09:00'
        command = {**self.previous, 'convertLunar': True}
        text, selected = calendar_answer(self.data(command))
        father = next(item for item in selected if item['id'] == 'father')
        self.assertEqual(father['start'], self.events[0]['start'])
        self.assertIn('이미 양력', text)

    def test_leap_ambiguity_keeps_registered_date(self):
        self.events = [{'id': 'a', 'title': '생신 음력 5/1', 'start': '2017-06-01', 'end': '2017-06-02'}]
        command = {**self.previous, 'convertLunar': True, 'range': {'start': '2017-05-01T00:00:00+09:00', 'end': '2017-08-01T00:00:00+09:00', 'label': '검증'}}
        text, selected = calendar_answer(self.data(command))
        self.assertIn('변환 보류', text)
        self.assertEqual(selected[0]['start'], '2017-06-01')

    def test_outside_range_disclosed(self):
        self.events[0]['title'] = '생신 음력 1/1'
        text, selected = calendar_answer(self.data({**self.previous, 'convertLunar': True}))
        self.assertNotIn('father', [item['id'] for item in selected])
        self.assertIn('제외했습니다', text)

    def test_semantic_followup_without_keyword(self):
        command = self.interpret('같은 조건으로 다시 보여줘', self.model(reusePrevious=True))
        self.assertEqual(command['range'], self.previous['range'])

    def test_unsupported_cannot_become_calendar_read(self):
        command = self.interpret('생일 목록을 모두 삭제해줘', self.model(action='unknown', unsupported=True, clarification='일정 삭제는 지원하지 않아요.'))
        self.assertEqual(command['action'], 'unknown')
        self.assertIn('삭제', command['clarification'])

    def test_conversion_without_context_asks_period(self):
        command = self.interpret('음력을 양력으로 바꿔줘', self.model(convertLunar=True), context={})
        self.assertEqual(command['action'], 'unknown')
        self.assertIn('기간', command['clarification'])
