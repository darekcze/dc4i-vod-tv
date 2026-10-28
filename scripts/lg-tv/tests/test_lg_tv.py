import contextlib
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, Mock, call, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import lg_tv
import build_atlas


class FakeTV:
    def __init__(self):
        self.events = []

    def launch(self, app_id, settle=2):
        self.events.append(('launch', app_id))
        return {'foreground_matches': True}

    def keys(self, keys, interval=0.35):
        self.events.append(('keys', keys))
        return {'keys_sent': keys}

    def capture(self, output, app_slug, view, note='', expected_app_id=None):
        self.events.append(('capture', view))
        path = Path(output) / (view + '.jpg')
        path.write_bytes(b'captured-evidence')
        return {'capture_id': 'id-' + view, 'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


class CaptureTests(unittest.TestCase):
    def connection_client(self, ws_type, query):
        client = lg_tv.TVClient.__new__(lg_tv.TVClient)
        client.host = '192.0.2.10'; client.device = 'test'; client.timeout = 1
        client.ws = None; client.hello = {'type': 'register'}
        client.helper = {'WS': ws_type, 'query': query}
        return client

    def test_connect_retries_handshake_and_closes_partial_sockets(self):
        resources = []
        class Socket:
            closed = False
            def close(self):
                self.closed = True
        class WS:
            def __init__(self, **kwargs):
                self.raw = Socket(); resources.append(self.raw)
                if len(resources) < 3:
                    raise TimeoutError('TLS handshake timed out')
                self.sock = self.raw
            def close(self):
                self.sock.close()
        client = self.connection_client(WS, lambda ws, request: {'type': 'registered'})
        with patch('lg_tv.time.sleep') as sleep:
            client.connect()
            self.assertEqual([call.args[0] for call in sleep.call_args_list], [0.7, 0.9])
            client.connect()
        self.assertEqual(len(resources), 3)
        self.assertTrue(resources[0].closed)
        self.assertTrue(resources[1].closed)
        self.assertFalse(resources[2].closed)
        client.close()

    def test_connect_retries_registration_transport_failure(self):
        transports = []
        class WS:
            def __init__(self, **kwargs):
                self.closed = False; transports.append(self)
            def close(self):
                self.closed = True
        def query(ws, request):
            if len(transports) == 1:
                raise TimeoutError('registration timeout')
            return {'type': 'registered'}
        client = self.connection_client(WS, query)
        with patch('lg_tv.time.sleep'):
            client.connect()
        self.assertEqual(len(transports), 2)
        self.assertTrue(transports[0].closed)
        self.assertFalse(transports[1].closed)
        client.close()

    def test_connect_stops_after_three_transport_failures(self):
        resources = []
        class WS:
            def __init__(self, **kwargs):
                self.closed = False; resources.append(self)
                raise TimeoutError('TLS timeout')
            def close(self):
                self.closed = True
        client = self.connection_client(WS, lambda ws, request: {'type': 'registered'})
        with patch('lg_tv.time.sleep') as sleep:
            with self.assertRaises(TimeoutError):
                client.connect()
        self.assertEqual(len(resources), 3)
        self.assertEqual(sleep.call_count, 2)
        self.assertTrue(all(resource.closed for resource in resources))
        self.assertIsNone(client.ws)

    def test_connect_does_not_retry_explicit_pairing_rejection(self):
        transports = []
        class WS:
            def __init__(self, **kwargs):
                self.closed = False; transports.append(self)
            def close(self):
                self.closed = True
        client = self.connection_client(WS, lambda ws, request: {'type': 'error'})
        with patch('lg_tv.time.sleep') as sleep:
            with self.assertRaises(lg_tv.TVError):
                client.connect()
            sleep.assert_not_called()
        self.assertEqual(len(transports), 1)
        self.assertTrue(transports[0].closed)

    def test_request_failure_discards_socket_without_replaying_mutation(self):
        transports, commands = [], []
        class WS:
            def __init__(self, **kwargs):
                self.closed = False; transports.append(self)
            def close(self):
                self.closed = True
        def query(ws, request):
            if request.get('type') == 'register':
                return {'type': 'registered'}
            commands.append(request['uri'])
            if request['uri'].endswith('/launch'):
                raise TimeoutError('Mutation may have reached the TV')
            return {'type': 'response', 'payload': {'returnValue': True, 'state': 'Active'}}
        client = self.connection_client(WS, query)
        with self.assertRaises(TimeoutError):
            client.request('ssap://system.launcher/launch', {'id': 'example'})
        self.assertIsNone(client.ws)
        self.assertTrue(transports[0].closed)
        result = client.request('ssap://com.webos.service.tvpower/power/getPowerState')
        self.assertEqual(result['state'], 'Active')
        self.assertEqual(commands.count('ssap://system.launcher/launch'), 1)
        self.assertEqual(len(commands), 2)
        self.assertEqual(len(transports), 2)
        client.close()

    def test_cli_global_options_and_capture_contract(self):
        args = lg_tv.parser().parse_args(['--root', '/device/root', '--output', '/output', 'capture', '--app-slug', 'disneyplus', '--view', 'home', '--expected-app-id', 'app.disney'])
        self.assertEqual(args.root, '/device/root')
        self.assertEqual(args.view, 'home')
        self.assertEqual(args.expected_app_id, 'app.disney')

    def test_slug_cannot_escape_output(self):
        for slug in ('../private', 'name/child', '', 'My TV', 'a\\b'):
            with self.assertRaises(lg_tv.TVError):
                lg_tv.safe_slug(slug)

    def test_secret_fields_redacted_recursively(self):
        value = {'client-key': 'private', 'nested': [{'passphrase': 'private2', 'accessToken': 'private3'}], 'keys_sent': ['LEFT'], 'app_id': 'disney'}
        serialized = json.dumps(lg_tv.redact(value))
        self.assertNotIn('private', serialized)
        self.assertIn('LEFT', serialized)
        self.assertIn('disney', serialized)

    def test_url_rejects_external_host_credentials_and_schemes(self):
        for url in ('https://evil.example/image.jpg', 'https://192.0.2.10.evil.example/image',
                    'file:///private/key', 'http://user:password@192.0.2.10/image',
                    'http://192.0.2.10@evil.example/image'):
            with self.assertRaises(lg_tv.TVError):
                lg_tv.validate_url(url, '192.0.2.10')
        self.assertEqual(lg_tv.validate_url('http://192.0.2.10:3000/image', '192.0.2.10').port, 3000)

    def test_redirect_rejects_external_host(self):
        with self.assertRaises(lg_tv.TVError):
            lg_tv.SameTVRedirect('192.0.2.10').redirect_request(None, None, 302, '', {}, 'https://evil.example/capture')

    def test_image_dimensions_png_and_jpeg(self):
        png = b'\x89PNG\r\n\x1a\n' + b'\x00\x00\x00\rIHDR' + struct.pack('>II', 1920, 1080)
        self.assertEqual(lg_tv.image_info(png), ('.png', 1920, 1080))
        jpg = b'\xff\xd8\xff\xc0' + struct.pack('>H', 11) + b'\x08' + struct.pack('>HH', 540, 960) + b'\x01\x01\x11\x00' + b'\xff\xd9'
        self.assertEqual(lg_tv.image_info(jpg), ('.jpg', 960, 540))
        with self.assertRaises(lg_tv.TVError):
            lg_tv.image_info(b'<html>not an image</html>')

    def test_capture_requires_explicit_success_before_download(self):
        client = lg_tv.TVClient.__new__(lg_tv.TVClient)
        client.host = '192.0.2.10'
        client.status = lambda: {'power': {'state': 'Active'}, 'foreground': {'appId': 'test.app'}}
        for value in ({'imageUri': 'http://192.0.2.10/capture.jpg'},
                      {'returnValue': False, 'imageUri': 'http://192.0.2.10/capture.jpg'},
                      {'returnValue': 1, 'imageUri': 'http://192.0.2.10/capture.jpg'}):
            client.request = lambda uri, body=value: body
            with tempfile.TemporaryDirectory() as temp, patch('lg_tv.urllib.request.build_opener') as opener:
                with self.assertRaises(lg_tv.TVError):
                    client.capture(temp, 'testapp', 'home')
                opener.assert_not_called()
                self.assertFalse((Path(temp) / 'manifest.jsonl').exists())

    def test_successful_capture_receipt_records_tv_success(self):
        client = lg_tv.TVClient.__new__(lg_tv.TVClient)
        client.host = '192.0.2.10'
        client.status = lambda: {'power': {'state': 'Active'}, 'foreground': {'appId': 'test.app'}}
        client.request = lambda uri: {'returnValue': True, 'imageUri': 'http://192.0.2.10/capture.jpg'}
        data = b'\xff\xd8\xff\xc0' + struct.pack('>H', 11) + b'\x08' + struct.pack('>HH', 540, 960) + b'\x01\x01\x11\x00' + b'\xff\xd9'
        with tempfile.TemporaryDirectory() as temp, patch('lg_tv.urllib.request.build_opener') as opener:
            response = opener.return_value.open.return_value.__enter__.return_value
            response.geturl.return_value = 'http://192.0.2.10/capture.jpg'
            response.read.return_value = data
            receipt = client.capture(temp, 'testapp', 'home')
            self.assertIs(receipt['capture_return_value'], True)
            self.assertEqual(receipt['download_attempts'], 1)
            saved = json.loads((Path(temp) / 'manifest.jsonl').read_text())
            self.assertIs(saved['capture_return_value'], True)
            self.assertEqual(saved['download_attempts'], 1)

    def download_client(self):
        client = lg_tv.TVClient.__new__(lg_tv.TVClient)
        client.host = '192.0.2.10'
        client.status = Mock(return_value={'power': {'state': 'Active'}, 'foreground': {'appId': 'test.app'}})
        client.request = Mock(return_value={'returnValue': True, 'imageUri': 'http://192.0.2.10/capture.jpg'})
        return client

    def download_response(self, final_url='http://192.0.2.10/capture.jpg'):
        response = MagicMock()
        response.__enter__.return_value = response
        response.geturl.return_value = final_url
        response.read.return_value = b'\x89PNG\r\n\x1a\n' + b'\x00\x00\x00\rIHDR' + struct.pack('>II', 960, 540)
        return response

    def test_capture_retries_same_uri_after_timeout_with_one_shot_and_same_host_redirect(self):
        client = self.download_client()
        uri = client.request.return_value['imageUri']
        response = self.download_response('https://192.0.2.10:3001/redirected/capture.png')
        with tempfile.TemporaryDirectory() as temp, patch('lg_tv.urllib.request.build_opener') as build, patch('lg_tv.time.sleep') as sleep:
            opener = build.return_value
            opener.open.side_effect = [lg_tv.urllib.error.URLError(TimeoutError('timed out')), response]
            receipt = client.capture(temp, 'testapp', 'home')
            self.assertEqual(opener.open.call_args_list, [call(uri, timeout=12), call(uri, timeout=12)])
            client.request.assert_called_once_with('ssap://tv/executeOneShot')
            sleep.assert_called_once_with(0.6)
            self.assertEqual(receipt['download_attempts'], 2)
            saved = json.loads((Path(temp) / 'manifest.jsonl').read_text())
            self.assertEqual(saved['download_attempts'], 2)
            redirect = next(handler for handler in build.call_args.args if isinstance(handler, lg_tv.SameTVRedirect))
            redirected = redirect.redirect_request(lg_tv.urllib.request.Request(uri), None, 302, '', {}, response.geturl())
            self.assertEqual(redirected.full_url, response.geturl())

    def test_capture_retries_reset_during_read_and_closes_response(self):
        client = self.download_client()
        first, second = self.download_response(), self.download_response()
        first.read.side_effect = ConnectionResetError('connection reset')
        with tempfile.TemporaryDirectory() as temp, patch('lg_tv.urllib.request.build_opener') as build, patch('lg_tv.time.sleep'):
            build.return_value.open.side_effect = [first, second]
            receipt = client.capture(temp, 'testapp', 'home')
            self.assertEqual(receipt['download_attempts'], 2)
            first.__exit__.assert_called_once()
            second.__exit__.assert_called_once()
            client.request.assert_called_once_with('ssap://tv/executeOneShot')

    def test_capture_stops_after_two_transfer_failures_without_new_one_shot(self):
        client = self.download_client()
        with tempfile.TemporaryDirectory() as temp, patch('lg_tv.urllib.request.build_opener') as build, patch('lg_tv.time.sleep') as sleep:
            build.return_value.open.side_effect = lg_tv.urllib.error.URLError(TimeoutError('timed out'))
            with self.assertRaises(lg_tv.urllib.error.URLError):
                client.capture(temp, 'testapp', 'home')
            self.assertEqual(build.return_value.open.call_count, 2)
            sleep.assert_called_once_with(0.6)
            client.request.assert_called_once_with('ssap://tv/executeOneShot')
            self.assertFalse((Path(temp) / 'manifest.jsonl').exists())

    def test_capture_does_not_retry_http_errors_or_unrelated_transport_errors(self):
        uri = 'http://192.0.2.10/capture.jpg'
        errors = [lg_tv.urllib.error.HTTPError(uri, code, 'HTTP error', {}, None) for code in (400, 401, 403, 500)]
        errors.append(lg_tv.urllib.error.URLError(ConnectionRefusedError('refused')))
        for error in errors:
            with self.subTest(error=error), tempfile.TemporaryDirectory() as temp, patch('lg_tv.urllib.request.build_opener') as build, patch('lg_tv.time.sleep') as sleep:
                client = self.download_client()
                build.return_value.open.side_effect = error
                with self.assertRaises(type(error)):
                    client.capture(temp, 'testapp', 'home')
                self.assertEqual(build.return_value.open.call_count, 1)
                sleep.assert_not_called()
                client.request.assert_called_once_with('ssap://tv/executeOneShot')
                self.assertFalse((Path(temp) / 'manifest.jsonl').exists())

    def test_capture_retry_rejects_foreign_final_url_before_reading(self):
        client = self.download_client()
        response = self.download_response('https://external.example/capture.jpg')
        with tempfile.TemporaryDirectory() as temp, patch('lg_tv.urllib.request.build_opener') as build, patch('lg_tv.time.sleep'):
            build.return_value.open.side_effect = [lg_tv.urllib.error.URLError(TimeoutError('timed out')), response]
            with self.assertRaises(lg_tv.TVError):
                client.capture(temp, 'testapp', 'home')
            response.read.assert_not_called()
            self.assertEqual(build.return_value.open.call_count, 2)
            client.request.assert_called_once_with('ssap://tv/executeOneShot')
            self.assertFalse((Path(temp) / 'manifest.jsonl').exists())

    def recipe(self):
        return {'schema_version': 1, 'reviewed': True, 'app_slug': 'testapp', 'app_id': 'test.app', 'steps': [
            {'action': 'launch', 'wait': 0}, {'action': 'key', 'keys': ['LEFT']},
            {'action': 'capture', 'view': 'home'}]}

    def test_recipe_requires_explicit_review_and_known_operations(self):
        value = self.recipe(); value['reviewed'] = False
        with self.assertRaises(lg_tv.TVError):
            lg_tv.validate_recipe(value)
        for step in ({'action': 'shell', 'command': 'bad'}, {'action': 'key', 'keys': ['POWER']},
                     {'action': 'wait', 'seconds': 900}, {'action': 'launch', 'app_id': 'other'}):
            value = self.recipe(); value['steps'].append(step)
            with self.assertRaises(lg_tv.TVError):
                lg_tv.validate_recipe(value)

    def test_resume_replays_navigation_and_skips_intact_capture(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            first = FakeTV(); lg_tv.run_flow(first, self.recipe(), temp)
            resumed = FakeTV(); result = lg_tv.run_flow(resumed, self.recipe(), temp, resume=True)
            self.assertEqual(resumed.events, [('launch', 'test.app'), ('keys', ['LEFT'])])
            self.assertEqual(result['capture_count'], 1)

    def test_resume_rejects_modified_capture(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            lg_tv.run_flow(FakeTV(), self.recipe(), temp)
            (Path(temp) / 'home.jpg').write_bytes(b'changed')
            with self.assertRaises(lg_tv.TVError):
                lg_tv.run_flow(FakeTV(), self.recipe(), temp, resume=True)

    def test_failed_app_restore_still_restores_screen_off(self):
        client = lg_tv.TVClient.__new__(lg_tv.TVClient)
        client.host = '192.0.2.10'; client.device = 'test'
        statuses = iter([
            {'foreground': {'appId': 'other'}, 'power': {'state': 'Active'}},
            {'foreground': {'appId': 'other'}, 'power': {'state': 'Screen Off'}}])
        client.status = lambda: next(statuses)
        def bad_launch(*args):
            raise lg_tv.TVError('launch failed')
        client.launch = bad_launch
        calls = []
        client.request = lambda uri, payload=None: calls.append(uri) or {'returnValue': True}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'session.json'
            path.write_text(json.dumps({'host': client.host, 'device': 'test', 'status': 'active',
                                        'restore_app': 'original', 'restore_screen_off': True}))
            with self.assertRaises(lg_tv.TVError):
                client.end(path)
            self.assertIn('ssap://com.webos.service.tvpower/power/turnOffScreen', calls)
            self.assertEqual(json.loads(path.read_text())['status'], 'needs_restore')

    def test_begin_records_screen_saver_before_enabling(self):
        client = lg_tv.TVClient.__new__(lg_tv.TVClient)
        client.host = '192.0.2.10'; client.device = 'test'
        statuses = iter([
            {'foreground': {'appId': 'disney'}, 'power': {'state': 'Screen Saver'}},
            {'foreground': {'appId': 'disney'}, 'power': {'state': 'Active'}}])
        client.status = lambda: next(statuses)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'session.json'
            def screen_on(uri, payload=None):
                receipt = json.loads(path.read_text())
                self.assertEqual(receipt['status'], 'needs_restore')
                self.assertTrue(receipt['restore_screen_off'])
                return {'returnValue': True}
            client.request = screen_on
            original_sleep = lg_tv.time.sleep
            try:
                lg_tv.time.sleep = lambda value: None
                result = client.begin(path)
            finally:
                lg_tv.time.sleep = original_sleep
            self.assertEqual(result['status'], 'active')

    def test_partial_begin_failure_attempts_restoration(self):
        client = lg_tv.TVClient.__new__(lg_tv.TVClient)
        client.host = '192.0.2.10'; client.device = 'test'; client.ws = None
        statuses = iter([
            {'foreground': {'appId': 'disney'}, 'power': {'state': 'Screen Off'}},
            {'foreground': {'appId': 'disney'}, 'power': {'state': 'Active'}},
            {'foreground': {'appId': 'disney'}, 'power': {'state': 'Screen Off'}}])
        client.status = lambda: next(statuses)
        calls = []
        def request(uri, payload=None):
            calls.append(uri)
            if uri.endswith('turnOnScreen'):
                raise ConnectionError('Response lost after screen-on')
            return {'returnValue': True}
        client.request = request
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'session.json'
            with self.assertRaises(ConnectionError):
                client.begin(path)
            receipt = json.loads(path.read_text())
            self.assertEqual(receipt['status'], 'restored')
            self.assertEqual(receipt['begin_error_type'], 'ConnectionError')
            self.assertIn('ssap://com.webos.service.tvpower/power/turnOffScreen', calls)

    def test_unreachable_after_partial_begin_keeps_restore_receipt(self):
        client = lg_tv.TVClient.__new__(lg_tv.TVClient)
        client.host = '192.0.2.10'; client.device = 'test'; client.ws = None
        calls = [0]
        def status():
            calls[0] += 1
            if calls[0] == 1:
                return {'foreground': {'appId': 'disney'}, 'power': {'state': 'Screen Off'}}
            raise TimeoutError('offline')
        def request(uri, payload=None):
            raise TimeoutError('offline')
        client.status = status; client.request = request
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'session.json'
            with self.assertRaises(TimeoutError):
                client.begin(path)
            receipt = json.loads(path.read_text())
            self.assertEqual(receipt['status'], 'needs_restore')
            self.assertTrue(receipt['restore_screen_off'])
            self.assertEqual(receipt['restore_app'], 'disney')
            self.assertEqual(receipt['begin_error_type'], 'TimeoutError')

    def test_begin_does_not_touch_preexisting_active_session(self):
        client = lg_tv.TVClient.__new__(lg_tv.TVClient)
        client.host = '192.0.2.10'; client.device = 'test'; client.ws = None
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'session.json'
            original = json.dumps({'session_id': 'someone-else', 'status': 'active'})
            path.write_text(original)
            with patch.object(client, 'status') as status, patch.object(client, 'end') as end:
                with self.assertRaises(lg_tv.TVError):
                    client.begin(path)
                status.assert_not_called(); end.assert_not_called()
            self.assertEqual(path.read_text(), original)

    def test_begin_cleanup_does_not_close_replaced_session(self):
        client = lg_tv.TVClient.__new__(lg_tv.TVClient)
        client.host = '192.0.2.10'; client.device = 'test'; client.ws = None
        client.status = lambda: {'foreground': {'appId': 'disney'}, 'power': {'state': 'Screen Off'}}
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'session.json'
            replacement = {'session_id': 'replacement', 'status': 'active'}
            def request(uri, payload=None):
                path.write_text(json.dumps(replacement))
                raise ConnectionError('setup failed')
            client.request = request
            with patch.object(client, 'end') as end:
                with self.assertRaises(ConnectionError):
                    client.begin(path)
                end.assert_not_called()
            self.assertEqual(json.loads(path.read_text()), replacement)

    def test_end_rejects_another_device_session(self):
        client = lg_tv.TVClient.__new__(lg_tv.TVClient)
        client.host = '192.0.2.10'; client.device = 'test'
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'session.json'
            path.write_text(json.dumps({'host': '192.0.2.99', 'device': 'test', 'status': 'active'}))
            with self.assertRaises(lg_tv.TVError):
                client.end(path)

    def test_atlas_missing_views_remain_explicit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); targets = root / 'targets.json'
            targets.write_text(json.dumps({'apps': [{'slug': 'netflix', 'title': 'Netflix', 'app_id': None}]}))
            lg_tv.append_jsonl(root / 'statuses.jsonl', {'app_slug': 'netflix', 'view': 'all', 'status': 'login-required', 'note': 'Login wall observed.'})
            summary = build_atlas.build(root, root / 'atlas', targets)
            self.assertEqual(summary['verified_views'], 0)
            self.assertEqual(summary['requested_views'], 6)
            document = (root / 'atlas/apps/netflix.md').read_text()
            self.assertEqual(document.count('**Status:** login-required'), 6)
            self.assertNotIn('![', document)

    def test_atlas_prefers_verified_image_over_unreviewed_retry(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'one.jpg').write_bytes(b'one'); (root / 'two.jpg').write_bytes(b'two')
            captures = [{'capture_id': 'one', 'app_slug': 'app', 'view': 'home', 'file': 'one.jpg'},
                        {'capture_id': 'two', 'app_slug': 'app', 'view': 'home', 'file': 'two.jpg'}]
            rows = build_atlas.select_rows(root, [{'slug': 'app', 'title': 'App'}], captures,
                                           [{'capture_id': 'one', 'status': 'verified', 'note': 'Confirmed.'}], [])
            self.assertEqual(rows[0]['capture']['capture_id'], 'one')
            self.assertEqual(rows[0]['status'], 'verified')

    def test_atlas_uses_verified_view_without_changing_manifest_record(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / 'profiles.jpg').write_bytes(b'image')
            capture = {'capture_id': 'profiles', 'app_slug': 'app', 'view': 'home', 'file': 'profiles.jpg'}
            original = dict(capture)
            rows = build_atlas.select_rows(root, [{'slug': 'app', 'title': 'App'}], [capture],
                [{'capture_id': 'profiles', 'status': 'verified', 'verified_view': 'profiles', 'note': 'Profile selector observed.'}], [])
            home = next(row for row in rows if row['view'] == 'home')
            profiles = next(row for row in rows if row['view'] == 'profiles')
            self.assertIsNone(home['capture'])
            self.assertEqual(profiles['status'], 'verified')
            self.assertEqual(profiles['capture']['requested_view'], 'home')
            self.assertEqual(profiles['capture']['view'], 'profiles')
            self.assertEqual(capture, original)

    def test_polish_atlas_labels_and_machine_statuses_are_separate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); targets = root / 'targets.json'; notes = root / 'notes-pl.json'
            targets.write_text(json.dumps({'apps': [{'slug': 'app', 'title': 'Aplikacja'}]}))
            notes.write_text(json.dumps({'app': {'summary': 'Opis widocznego interfejsu.',
                                              'observations': ['Potwierdzona obserwacja.'], 'limitations': ['Brak kolejnych ekranów.']}}))
            summary = build_atlas.build(root, root / 'atlas', targets, notes, language='pl')
            document = (root / 'atlas/index.html').read_text()
            self.assertIn('<html lang="pl">', document)
            self.assertIn('Menu główne', document)
            self.assertIn('Wyszukiwanie', document)
            self.assertIn('Nie zaobserwowano', document)
            self.assertIn('Opis widocznego interfejsu.', document)
            self.assertIn('Ten ekran nie został jeszcze udokumentowany.', document)
            self.assertEqual(summary['language'], 'pl')
            self.assertIn('not-observed', (root / 'atlas/coverage.csv').read_text())
            self.assertEqual(summary['verified_views'], 0)

    def test_polish_verified_reclassification_preserves_source_label_in_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); targets = root / 'targets.json'
            targets.write_text(json.dumps({'apps': [{'slug': 'app', 'title': 'Aplikacja'}]}))
            (root / 'profile.jpg').write_bytes(b'image')
            lg_tv.append_jsonl(root / 'manifest.jsonl', {'capture_id': 'one', 'app_slug': 'app',
                'view': 'home', 'file': 'profile.jpg'})
            lg_tv.append_jsonl(root / 'reviews.jsonl', {'capture_id': 'one', 'status': 'verified',
                'verified_view': 'profiles', 'note': 'Potwierdzony wybór profilu.'})
            summary = build_atlas.build(root, root / 'atlas', targets, language='pl')
            self.assertEqual(summary['verified_views'], 1)
            document = (root / 'atlas/apps/app.md').read_text()
            self.assertIn('**Status:** Potwierdzono', document)
            self.assertIn('requested_view=home; verified_view=profiles', document)
            self.assertIn('Potwierdzony wybór profilu.', document)

    def test_atlas_ignores_unverified_or_invalid_view_override(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / 'image.jpg').write_bytes(b'image')
            capture = {'capture_id': 'image', 'app_slug': 'app', 'view': 'home', 'file': 'image.jpg'}
            for review in ({'status': 'blocked', 'verified_view': 'profiles'},
                           {'status': 'verified', 'verified_view': 'not-a-view'}):
                rows = build_atlas.select_rows(root, [{'slug': 'app', 'title': 'App'}], [capture],
                    [{'capture_id': 'image', **review}], [])
                self.assertIsNotNone(next(row for row in rows if row['view'] == 'home')['capture'])
                self.assertIsNone(next(row for row in rows if row['view'] == 'profiles')['capture'])

    def test_atlas_prefers_verified_reclassified_capture_over_unreviewed_profile(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'one.jpg').write_bytes(b'one'); (root / 'two.jpg').write_bytes(b'two')
            captures = [{'capture_id': 'one', 'app_slug': 'app', 'view': 'home', 'file': 'one.jpg'},
                        {'capture_id': 'two', 'app_slug': 'app', 'view': 'profiles', 'file': 'two.jpg'}]
            rows = build_atlas.select_rows(root, [{'slug': 'app', 'title': 'App'}], captures,
                [{'capture_id': 'one', 'status': 'verified', 'verified_view': 'profiles'}], [])
            profiles = next(row for row in rows if row['view'] == 'profiles')
            self.assertEqual(profiles['capture']['capture_id'], 'one')
            self.assertEqual(profiles['status'], 'verified')

    def test_atlas_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                build_atlas.safe_file(Path(temp), '../private-key')
            targets = Path(temp) / 'targets.json'
            targets.write_text(json.dumps({'apps': [{'slug': '../private', 'title': 'Bad'}]}))
            with self.assertRaises(ValueError):
                build_atlas.read_targets(targets, [])


if __name__ == '__main__':
    unittest.main()
