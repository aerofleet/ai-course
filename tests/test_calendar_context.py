import unittest
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import assistant_api as api
from calendar_assistant import calendar_answer


class CalendarContextTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 26, 14, 30, tzinfo=ZoneInfo('Asia/Seoul'))
        self.previous = {'action': 'calendar_read', 'range': {'start': '2026-09-26T14:30:00+09:00', 'end': '2026-12-26T14:30:00+09:00', 'label': '앞으로 3개월'}, 'importantOnly': True, 'categoryFilter': []}
        self.context = {'calendarCommand': self.previous, 'lastTopic': 'calendar', 'importantCategories': ['birthday', 'anniversary']}
        self.events = [
            {'id': 'father', 'title': '장인생신 음력 10/10', 'start': '2026-10-10T01:30:00Z', 'end': '2026-10-10T02:30:00Z', 'calendarName': '가족'},
            {'id': 'mother', 'title': '장모님 생신(음력)', 'start': '2026-11-10', 'end': '2026-11-11'},
            {'id': 'birthday', 'title': 'Happy birthday!', 'start': '2026-11-26', 'end': '2026-11-27'},
            {'id': 'nephew', 'title': '낙구생일', 'start': '2026-12-18', 'end': '2026-12-19'},
            {'id': 'anniversary', 'title': '결혼기념일', 'start': '2026-12-21T06:30:00Z', 'end': '2026-12-21T07:30:00Z'},
            {'id': 'payment', 'title': 'KT통신요금', 'start': '2026-11-26T16:00:00Z', 'end': '2026-11-26T17:00:00Z'},
        ]

    def model(self, **changes):
        value = {'action': 'calendar_read', 'range': {'kind': 'today', 'count': 0}, 'importantOnly': False,
                 'query': '', 'clarification': None, 'categoryFilter': [], 'importantCategories': None,
                 'title': None, 'start': None, 'end': None, 'inspectTitle': None, 'reusePrevious': False, 'listOnly': False}
        value.update(changes)
        return value

    def interpret(self, question, model=None, context=None):
        with patch.object(api, 'openai_response', return_value=model or self.model()):
            return api.interpret_command(question, now=self.now, context=context if context is not None else self.context)

    def data(self, command):
        return {'command': command, 'events': self.events, 'scope': {'calendarCount': 2, 'failedCalendars': [], 'skippedCalendars': 0}}

    def test_filter_followup_keeps_three_months_despite_model_today(self):
        command = self.interpret('생일과 기념일 목록만 추려줘')
        self.assertEqual(command['range'], self.previous['range'])
        self.assertTrue(command['reusePrevious'])
        self.assertEqual(command['categoryFilter'], ['birthday', 'anniversary'])
        text, selected = calendar_answer(self.data(command))
        self.assertEqual(len(selected), 5)
        self.assertIn('장인생신', text)
        self.assertNotIn('KT통신요금', text)
        self.assertNotIn('캘린더: 가족', text)

    def test_supported_omission_ignores_wrong_share_and_unsupported_flags(self):
        command = self.interpret('장인생신 음력 10/10 10월 10일 이게 앞에 뽑아준 중요 후보에서 누락이 되었어', self.model(action='unknown', shareWithTeam=True, unsupported=True, clarification='명령 해석이 필요합니다.'))
        self.assertEqual(command['action'], 'calendar_read')
        self.assertEqual(command['range'], self.previous['range'])
        self.assertEqual(command['inspectTitle'], '장인생신')

    def test_generic_list_followup_keeps_previous_filter(self):
        self.previous['categoryFilter'] = ['birthday', 'anniversary']
        command = self.interpret('목록만 추려줘')
        self.assertEqual(command['categoryFilter'], ['birthday', 'anniversary'])
        self.assertEqual(command['range'], self.previous['range'])

    def test_new_explicit_range_overrides_context(self):
        command = self.interpret('오늘 생일 목록만 추려줘')
        self.assertEqual(command['range']['label'], '오늘')
        self.assertFalse(command['reusePrevious'])

    def test_explicit_month_does_not_reuse_prior_range(self):
        model = self.model(range={'kind': 'dates', 'count': 0, 'dateFrom': '2026-10-01', 'dateTo': '2026-10-31'})
        command = self.interpret('10월 생일과 기념일 확인해줘', model)
        self.assertEqual(command['range']['start'][:10], '2026-10-01')
        self.assertFalse(command['reusePrevious'])

    def test_preference_statement_overrides_model_unknown(self):
        command = self.interpret('생일과 기념일이 나한테는 중요 일정이야', self.model(action='unknown', clarification='어떤 작업인가요?'))
        self.assertEqual(command['action'], 'preference_update')
        self.assertEqual(command['importantCategories'], ['birthday', 'anniversary'])

    def test_saved_preferences_select_all_family_events_on_repeated_question(self):
        question = '앞으로 3개월 내 중요한 일정 확인해줘'
        outputs = []
        for model in [self.model(), self.model(clarification='확인이 필요합니다.', categoryFilter=['payment']), self.model(action='preference_update')]:
            command = self.interpret(question, model)
            text, selected = calendar_answer(self.data(command))
            outputs.append(text)
            self.assertEqual([event['id'] for event in selected], ['father', 'mother', 'birthday', 'nephew', 'anniversary'])
        self.assertEqual(outputs[0], outputs[1])

    def test_short_omission_is_lookup_and_refreshes_same_range(self):
        command = self.interpret('장인생신이 누락 되어 있어', self.model(action='unknown', clarification='어떤 작업인가요?'))
        self.assertEqual(command['action'], 'calendar_read')
        self.assertEqual(command['inspectTitle'], '장인생신')
        self.assertEqual(command['range'], self.previous['range'])
        self.assertFalse(command['reusePrevious'])
        text, selected = calendar_answer(self.data(command))
        self.assertEqual([event['id'] for event in selected], ['father'])
        self.assertIn('찾았습니다', text)

    def test_pasted_card_omission_never_becomes_creation_or_invalid_date(self):
        question = '장인생신 음력 10/10 10월 10일 (토) 오전 10:30 – 오전 11:30 이게 앞에 뽑아준 중요 후보에서 누락이 되었어'
        command = self.interpret(question, self.model(action='calendar_create', start='10/10', end='invalid'))
        self.assertEqual(command['action'], 'calendar_read')
        self.assertEqual(command['inspectTitle'], '장인생신')
        self.assertEqual(command['range'], self.previous['range'])
        self.assertNotIn('create', command)

    def test_omission_missing_from_source_reports_lookup_scope(self):
        command = self.interpret('장인생신이 누락됐어')
        data = self.data(command)
        data['events'] = self.events[1:]
        text, selected = calendar_answer(data)
        self.assertFalse(selected)
        self.assertIn('찾지 못했습니다', text)
        self.assertIn('공유 권한', text)
        self.assertNotIn('등록된 일정이 없습니다', text)

    def test_ambiguous_omission_asks_title(self):
        command = self.interpret('그게 누락됐어')
        self.assertEqual(command['action'], 'unknown')
        self.assertIn('제목', command['clarification'])

    def test_no_prior_range_requests_period_instead_of_today(self):
        for model in [self.model(range={'kind': 'previous', 'count': 0}), self.model()]:
            command = self.interpret('생일과 기념일 목록만 추려줘', model, context={})
            self.assertEqual(command['action'], 'unknown')
            self.assertIn('기간', command['clarification'])

    def test_explicit_read_does_not_require_confirmation_or_user_timezone(self):
        command = self.interpret('앞으로 3개월 내 중요한 일정 확인해줘', self.model(action='unknown', clarification='시간대와 확인이 필요합니다.'))
        self.assertEqual(command['action'], 'calendar_read')
        self.assertIsNone(command['clarification'])

    def test_model_invalid_date_requests_clarification_instead_of_502(self):
        command = self.interpret('10월 일정 확인해줘', self.model(range={'kind': 'dates', 'count': 0, 'dateFrom': '10/10', 'dateTo': None}))
        self.assertEqual(command['action'], 'unknown')
        self.assertIn('기간', command['clarification'])

    def test_calendar_times_come_from_source_in_user_timezone(self):
        command = self.interpret('앞으로 3개월 생일과 기념일 확인해줘')
        text, _ = calendar_answer(self.data(command))
        self.assertIn('2026-10-10 (토) 10:30–11:30', text)
        self.assertIn('2026-12-21 (월) 15:30–16:30', text)
        self.assertIn('장인생신 음력 10/10', text)
        self.assertNotIn('양력 변환', text)

    def test_all_day_exclusive_end_is_not_shown_as_an_extra_day(self):
        text, _ = calendar_answer(self.data(self.interpret('생일 목록만 추려줘')))
        self.assertIn('2026-11-26 · 하루 종일 · Happy birthday!', text)
        self.assertNotIn('2026-11-26 ~ 2026-11-27', text)

    def test_no_category_matches_does_not_claim_no_calendar_events(self):
        data = self.data(self.interpret('생일 목록만 추려줘'))
        data['events'] = [self.events[-1]]
        text, _ = calendar_answer(data)
        self.assertIn('조회한 일정 1개 중', text)
        self.assertNotIn('등록된 일정이 없습니다', text)

    def test_partial_results_always_disclose_missing_calendars(self):
        data = self.data(self.interpret('생일 목록만 추려줘'))
        data['events'] = []
        data['scope']['failedCalendars'] = ['가족']
        text, _ = calendar_answer(data)
        self.assertIn('전체 결과로 단정할 수 없습니다', text)
        self.assertIn('조회 실패: 가족', text)
        self.assertNotIn('등록된 일정이 없습니다', text)

    def test_calendar_native_birthday_type_without_keyword_is_selected(self):
        data = self.data(self.interpret('생일 목록만 추려줘'))
        data['events'] = [{'id': 'native', 'title': '홍길동', 'eventType': 'birthday', 'start': '2026-10-10', 'end': '2026-10-11'}]
        text, selected = calendar_answer(data)
        self.assertEqual(len(selected), 1)
        self.assertIn('홍길동', text)

    def test_all_events_request_removes_prior_filter(self):
        command = self.interpret('앞으로 3개월 모든 일정 보여줘', self.model(importantOnly=True, categoryFilter=['birthday']))
        self.assertFalse(command['importantOnly'])
        _, selected = calendar_answer(self.data(command))
        self.assertEqual(len(selected), 6)

    def test_mail_about_birthdays_is_not_overridden_by_calendar_context(self):
        command = self.interpret('생일 축하 메일 요약해줘', self.model(action='gmail_summary', query='생일'))
        self.assertEqual(command['action'], 'gmail_summary')

    def test_generic_list_after_title_lookup_keeps_target(self):
        self.previous['inspectTitle'] = '장인생신'
        command = self.interpret('목록만 추려줘')
        _, selected = calendar_answer(self.data(command))
        self.assertEqual([event['id'] for event in selected], ['father'])

    def test_new_category_request_does_not_keep_old_title_lookup(self):
        self.previous['inspectTitle'] = '장인생신'
        command = self.interpret('생일과 기념일 목록만 추려줘', self.model(inspectTitle='장인생신'))
        _, selected = calendar_answer(self.data(command))
        self.assertEqual(len(selected), 5)


if __name__ == '__main__':
    unittest.main()
