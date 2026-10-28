import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import capture_session
import lg_tv


class FakeTV:
    def __init__(self):
        self.calls = []
        self.fail_restore = False

    def begin(self, path):
        self.calls.append('begin')
        value = {'session_id': 'owned-session', 'created_at': '2026-10-28T09:00:00+01:00',
                 'host': '192.0.2.10', 'device': 'test-tv', 'status': 'active'}
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(value))
        return value

    def end(self, path):
        self.calls.append('end')
        value = json.loads(Path(path).read_text())
        value['status'] = 'needs_restore' if self.fail_restore else 'restored'
        Path(path).write_text(json.dumps(value))
        if self.fail_restore:
            raise TimeoutError('offline during restoration')
        return value

    def close(self):
        self.calls.append('close')


class SessionTests(unittest.TestCase):
    def plan(self, slug='app'):
        return {'schema_version': 1, 'app_slug': slug, 'app_id': 'test.' + slug,
                'steps': [{'launch': 'test.' + slug, 'wait': 0}, {'capture': 'home'}]}

    def summary(self, root):
        paths = list((Path(root) / 'session-runs').glob('*.json'))
        self.assertEqual(len(paths), 1)
        return json.loads(paths[0].read_text())

    def test_multiple_plans_use_one_owned_session_and_restore(self):
        with tempfile.TemporaryDirectory() as temp:
            tv = FakeTV(); seen = []
            def runner(client, plan, *args):
                seen.append(plan['app_slug'])
                return {'status': 'completed'}
            result = capture_session.execute_owned_session(tv, [self.plan('one'), self.plan('two')], temp,
                Path(temp) / 'session.json', '192.0.2.10', 'test-tv', runner=runner)
            self.assertEqual(seen, ['one', 'two'])
            self.assertEqual(tv.calls.count('begin'), 1)
            self.assertEqual(tv.calls.count('end'), 1)
            self.assertEqual(result['restore_status'], 'restored')
            self.assertEqual(result['status'], 'completed')

    def test_plan_failure_stops_remaining_plans_and_restores(self):
        with tempfile.TemporaryDirectory() as temp:
            tv = FakeTV(); seen = []
            def runner(client, plan, *args):
                seen.append(plan['app_slug'])
                raise TimeoutError('outcome uncertain')
            with self.assertRaises(TimeoutError):
                capture_session.execute_owned_session(tv, [self.plan('one'), self.plan('two')], temp,
                    Path(temp) / 'session.json', '192.0.2.10', 'test-tv', runner=runner)
            self.assertEqual(seen, ['one'])
            self.assertEqual(tv.calls.count('end'), 1)
            summary = self.summary(temp)
            self.assertEqual(summary['status'], 'failed')
            self.assertEqual(summary['restore_status'], 'restored')

    def test_preexisting_session_is_never_adopted_or_ended(self):
        with tempfile.TemporaryDirectory() as temp:
            tv = FakeTV(); path = Path(temp) / 'session.json'
            content = json.dumps({'session_id': 'other-owner', 'status': 'active'})
            path.write_text(content)
            with self.assertRaises(lg_tv.TVError):
                capture_session.execute_owned_session(tv, [self.plan()], temp, path, '192.0.2.10', 'test-tv')
            self.assertEqual(tv.calls, [])
            self.assertEqual(path.read_text(), content)

    def test_replaced_session_blocks_next_plan_and_cleanup(self):
        with tempfile.TemporaryDirectory() as temp:
            tv = FakeTV(); path = Path(temp) / 'session.json'; seen = []
            def runner(client, plan, output, receipt, *args):
                seen.append(plan['app_slug'])
                replacement = json.loads(Path(receipt).read_text())
                replacement['session_id'] = 'new-owner'
                Path(receipt).write_text(json.dumps(replacement))
                return {'status': 'completed'}
            with self.assertRaises(capture_session.SessionOwnershipError):
                capture_session.execute_owned_session(tv, [self.plan('one'), self.plan('two')], temp,
                    path, '192.0.2.10', 'test-tv', runner=runner)
            self.assertEqual(seen, ['one'])
            self.assertNotIn('end', tv.calls)
            self.assertEqual(json.loads(path.read_text())['session_id'], 'new-owner')
            self.assertEqual(self.summary(temp)['restore_status'], 'skipped_ownership_changed')

    def test_cleanup_failure_is_not_reported_as_success(self):
        with tempfile.TemporaryDirectory() as temp:
            tv = FakeTV(); tv.fail_restore = True
            with self.assertRaises(lg_tv.TVError):
                capture_session.execute_owned_session(tv, [self.plan()], temp, Path(temp) / 'session.json',
                    '192.0.2.10', 'test-tv', runner=lambda *args: {'status': 'completed'})
            summary = self.summary(temp)
            self.assertEqual(summary['status'], 'failed')
            self.assertEqual(summary['restore_status'], 'failed')
            self.assertEqual(summary['restore_error_type'], 'TimeoutError')

    def test_partial_begin_cleanup_is_not_replayed_by_wrapper(self):
        with tempfile.TemporaryDirectory() as temp:
            tv = FakeTV(); original_begin = tv.begin
            def begin(path):
                original_begin(path)
                tv.end(path)  # Emulate lg_tv.begin's own failure cleanup.
                raise TimeoutError('begin failed after its own cleanup')
            tv.begin = begin
            with self.assertRaises(TimeoutError):
                capture_session.execute_owned_session(tv, [self.plan()], temp, Path(temp) / 'session.json',
                    '192.0.2.10', 'test-tv', runner=lambda *args: {'status': 'completed'})
            self.assertEqual(tv.calls.count('end'), 1)
            self.assertEqual(self.summary(temp)['session_status_on_exit'], 'restored')

    def test_dry_run_needs_no_host_pairing_or_output_files(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(temp); plan = root / 'plan.json'; plan.write_text(json.dumps(self.plan()))
            output = root / 'evidence'; session = root / 'session.json'
            with patch.dict(os.environ, {'LGTV_HOST': ''}), patch('lg_tv.resolve_root') as resolve, patch('lg_tv.TVClient') as client:
                code = capture_session.main(['--plan', str(plan), '--session', str(session), '--output', str(output), '--dry-run'])
            self.assertEqual(code, 0)
            resolve.assert_not_called(); client.assert_not_called()
            self.assertFalse(output.exists()); self.assertFalse(session.exists())

    def test_all_plans_are_validated_before_any_tv_access(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); first = root / 'one.json'; second = root / 'two.json'
            first.write_text(json.dumps(self.plan())); second.write_text(json.dumps({'steps': [{'shell': 'no'}]}))
            with patch('lg_tv.resolve_root') as resolve, patch('lg_tv.TVClient') as client:
                with self.assertRaises(lg_tv.TVError):
                    capture_session.main(['--host', '192.0.2.10', '--plan', str(first), '--plan', str(second),
                                          '--session', str(root / 'session.json'), '--output', str(root / 'evidence')])
            resolve.assert_not_called(); client.assert_not_called()

    def test_host_is_required_before_runtime_pairing_access(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); plan = root / 'plan.json'; plan.write_text(json.dumps(self.plan()))
            with patch.dict(os.environ, {'LGTV_HOST': ''}), patch('lg_tv.resolve_root') as resolve, patch('lg_tv.TVClient') as client:
                with self.assertRaises(lg_tv.TVError):
                    capture_session.main(['--plan', str(plan), '--session', str(root / 'session.json'), '--output', str(root / 'evidence')])
            resolve.assert_not_called(); client.assert_not_called()

    def test_host_can_come_from_environment(self):
        with patch.dict(os.environ, {'LGTV_HOST': '192.0.2.10'}):
            self.assertEqual(lg_tv.configured_host(), '192.0.2.10')
            self.assertEqual(lg_tv.configured_host('192.0.2.20'), '192.0.2.20')

    def test_oversized_plan_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'large.json'
            path.write_bytes(b' ' * (capture_session.run_plan.MAX_PLAN_BYTES + 2))
            with self.assertRaises(lg_tv.TVError):
                capture_session.read_plans([path])

    def test_review_reclassification_is_local_and_preserves_raw_manifest(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(temp); manifest = root / 'manifest.jsonl'
            raw = '{"capture_id":"one","view":"home"}\n'; manifest.write_text(raw)
            with patch.dict(os.environ, {'LGTV_HOST': ''}), patch('lg_tv.TVClient') as client:
                code = lg_tv.main(['--output', temp, 'review', '--capture-id', 'one', '--status', 'verified',
                                   '--verified-view', 'profiles', '--note', 'Profile selector observed.'])
            self.assertEqual(code, 0); client.assert_not_called()
            self.assertEqual(json.loads((root / 'reviews.jsonl').read_text())['verified_view'], 'profiles')
            self.assertEqual(manifest.read_text(), raw)

    def test_review_override_requires_verified_status(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(lg_tv.TVError):
                lg_tv.main(['--output', temp, 'review', '--capture-id', 'one', '--status', 'blocked',
                            '--verified-view', 'profiles'])
            self.assertFalse((Path(temp) / 'reviews.jsonl').exists())


if __name__ == '__main__':
    unittest.main()
