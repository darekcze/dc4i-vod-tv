import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lg_tv
import run_plan


class FakeTV:
    def __init__(self, foreground='com.example.tv', power='Active', enable_works=True):
        self.state = {'power': {'state': power}, 'foreground': {'appId': foreground}}
        self.enable_works = enable_works
        self.sent_keys = []
        self.captures = []
        self.requests = []
        self.closed = False

    def status(self):
        return copy.deepcopy(self.state)

    def request(self, uri, payload):
        self.requests.append((uri, payload))
        if self.enable_works:
            self.state['power']['state'] = 'Active'
        return {'returnValue': True}

    def launch(self, app, settle):
        self.state['foreground']['appId'] = app
        return {'foreground_matches': True, 'foreground_app': app}

    def keys(self, keys, interval):
        self.sent_keys.append(keys)
        return {'keys_sent': keys}

    def capture(self, output, slug, view, note, expected_app_id):
        self.captures.append((slug, view, expected_app_id))
        return {'capture_id': 'fake-capture', 'app_id': expected_app_id, 'view': view}

    def close(self):
        self.closed = True


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name)
        self.session = self.output / 'session.json'
        self.receipt = {'status': 'active', 'session_id': 'session-a', 'created_at': '2026-10-28T08:00:00+01:00',
                        'host': '192.0.2.10', 'device': 'LG_OLED55G42LW'}
        self.session.write_text(json.dumps(self.receipt))
        self.patch = patch.object(lg_tv, 'emit')
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def plan(self, steps):
        return {'app_slug': 'example', 'app_id': 'com.example.tv', 'steps': steps}

    def execute(self, client, steps, sleeper=lambda _: None):
        return run_plan.execute_plan(client, self.plan(steps), self.output, self.session,
                                     '192.0.2.10', 'LG_OLED55G42LW', sleeper=sleeper)

    def results(self):
        return [json.loads(p.read_text()) for p in (self.output / 'runs').glob('*.result.json')]

    def test_rejects_ambiguous_or_unapproved_actions(self):
        for step in [{'keys': ['ENTER'], 'capture': 'home'}, {'shell': 'echo unsafe'},
                     {'keys': ['PLAY']}, {'keys': ['LEFT'], 'unexpected': True}]:
            with self.subTest(step=step), self.assertRaises(lg_tv.TVError):
                run_plan.validate_plan(self.plan([step]))

    def test_rejects_different_launch_target(self):
        with self.assertRaises(lg_tv.TVError):
            run_plan.validate_plan(self.plan([{'launch': 'com.other.app'}]))

    def test_rejects_nonfinite_and_boolean_waits(self):
        for value in [float('nan'), float('inf'), True, -1, 31, '1']:
            with self.subTest(value=value), self.assertRaises(lg_tv.TVError):
                run_plan.validate_plan(self.plan([{'wait': value}]))

    def test_inactive_session_prevents_all_device_reads(self):
        self.receipt['status'] = 'restored'
        self.session.write_text(json.dumps(self.receipt))
        client = FakeTV()
        with patch.object(client, 'status') as status, self.assertRaises(lg_tv.TVError):
            self.execute(client, [{'keys': ['LEFT']}])
        status.assert_not_called()
        self.assertFalse(client.sent_keys)

    def test_wrong_tv_session_is_rejected(self):
        self.receipt['host'] = '192.0.2.99'
        self.session.write_text(json.dumps(self.receipt))
        with self.assertRaises(lg_tv.TVError):
            self.execute(FakeTV(), [{'wait': 0}])

    def test_foreground_check_blocks_keys_and_records_failure(self):
        client = FakeTV(foreground='com.other.app')
        with self.assertRaises(lg_tv.TVError):
            self.execute(client, [{'keys': ['ENTER']}])
        self.assertFalse(client.sent_keys)
        self.assertTrue(client.closed)
        self.assertEqual(self.results()[0]['status'], 'failed')
        self.assertEqual(self.results()[0]['completed_steps'], 0)
        actions = [json.loads(s) for s in (self.output / 'actions.jsonl').read_text().splitlines()]
        self.assertEqual(actions[-1]['phase'], 'failed')

    def test_success_keeps_session_owned_by_caller(self):
        before = self.session.read_bytes()
        client = FakeTV()
        result = self.execute(client, [{'launch': 'com.example.tv', 'wait': 0},
                                       {'keys': ['LEFT'], 'wait': 0},
                                       {'capture': 'search', 'note': 'Observed search panel'}])
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['completed_steps'], 3)
        self.assertEqual(client.captures, [('example', 'search', 'com.example.tv')])
        self.assertEqual(before, self.session.read_bytes())
        self.assertTrue(client.closed)

    def test_replaced_session_stops_later_steps(self):
        client = FakeTV()

        def replace_session(_):
            updated = dict(self.receipt, session_id='session-b')
            self.session.write_text(json.dumps(updated))

        with self.assertRaises(lg_tv.TVError):
            self.execute(client, [{'wait': 0}, {'keys': ['ENTER']}], sleeper=replace_session)
        self.assertFalse(client.sent_keys)
        self.assertEqual(self.results()[0]['completed_steps'], 1)
        self.assertEqual(json.loads(self.session.read_text())['session_id'], 'session-b')

    def test_home_cannot_send_following_enter_into_other_app(self):
        client = FakeTV()
        original_keys = client.keys

        def leave_app(keys, interval):
            result = original_keys(keys, interval)
            if 'HOME' in keys:
                client.state['foreground']['appId'] = 'com.webos.app.home'
            return result

        client.keys = leave_app
        with self.assertRaises(lg_tv.TVError):
            self.execute(client, [{'keys': ['HOME', 'ENTER'], 'wait': 0}])
        self.assertEqual(client.sent_keys, [['HOME']])

    def test_enter_boundary_rechecks_foreground_before_following_keys(self):
        client = FakeTV()
        original_keys = client.keys

        def external_selection(keys, interval):
            result = original_keys(keys, interval)
            if 'ENTER' in keys:
                client.state['foreground']['appId'] = 'com.other.app'
            return result

        client.keys = external_selection
        with self.assertRaises(lg_tv.TVError):
            self.execute(client, [{'keys': ['LEFT', 'ENTER', 'DOWN'], 'wait': 0}])
        self.assertEqual(client.sent_keys, [['LEFT', 'ENTER']])

    def test_screen_saver_enable_is_verified_before_input(self):
        client = FakeTV(power='Screen Saver', enable_works=False)
        with self.assertRaises(lg_tv.TVError):
            self.execute(client, [{'keys': ['ENTER']}])
        self.assertEqual(len(client.requests), 1)
        self.assertFalse(client.sent_keys)
        self.assertEqual(self.results()[0]['failed_step'], None)

    def test_cli_requires_one_plan_source_and_session(self):
        with self.assertRaises(SystemExit):
            run_plan.parser().parse_args(['--output', '/tmp/example', '--plan-json', '{}'])
        with self.assertRaises(SystemExit):
            run_plan.parser().parse_args(['--output', '/tmp/example', '--session', '/tmp/session.json',
                                         '--plan', 'plan.json', '--plan-json', '{}'])


if __name__ == '__main__':
    unittest.main()
