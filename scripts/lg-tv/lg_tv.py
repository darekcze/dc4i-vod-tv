#!/usr/bin/env python3
"""LG webOS capture client. Uses existing local pairing, Python standard library only."""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import ssl
import struct
import sys
import time
import urllib.parse
import urllib.request
import uuid
from zoneinfo import ZoneInfo

DEFAULT_ROOTS = (
    Path('/Volumes/AI-Hot/Services/LGWebOSRemote'),
    Path('/Volumes/Mac mini Data/AI-Hot/Services/LGWebOSRemote'),
)
VIEWS = ('home', 'settings', 'details', 'recommendations', 'profiles', 'search')
KEYS = frozenset(('UP', 'DOWN', 'LEFT', 'RIGHT', 'ENTER', 'BACK', 'HOME'))
OFF_STATES = frozenset(('Screen Off', 'ScreenOff', 'Screen Saver'))
MAX_IMAGE_BYTES = 16 * 1024 * 1024
SECRET_FIELDS = re.compile(r'(client.?key|password|passphrase|secret|token|authorization|^key$)', re.I)


class TVError(Exception):
    pass


def stamp():
    return dt.datetime.now(ZoneInfo('Europe/Warsaw')).isoformat(timespec='milliseconds')


def safe_slug(value):
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,79}', value):
        raise TVError('App slug must contain only lowercase letters, numbers, underscores and hyphens')
    return value


def redact(value):
    if isinstance(value, dict):
        return {k: '[REDACTED]' if SECRET_FIELDS.search(str(k)) else redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


def emit(value):
    print(json.dumps(redact(value), ensure_ascii=False), flush=True)


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex[:8] + '.tmp')
    temp.write_text(json.dumps(redact(value), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def append_jsonl(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(redact(value), ensure_ascii=False) + '\n')


def validate_url(url, host, schemes=('http', 'https')):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in schemes or parsed.hostname != host or parsed.username or parsed.password:
        raise TVError('Device returned an unexpected image or pointer endpoint')
    return parsed


class SameTVRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, host):
        self.host = host

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl, self.host)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def image_info(data):
    if data.startswith(b'\x89PNG\r\n\x1a\n') and len(data) >= 24:
        width, height = struct.unpack('>II', data[16:24])
        return '.png', width, height
    if not data.startswith(b'\xff\xd8\xff'):
        raise TVError('Capture response is not a PNG or JPEG image')
    index = 2
    while index < len(data) - 4:
        if data[index] != 255:
            index += 1
            continue
        while index < len(data) and data[index] == 255:
            index += 1
        if index >= len(data):
            break
        marker = data[index]
        index += 1
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            continue
        if index + 2 > len(data):
            break
        size = struct.unpack('>H', data[index:index + 2])[0]
        if size < 2 or index + size > len(data):
            break
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            if size < 7:
                break
            height, width = struct.unpack('>HH', data[index + 3:index + 7])
            return '.jpg', width, height
        if marker == 0xDA:
            break
        index += size
    raise TVError('JPEG dimensions could not be verified')


def resolve_root(value=None):
    candidates = [Path(value).expanduser()] if value else (
        [Path(os.environ['LGTV_ROOT']).expanduser()] if os.environ.get('LGTV_ROOT') else list(DEFAULT_ROOTS)
    )
    for root in candidates:
        if (root / '.config/lgtv/config.json').is_file() and (root / 'tools/lg_ssap_probe.py').is_file():
            return root.resolve()
    raise TVError('Existing LG pairing and lg_ssap_probe.py were not found; pass --root with the configured device path')


def configured_host(value=None):
    host = value if value is not None else os.environ.get('LGTV_HOST')
    if not isinstance(host, str) or not host.strip():
        raise TVError('Set --host or LGTV_HOST for operations that contact the television')
    host = host.strip()
    if any(c.isspace() for c in host) or any(c in host for c in '/@?#'):
        raise TVError('TV host must be a hostname or IP address, without URL components')
    return host


