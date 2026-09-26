import os
import unittest
from datetime import datetime
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

import assistant_api as api
from webapp import app


class AssistantTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 26, 14, 30, tzinfo=ZoneInfo('Asia/Seoul'))
        self.client = app.test_client()
        api._limits.clear()

    def command(self, kind='next_months', count=3):
        return {'action': 'calendar_read', 'range': {'kind': kind, 'count': count, 'dateFrom': None, 'dateTo': None},
                'importantOnly': True, 'query': '', 'title': None, 'start': None, 'end': None, 'clarification': None}

    def test_original_three_month_question_preserves_range(self):
        with patch.object(api, 'openai_response', return_value=self.command()) as llm:
            command = api.interpret_command('앞으로 남은 3개월내에 있을 중요한 일정이 있는지 확인해줘', now=self.now)
        self.assertEqual(command['range']['start'], '2026-09-26T14:30:00+09:00')
        self.assertEqual(command['range']['end'], '2026-12-26T14:30:00+09:00')
        self.assertTrue(command['importantOnly'])
        self.assertIn('3개월', llm.call_args.args[1]['question'])

    def test_end_of_month_is_clamped(self):
        now = self.now.replace(month=1, day=31)
        result = api.date_range(self.command(count=1)['range'], now)
        self.assertEqual(result['end'], '2026-02-28T14:30:00+09:00')

    def test_explicit_range_includes_last_day(self):
        result = api.date_range({'kind': 'dates', 'count': 0, 'dateFrom': '2026-10-01', 'dateTo': '2026-10-31'}, self.now)
        self.assertEqual(result['end'], '2026-11-01T00:00:00+09:00')

    def test_today_tomorrow_week_and_relative_units(self):
        expected = {'today': ('2026-09-26', '2026-09-27'), 'tomorrow': ('2026-09-27', '2026-09-28'),
                    'this_week': ('2026-09-21', '2026-09-28'), 'next_week': ('2026-09-28', '2026-10-05'),
                    'next_days': ('2026-09-26', '2026-09-29'), 'next_weeks': ('2026-09-26', '2026-10-17')}
        for kind, (start, end) in expected.items():
            with self.subTest(kind=kind):
                result = api.date_range(self.command(kind)['range'], self.now)
                self.assertTrue(result['start'].startswith(start))
                self.assertTrue(result['end'].startswith(end))

    def test_reversed_and_excessive_ranges_rejected(self):
        for value in [self.command(count=13)['range'], self.command('next_weeks', 100)['range'],
                      {'kind': 'dates', 'count': 0, 'dateFrom': '2026-10-31', 'dateTo': '2026-10-01'}]:
            with self.assertRaises(api.AssistantError):
                api.date_range(value, self.now)

    def test_empty_result_mentions_requested_period_without_llm(self):
        with patch.object(api, 'openai_response') as llm:
            result = api.answer_question({'question': '3개월 일정', 'command': {'action': 'calendar_read', 'range': {'label': '앞으로 3개월'}}, 'events': []})
        self.assertIn('앞으로 3개월', result)
        self.assertNotIn('오늘', result)
        llm.assert_not_called()

    def test_next_month_event_is_rendered_without_answer_model(self):
        data = {'question': '3개월 중요한 일정', 'command': {'action': 'calendar_read', 'importantOnly': True, 'range': {'label': '앞으로 3개월'}},
                'events': [{'title': '면접', 'start': '2026-10-12T14:00:00+09:00'}]}
        with patch.object(api, 'openai_response', return_value='10월 12일 면접') as llm:
            self.assertIn('면접', api.answer_question(data))
        llm.assert_not_called()

    def test_creation_keeps_explicit_duration_and_never_writes(self):
        result = self.command()
        result.update(action='calendar_create', title='회의', start='2026-09-27T14:00:00+09:00', end='2026-09-27T16:00:00+09:00')
        with patch.object(api, 'openai_response', return_value=result), patch.object(api.requests, 'post') as google:
            command = api.interpret_command('내일 오후 2시부터 4시 회의', now=self.now)
        self.assertTrue(command['create']['end'].endswith('16:00:00+09:00'))
        google.assert_not_called()

    def test_missing_token_blocks_openai(self):
        with patch.object(api, 'openai_response') as llm:
            response = self.client.post('/api/assistant/interpret', json={'question': '일정'})
        self.assertEqual(response.status_code, 401)
        llm.assert_not_called()

    def test_wrong_client_expired_token_and_missing_scope_block_openai(self):
        for info in [{'aud': 'other', 'scope': 'https://www.googleapis.com/auth/calendar.readonly', 'expires_in': '300'},
                     {'aud': 'client', 'scope': 'https://www.googleapis.com/auth/calendar.readonly', 'expires_in': '0'},
                     {'aud': 'client', 'scope': 'openid', 'expires_in': '300'}]:
            with patch.dict(os.environ, {'ASSISTANT_GOOGLE_CLIENT_ID': 'client'}), patch.object(api.requests, 'get', return_value=Mock(ok=True, json=lambda: info)), patch.object(api, 'openai_response') as llm:
                response = self.client.post('/api/assistant/interpret', json={'question': '일정'}, headers={'Authorization': 'Bearer fake'})
            self.assertEqual(response.status_code, 401)
            llm.assert_not_called()

    def test_valid_google_session_calls_openai(self):
        info = {'aud': 'client', 'scope': 'https://www.googleapis.com/auth/calendar.readonly', 'expires_in': '300', 'sub': 'user'}
        with patch.dict(os.environ, {'ASSISTANT_GOOGLE_CLIENT_ID': 'client'}), patch.object(api.requests, 'get', return_value=Mock(ok=True, json=lambda: info)), patch.object(api, 'openai_response', return_value=self.command()):
            response = self.client.post('/api/assistant/interpret', json={'question': '3개월 일정'}, headers={'Authorization': 'Bearer fake'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['command']['range']['label'], '앞으로 3개월')

    def test_rate_limit(self):
        info = {'aud': 'client', 'scope': 'https://www.googleapis.com/auth/calendar.readonly', 'expires_in': '300', 'sub': 'user'}
        with patch.dict(os.environ, {'ASSISTANT_GOOGLE_CLIENT_ID': 'client'}), patch.object(api.requests, 'get', return_value=Mock(ok=True, json=lambda: info)), self.client.application.test_request_context(headers={'Authorization': 'Bearer fake'}):
            for _ in range(30):
                api.authorize()
            with self.assertRaises(api.AssistantError) as error:
                api.authorize()
        self.assertEqual(error.exception.status, 429)

    def test_openai_error_does_not_expose_key_or_fall_back(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-secret'}), patch.object(api.requests, 'post', return_value=Mock(ok=False, status_code=401)):
            with self.assertRaises(api.AssistantError) as error:
                api.openai_response('test', {})
        self.assertNotIn('test-secret', str(error.exception))

    def test_incomplete_model_response_is_rejected(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-secret'}), patch.object(api.requests, 'post', return_value=Mock(ok=True, json=lambda: {'status': 'incomplete', 'output': []})):
            with self.assertRaises(api.AssistantError):
                api.openai_response('test', {})


if __name__ == '__main__':
    unittest.main()
