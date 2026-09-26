import os
import unittest
from copy import deepcopy
from datetime import datetime
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo
import assistant_api as api
import assistant_graph as graph
from webapp import app


class GraphTests(unittest.TestCase):
    def setUp(self):
        self.data = {'question': '확인', 'approved': True, 'operationId': '12345678-1234-1234-1234-123456789abc', 'create': {'title': '팀 회의', 'start': '2027-09-27T10:00:00+09:00', 'end': '2027-09-27T11:00:00+09:00', 'attendees': ['team@example.com']}}
        self.plan = graph.validate_execution({'data': self.data, 'identity': 'user'})['plan']
        self.event = {**deepcopy(self.plan), 'status': 'confirmed', 'htmlLink': 'https://calendar.google.com/event'}

    def invoke(self):
        return graph.run_assistant('execute', self.data, 'fake-token', 'user')

    def test_graph_creates_with_attendees_and_notifications(self):
        with patch.object(graph.requests, 'get', return_value=Mock(status_code=404)), patch.object(graph.requests, 'post', return_value=Mock(ok=True, status_code=200, json=lambda: self.event)) as post:
            output = self.invoke()
        self.assertEqual(output['sharedWith'], ['team@example.com'])
        self.assertEqual(output['workflow'], 'langgraph')
        self.assertEqual(post.call_args.kwargs['params'], {'sendUpdates': 'all'})
        self.assertEqual(post.call_args.kwargs['json']['attendees'], [{'email': 'team@example.com'}])
        self.assertNotIn('fake-token', str(output))

    def test_retry_recovers_without_second_create(self):
        with patch.object(graph.requests, 'get', return_value=Mock(status_code=200, json=lambda: self.event)), patch.object(graph.requests, 'post') as post:
            output = self.invoke()
        post.assert_not_called()
        self.assertEqual(output['event']['id'], self.plan['id'])

    def test_unapproved_blocks_all_google_calls(self):
        self.data['approved'] = False
        with patch.object(graph.requests, 'get') as get, patch.object(graph.requests, 'post') as post, self.assertRaises(api.AssistantError):
            self.invoke()
        get.assert_not_called()
        post.assert_not_called()

    def test_timeout_never_reports_success_and_keeps_retry_id(self):
        with patch.object(graph.requests, 'get', return_value=Mock(status_code=404)), patch.object(graph.requests, 'post', side_effect=graph.requests.Timeout), self.assertRaises(api.AssistantError) as error:
            self.invoke()
        self.assertIn('중복', str(error.exception))
        self.assertEqual(graph.validate_execution({'data': self.data, 'identity': 'user'})['plan']['id'], self.plan['id'])

    def test_conflicting_retry_payload_is_rejected(self):
        self.event['summary'] = '다른 회의'
        with patch.object(graph.requests, 'get', return_value=Mock(status_code=200, json=lambda: self.event)), patch.object(graph.requests, 'post') as post, self.assertRaises(api.AssistantError):
            self.invoke()
        post.assert_not_called()

    def test_concurrent_conflict_recovers_existing_event(self):
        with patch.object(graph.requests, 'get', side_effect=[Mock(status_code=404), Mock(status_code=200, ok=True, json=lambda: self.event)]), patch.object(graph.requests, 'post', return_value=Mock(status_code=409)):
            self.assertEqual(self.invoke()['event']['id'], self.plan['id'])

    def test_email_injection_is_rejected(self):
        self.data['create']['attendees'] = ['team@example.com\r\nBcc: attacker@example.com']
        with patch.object(graph.requests, 'post') as post, self.assertRaises(api.AssistantError):
            self.invoke()
        post.assert_not_called()

    def test_event_id_is_scoped_to_user(self):
        other = graph.validate_execution({'data': self.data, 'identity': 'other'})['plan']
        self.assertNotEqual(other['id'], self.plan['id'])

    def test_readonly_token_cannot_execute(self):
        info = {'aud': 'client', 'scope': 'https://www.googleapis.com/auth/calendar.readonly', 'expires_in': '300', 'sub': 'user'}
        with patch.dict(os.environ, {'ASSISTANT_GOOGLE_CLIENT_ID': 'client'}), patch.object(api.requests, 'get', return_value=Mock(ok=True, json=lambda: info)), patch.object(graph.requests, 'post') as post:
            response = app.test_client().post('/api/assistant/execute', json=self.data, headers={'Authorization': 'Bearer fake'})
        self.assertEqual(response.status_code, 401)
        post.assert_not_called()

    def test_execute_endpoint_with_write_token_runs_graph(self):
        info = {'aud': 'client', 'scope': 'https://www.googleapis.com/auth/calendar.events', 'expires_in': '300', 'sub': 'user'}
        def fake_get(url, **kwargs):
            if url.endswith('/tokeninfo'):
                return Mock(ok=True, json=lambda: info)
            return Mock(status_code=404)
        def fake_post(url, **kwargs):
            return Mock(ok=True, status_code=200, json=lambda: {**kwargs['json'], 'status': 'confirmed'})
        with patch.dict(os.environ, {'ASSISTANT_GOOGLE_CLIENT_ID': 'client'}), patch.object(graph.requests, 'get', side_effect=fake_get), patch.object(graph.requests, 'post', side_effect=fake_post):
            response = app.test_client().post('/api/assistant/execute', json=self.data, headers={'Authorization': 'Bearer fake'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['workflow'], 'langgraph')
        self.assertEqual(response.json['sharedWith'], ['team@example.com'])

    def test_creation_without_team_disables_notifications(self):
        self.data['create']['attendees'] = []
        self.event['attendees'] = []
        with patch.object(graph.requests, 'get', return_value=Mock(status_code=404)), patch.object(graph.requests, 'post', return_value=Mock(ok=True, status_code=200, json=lambda: self.event)) as post:
            output = self.invoke()
        self.assertEqual(post.call_args.kwargs['params'], {'sendUpdates': 'none'})
        self.assertEqual(output['sharedWith'], [])

    def test_plan_uses_known_team_never_model_invented_recipients(self):
        model = {'action': 'calendar_create', 'shareWithTeam': True, 'clarification': None, 'title': '회의', 'start': self.data['create']['start'], 'end': self.data['create']['end']}
        now = datetime(2026, 9, 26, tzinfo=ZoneInfo('Asia/Seoul'))
        with patch.object(api, 'openai_response', return_value=model):
            command = api.interpret_command('내일 오전 10시 회의 만들고 팀에 공유해줘', now=now, context={'teamMembers': ['team@example.com']})
        self.assertEqual(command['create']['attendees'], ['team@example.com'])

    def test_missing_team_returns_resumable_request(self):
        model = {'action': 'calendar_create', 'shareWithTeam': True, 'clarification': None, 'title': '회의', 'start': self.data['create']['start'], 'end': self.data['create']['end']}
        with patch.object(api, 'openai_response', return_value=model):
            command = api.interpret_command('오전 10시 회의 만들고 팀에 공유해줘')
        self.assertEqual(command['action'], 'unknown')
        self.assertIn('이메일', command['clarification'])
        self.assertIn('공유', command['pendingRequest'])

    def test_model_cannot_invent_morning_start_time(self):
        model = {'action': 'calendar_create', 'shareWithTeam': True, 'clarification': None, 'title': '회의', 'start': self.data['create']['start'], 'end': self.data['create']['end']}
        with patch.object(api, 'openai_response', return_value=model):
            command = api.interpret_command('내일 오전 회의 일정 정리하고 팀에 공유해줘', context={'teamMembers': ['team@example.com']})
        self.assertEqual(command['action'], 'unknown')
        self.assertIn('몇 시', command['clarification'])

    def test_complete_followup_proceeds_to_app_confirmation(self):
        model = {'action': 'unknown', 'shareWithTeam': True, 'clarification': '초대 여부를 확인해 주세요.', 'title': '회의', 'start': self.data['create']['start'], 'end': self.data['create']['end']}
        with patch.object(api, 'openai_response', return_value=model):
            command = api.interpret_command('오전 10시부터 11시까지', context={'pendingRequest': '내일 회의 만들고 팀에 공유해줘', 'teamMembers': ['team@example.com']})
        self.assertEqual(command['action'], 'calendar_create')
        self.assertEqual(command['create']['attendees'], ['team@example.com'])

    def test_interpret_endpoint_invokes_langgraph(self):
        with patch.object(api, 'authorize'), patch.object(api, 'interpret_command', return_value={'action': 'unknown'}):
            response = app.test_client().post('/api/assistant/interpret', json={'question': '검증'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['workflow'], 'langgraph')