class TVClient:
    def __init__(self, root, host, device, timeout=8):
        self.root = Path(root)
        self.host = host
        self.device = device
        self.timeout = timeout
        self.ws = None
        self.helper = runpy.run_path(str(self.root / 'tools/lg_ssap_probe.py'))
        config = json.loads((self.root / '.config/lgtv/config.json').read_text(encoding='utf-8'))
        selected = config.get(device, {})
        if not selected.get('key'):
            raise TVError('No existing paired client key for the selected device; automatic pairing is disabled')
        self.hello = copy.deepcopy(runpy.run_path(str(self.root / 'source/LGTV/payload.py'))['hello_data'])
        self.hello['payload'].update({'client-key': selected['key'], 'forcePairing': False, 'pairingType': 'PROMPT'})

    def connect(self):
        if self.ws is not None:
            return
        for attempt in range(3):
            candidate = None
            try:
                # Retain the partially initialized object so a TLS handshake
                # timeout cannot leak the raw socket inside the existing helper.
                ws_type = self.helper['WS']
                candidate = ws_type.__new__(ws_type)
                ws_type.__init__(candidate, url_host=self.host, seconds=self.timeout)
                reply = self.helper['query'](candidate, self.hello)
                if reply.get('type') != 'registered':
                    raise TVError('Existing pairing was not accepted; no new pairing was requested')
                self.ws = candidate
                return
            except (OSError, EOFError, ConnectionError):
                self._close_transport(candidate)
                if attempt == 2:
                    raise
                time.sleep((0.7, 0.9)[attempt])
            except BaseException:
                self._close_transport(candidate)
                raise

    @staticmethod
    def _close_transport(transport):
        if transport is None:
            return
        # The helper's close() may itself fail if __init__ stopped before sock
        # was assigned. Close raw/sock separately as a best-effort fallback.
        for handle in (transport, getattr(transport, 'sock', None), getattr(transport, 'raw', None)):
            if handle is not None:
                try:
                    handle.close()
                except (OSError, AttributeError):
                    pass

    def close(self):
        if self.ws is not None:
            self._close_transport(self.ws)
            self.ws = None

    def request(self, uri, payload=None):
        self.connect()
        try:
            response = self.helper['query'](self.ws, {
                'id': 'dc4i-' + uuid.uuid4().hex[:12], 'type': 'request', 'uri': uri, 'payload': payload or {},
            })
        except (OSError, EOFError, ConnectionError):
            # A timed-out mutation may already have happened on the television.
            # Discard the connection, but never replay the request automatically.
            self.close()
            raise
        body = response.get('payload', {})
        if response.get('type') == 'error' or body.get('returnValue') is False:
            raise TVError('TV request failed for ' + uri + ': ' + str(body.get('errorCode', response.get('error', 'unknown'))))
        return body

    def status(self):
        power = self.request('ssap://com.webos.service.tvpower/power/getPowerState')
        foreground = self.request('ssap://com.webos.applicationManager/getForegroundAppInfo')
        return {'time': stamp(), 'host': self.host, 'device': self.device,
                'power': {k: power[k] for k in ('state', 'returnValue', 'processing') if k in power},
                'foreground': {k: foreground[k] for k in ('appId', 'windowId', 'processId') if k in foreground}}

    def apps(self):
        raw = None
        for endpoint in ('listApps', 'listLaunchPoints'):
            try:
                raw = self.request('ssap://com.webos.applicationManager/' + endpoint)
                rows = raw.get('apps', raw.get('launchPoints', []))
                if rows:
                    break
            except TVError:
                continue
        if raw is None or not rows:
            raise TVError('TV did not return its installed app inventory')
        apps = []
        for item in rows:
            app_id = item.get('id') or item.get('appId')
            if app_id:
                apps.append({'id': app_id, 'title': item.get('title') or item.get('name') or app_id,
                             **({k: item[k] for k in ('version', 'type') if k in item})})
        return apps

    def launch(self, app_id, settle=2.0):
        if app_id not in {item['id'] for item in self.apps()}:
            raise TVError('Refusing to launch an app absent from the installed app inventory')
        response = self.request('ssap://system.launcher/launch', {'id': app_id})
        time.sleep(settle)
        foreground = self.request('ssap://com.webos.applicationManager/getForegroundAppInfo').get('appId')
        return {'time': stamp(), 'requested_app': app_id, 'foreground_app': foreground,
                'launch_accepted': response.get('returnValue', True), 'foreground_matches': foreground == app_id}

    def keys(self, keys, interval=0.35):
        keys = [key.upper() for key in keys]
        if not keys or len(keys) > 50 or any(key not in KEYS for key in keys):
            raise TVError('Keys must be 1 to 50 UP/DOWN/LEFT/RIGHT/ENTER/BACK/HOME actions')
        if not 0.1 <= interval <= 2:
            raise TVError('Key interval must be from 0.1 to 2 seconds')
        body = self.request('ssap://com.webos.service.networkinput/getPointerInputSocket')
        url = body.get('socketPath')
        if not url:
            raise TVError('TV did not provide its paired pointer socket')
        parsed = validate_url(url, self.host, ('ws', 'wss'))
        self.close()
        pointer = self.helper['WS'](url_host=self.host, port=parsed.port or (3001 if parsed.scheme == 'wss' else 3000),
                                    uri=parsed.path + ('?' + parsed.query if parsed.query else ''),
                                    tls=parsed.scheme == 'wss', seconds=self.timeout)
        try:
            for key in keys:
                pointer.send('type:button\nname:' + key + '\n\n')
                time.sleep(interval)
        finally:
            pointer.close()
        return {'time': stamp(), 'keys_sent': keys, 'interval_seconds': interval}

    def capture(self, output, app_slug, view, note='', expected_app_id=None):
        app_slug = safe_slug(app_slug)
        if view not in VIEWS:
            raise TVError('Unknown capture view')
        status = self.status()
        state = status['power'].get('state')
        if state != 'Active':
            raise TVError('Display is not Active. Use begin to enable it temporarily and end to restore it')
        app_id = status['foreground'].get('appId')
        if expected_app_id and app_id != expected_app_id:
            raise TVError('Capture aborted because foreground app does not match the expected app')
        body = self.request('ssap://tv/executeOneShot')
        if body.get('returnValue') is not True:
            raise TVError('TV did not explicitly confirm a successful screen capture')
        uri = body.get('imageUri')
        if not uri:
            raise TVError('TV capture response contained no image URI')
        validate_url(uri, self.host)
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}), SameTVRedirect(self.host),
            urllib.request.HTTPSHandler(context=ssl._create_unverified_context()),
        )
        with opener.open(uri, timeout=12) as response:
            validate_url(response.geturl(), self.host)
            data = response.read(MAX_IMAGE_BYTES + 1)
        if len(data) > MAX_IMAGE_BYTES:
            raise TVError('Capture exceeded the 16 MiB size limit')
        extension, width, height = image_info(data)
        now = dt.datetime.now(ZoneInfo('Europe/Warsaw'))
        capture_id = now.strftime('%Y%m%dT%H%M%S%f') + '-' + uuid.uuid4().hex[:6]
        relative = Path(app_slug) / (view + '-' + capture_id + extension)
        path = Path(output) / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        receipt = {'schema_version': 1, 'capture_id': capture_id, 'time': now.isoformat(timespec='milliseconds'),
                   'timezone': 'Europe/Warsaw', 'app_slug': app_slug, 'view': view, 'app_id': app_id,
                   'expected_app_id': expected_app_id, 'power_state': state, 'file': relative.as_posix(),
                   'width': width, 'height': height, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                   'visual_status': 'unreviewed', 'note': note, 'method': 'ssap://tv/executeOneShot',
                   'capture_return_value': body['returnValue']}
        append_jsonl(Path(output) / 'manifest.jsonl', receipt)
        atomic_json(path.with_suffix('.json'), receipt)
        return {**receipt, 'absolute_file': str(path.resolve())}

    def begin(self, session_path):
        path = Path(session_path)
        if path.exists() and json.loads(path.read_text()).get('status') in ('active', 'needs_restore'):
            raise TVError('An unfinished session already exists. Restore it with end before starting another')
        initial = self.status()
        state = initial['power'].get('state')
        if state not in OFF_STATES | {'Active'}:
            raise TVError('The TV is not active or screen-off; this tool does not wake powered-off TVs')
        session = {'schema_version': 1, 'session_id': uuid.uuid4().hex, 'created_at': stamp(),
                   'status': 'needs_restore', 'initial': initial,
                   'restore_app': initial['foreground'].get('appId'), 'restore_screen_off': state in OFF_STATES,
                   'host': self.host, 'device': self.device}
        atomic_json(path, session)
        try:
            if state in OFF_STATES:
                self.request('ssap://com.webos.service.tvpower/power/turnOnScreen', {'standbyMode': 'active'})
                time.sleep(1.2)
            current = self.status()
            if current['power'].get('state') != 'Active':
                raise TVError('Display did not become Active; automatic restoration will be attempted')
            session.update({'status': 'active', 'started_at': stamp()})
            atomic_json(path, session)
            return session
        except BaseException as begin_error:
            # This receipt was created by this call. Do not close a pre-existing
            # session or a receipt replaced by another controller.
            try:
                current = json.loads(path.read_text(encoding='utf-8'))
                if current.get('session_id') != session['session_id']:
                    raise TVError('Session receipt ownership changed; cleanup skipped')
                current['begin_error_type'] = type(begin_error).__name__
                atomic_json(path, current)
                self.close()  # Discard a socket that may have failed during screen-on.
                self.end(path)
            except Exception as cleanup_error:
                try:
                    current = json.loads(path.read_text(encoding='utf-8'))
                    if current.get('session_id') == session['session_id']:
                        current.update({'status': 'needs_restore',
                                        'begin_error_type': type(begin_error).__name__,
                                        'begin_cleanup_error_type': type(cleanup_error).__name__})
                        atomic_json(path, current)
                except Exception:
                    pass  # Keep the original setup failure, never alter another receipt.
            raise

    def end(self, session_path):
        path = Path(session_path)
        session = json.loads(path.read_text(encoding='utf-8'))
        if session.get('host') != self.host or session.get('device') != self.device:
            raise TVError('Session belongs to another TV; restoration refused')
        if session.get('status') == 'restored':
            return session
        errors = []
        target = session.get('restore_app')
        try:
            current = self.status()['foreground'].get('appId')
            if target and current != target:
                result = self.launch(target)
                if not result.get('foreground_matches'):
                    errors.append('original_app_not_confirmed')
        except Exception as exc:
            errors.append('app_restore_' + type(exc).__name__)
        try:
            if session.get('restore_screen_off'):
                self.request('ssap://com.webos.service.tvpower/power/turnOffScreen', {'standbyMode': 'active'})
            session['final'] = self.status()
            expected = OFF_STATES if session.get('restore_screen_off') else {'Active'}
            if session['final']['power'].get('state') not in expected:
                errors.append('display_state_not_confirmed')
        except Exception as exc:
            errors.append('display_restore_' + type(exc).__name__)
        session.update({'status': 'needs_restore' if errors else 'restored', 'ended_at': stamp(), 'restore_errors': errors})
        atomic_json(path, session)
        if errors:
            raise TVError('Session restoration incomplete; see the session receipt')
        return session


def validate_recipe(recipe):
    if recipe.get('schema_version') != 1 or recipe.get('reviewed') is not True:
        raise TVError('Only schema_version 1 recipes with reviewed=true may execute')
    safe_slug(recipe.get('app_slug', ''))
    if not isinstance(recipe.get('app_id'), str) or not recipe['app_id']:
        raise TVError('Recipe requires an exact installed app_id')
    steps = recipe.get('steps')
    if not isinstance(steps, list) or not 1 <= len(steps) <= 300:
        raise TVError('Recipe must contain 1 to 300 steps')
    if steps[0].get('action') != 'launch':
        raise TVError('Recipe must start by launching its app')
    for step in steps:
        action = step.get('action')
        allowed = {'launch': {'action', 'wait'}, 'key': {'action', 'keys', 'interval'},
                   'wait': {'action', 'seconds'}, 'capture': {'action', 'view', 'note'}}
        if action not in allowed or set(step) - allowed[action]:
            raise TVError('Recipe contains an unknown action or field')
        if action == 'key':
            keys = step.get('keys')
            if not isinstance(keys, list) or not 1 <= len(keys) <= 50 or any(k not in KEYS for k in keys):
                raise TVError('Recipe contains an unapproved key')
            if not 0.1 <= step.get('interval', 0.35) <= 2:
                raise TVError('Recipe key interval is outside permitted bounds')
        elif action == 'capture' and step.get('view') not in VIEWS:
            raise TVError('Recipe contains an unknown view')
        elif action == 'wait' and not 0 <= step.get('seconds', -1) <= 10:
            raise TVError('Recipe wait must be from 0 to 10 seconds')
        elif action == 'launch' and not 0 <= step.get('wait', 2) <= 10:
            raise TVError('Recipe launch wait must be from 0 to 10 seconds')
    return recipe


def run_flow(client, recipe, output, resume=False):
    validate_recipe(recipe)
    output = Path(output)
    fingerprint = hashlib.sha256(json.dumps(recipe, sort_keys=True).encode()).hexdigest()
    state_path = output / '.flow-state' / (recipe['app_slug'] + '-' + fingerprint[:16] + '.json')
    state = json.loads(state_path.read_text()) if resume and state_path.exists() else {
        'recipe_sha256': fingerprint, 'completed_captures': {}, 'steps': []}
    if state.get('recipe_sha256') != fingerprint:
        raise TVError('Recipe changed; refusing to use a mismatched checkpoint')
    # Replay navigation from the start, skipping completed capture writes only.
    # Resuming at an arbitrary key step would assume an unverified TV UI state.
    for index, step in enumerate(recipe['steps']):
        action = step['action']
        if action == 'launch':
            result = client.launch(recipe['app_id'], step.get('wait', 2))
            if not result.get('foreground_matches'):
                raise TVError('Recipe launch did not reach its expected app')
        elif action == 'key':
            result = client.keys(step['keys'], step.get('interval', 0.35))
        elif action == 'wait':
            time.sleep(step['seconds'])
            result = {'wait_seconds': step['seconds']}
        elif str(index) in state['completed_captures']:
            receipt = state['completed_captures'][str(index)]
            path = output / receipt['file']
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != receipt['sha256']:
                raise TVError('A completed capture is missing or changed; checkpoint was not skipped')
            result = {'skipped_existing_capture': receipt['capture_id']}
        else:
            result = client.capture(output, recipe['app_slug'], step['view'], step.get('note', ''), recipe['app_id'])
            state['completed_captures'][str(index)] = {k: result[k] for k in ('capture_id', 'file', 'sha256')}
        state['steps'].append({'index': index, 'action': action, 'time': stamp(), 'result': result})
        state['updated_at'] = stamp()
        atomic_json(state_path, state)
        emit({'step': index, 'action': action, 'result': result})
    return {'recipe': recipe['app_slug'], 'state_file': str(state_path), 'capture_count': len(state['completed_captures'])}


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', help='Existing LGWebOSRemote directory on the chosen Mac')
    p.add_argument('--host', help='TV hostname/IP; defaults to LGTV_HOST when set')
    p.add_argument('--device', default='LG_OLED55G42LW')
    p.add_argument('--output', default='private/lg-tv-captures')
    p.add_argument('--timeout', type=float, default=8)
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('status')
    sub.add_parser('apps')
    launch = sub.add_parser('launch'); launch.add_argument('app_id'); launch.add_argument('--wait', type=float, default=2)
    key = sub.add_parser('key'); key.add_argument('keys', nargs='+'); key.add_argument('--interval', type=float, default=0.35)
    cap = sub.add_parser('capture')
    cap.add_argument('--app-slug', required=True); cap.add_argument('--view', choices=VIEWS, required=True)
    cap.add_argument('--note', default=''); cap.add_argument('--expected-app-id')
    for command in ('begin', 'end'):
        sub.add_parser(command).add_argument('--session', required=True)
    flow = sub.add_parser('flow'); flow.add_argument('recipe'); flow.add_argument('--resume', action='store_true')
    flow.add_argument('--session', help='Optional session to begin and restore automatically for this flow')
    mark = sub.add_parser('review'); mark.add_argument('--capture-id', required=True)
    mark.add_argument('--status', choices=('verified', 'incorrect', 'blocked'), required=True)
    mark.add_argument('--note', default='')
    mark.add_argument('--verified-view', choices=VIEWS, help='Verified actual menu; immutable capture manifest is preserved')
    status = sub.add_parser('mark-status'); status.add_argument('--app-slug', required=True)
    status.add_argument('--view', choices=VIEWS + ('all',), required=True)
    status.add_argument('--status', choices=('not-installed', 'login-required', 'not-available', 'not-observed', 'error'), required=True)
    status.add_argument('--note', required=True)
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    output = Path(args.output).expanduser().resolve()
    if args.command in ('review', 'mark-status'):
        record = {'time': stamp(), 'status': args.status, 'note': args.note}
        if args.command == 'review':
            if args.verified_view is not None:
                if args.status != 'verified':
                    raise TVError('--verified-view requires --status verified')
                record['verified_view'] = args.verified_view
            record['capture_id'] = args.capture_id
            path = output / 'reviews.jsonl'
        else:
            record.update({'app_slug': safe_slug(args.app_slug), 'view': args.view})
            path = output / 'statuses.jsonl'
        append_jsonl(path, record)
        emit(record)
        return 0
    args.host = configured_host(args.host)
    if not 0.5 <= args.timeout <= 15:
        raise TVError('Timeout must be from 0.5 to 15 seconds')
    if args.command == 'launch' and not 0 <= args.wait <= 10:
        raise TVError('Launch wait must be from 0 to 10 seconds')
    root = resolve_root(args.root)
    # Prevent overlapping controls on one Mac. Select one host for an audit.
    import fcntl
    lock = (root / '.capture-control.lock').open('a')
    try:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise TVError('Another local LG capture command is active')
    client = TVClient(root, args.host, args.device, args.timeout)
    try:
        if args.command == 'status':
            result = client.status()
        elif args.command == 'apps':
            result = {'time': stamp(), 'host': args.host, 'apps': client.apps()}
            atomic_json(output / 'installed-apps.json', result)
        elif args.command == 'launch':
            result = client.launch(args.app_id, args.wait)
        elif args.command == 'key':
            result = client.keys(args.keys, args.interval)
        elif args.command == 'capture':
            result = client.capture(output, args.app_slug, args.view, args.note, args.expected_app_id)
        elif args.command in ('begin', 'end'):
            result = getattr(client, args.command)(args.session)
        elif args.command == 'flow':
            recipe = validate_recipe(json.loads(Path(args.recipe).read_text(encoding='utf-8')))
            if args.session:
                client.begin(args.session)
            try:
                result = run_flow(client, recipe, output, args.resume)
            finally:
                if args.session:
                    client.end(args.session)
        emit(result)
        return 0
    finally:
        client.close()
        lock.close()


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        emit({'error': 'Interrupted. Restore an open session using end --session PATH.'})
        raise SystemExit(130)
    except TVError as exc:
        emit({'error': str(exc)})
        raise SystemExit(2)
    except Exception as exc:
        # Raw network/config errors can contain endpoints or secrets. Retain only type.
        emit({'error': 'Operation failed', 'error_type': type(exc).__name__,
              'next_step': 'Check host connectivity and existing local pairing; restore any open session.'})
        raise SystemExit(3)
