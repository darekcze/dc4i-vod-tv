#!/usr/bin/env python3
"""Execute observed LG TV navigation steps inside an already active capture session."""
from __future__ import annotations

import argparse
import fcntl
import json
import math
from pathlib import Path
import sys
import time
import uuid

import lg_tv


MAX_PLAN_BYTES = 256 * 1024


def bounded_number(value, minimum, maximum, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise lg_tv.TVError(label + ' must be a number')
    if not math.isfinite(value) or not minimum <= value <= maximum:
        raise lg_tv.TVError(label + ' is outside permitted bounds')
    return float(value)


def validate_plan(plan):
    if not isinstance(plan, dict) or set(plan) - {'schema_version', 'app_slug', 'app_id', 'steps'}:
        raise lg_tv.TVError('Plan contains unknown fields or is not an object')
    if plan.get('schema_version', 1) != 1:
        raise lg_tv.TVError('Only plan schema version 1 is supported')
    if not isinstance(plan.get('app_slug'), str):
        raise lg_tv.TVError('Plan requires an app_slug string')
    lg_tv.safe_slug(plan['app_slug'])
    app = plan.get('app_id')
    if not isinstance(app, str) or not app or len(app) > 256 or any(c.isspace() for c in app):
        raise lg_tv.TVError('Plan requires an exact app_id string without whitespace')
    steps = plan.get('steps')
    if not isinstance(steps, list) or not 1 <= len(steps) <= 40:
        raise lg_tv.TVError('Plan must contain 1 to 40 steps')
    for step in steps:
        if not isinstance(step, dict):
            raise lg_tv.TVError('Each plan step must be an object')
        actions = set(step) & {'launch', 'keys', 'capture'}
        if len(actions) > 1:
            raise lg_tv.TVError('A step cannot combine multiple actions')
        if not actions:
            if set(step) != {'wait'}:
                raise lg_tv.TVError('Unknown plan action or field')
            bounded_number(step['wait'], 0, 30, 'Wait')
            continue
        action = next(iter(actions))
        allowed = {'launch': {'launch', 'wait'}, 'keys': {'keys', 'wait', 'interval'},
                   'capture': {'capture', 'note'}}[action]
        if set(step) - allowed:
            raise lg_tv.TVError('Step contains an unknown field')
        if action == 'launch':
            if step['launch'] != app:
                raise lg_tv.TVError('Launch target differs from the plan app_id')
            bounded_number(step.get('wait', 12), 0, 30, 'Launch wait')
        elif action == 'keys':
            keys = step['keys']
            if not isinstance(keys, list) or not 1 <= len(keys) <= 50:
                raise lg_tv.TVError('Keys must be a list of 1 to 50 approved buttons')
            if any(not isinstance(k, str) or k not in lg_tv.KEYS for k in keys):
                raise lg_tv.TVError('Plan contains an unapproved button')
            bounded_number(step.get('interval', 0.4), 0.1, 2, 'Key interval')
            bounded_number(step.get('wait', 1.3), 0, 30, 'Key settle wait')
        elif step['capture'] not in lg_tv.VIEWS:
            raise lg_tv.TVError('Unknown capture view')
        elif not isinstance(step.get('note', ''), str) or len(step.get('note', '')) > 4096:
            raise lg_tv.TVError('Capture note must be a string of at most 4096 characters')
    return plan


def read_active_session(path, host, device, expected=None):
    try:
        session = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise lg_tv.TVError('A readable existing session receipt is required') from exc
    if not isinstance(session, dict) or session.get('status') != 'active':
        raise lg_tv.TVError('Capture session is not active')
    if session.get('host') != host or session.get('device') != device:
        raise lg_tv.TVError('Session belongs to a different TV')
    # Keep legacy receipts usable without accepting a replaced modern session.
    identity = {k: session.get(k) for k in ('session_id', 'created_at', 'host', 'device')}
    if expected is not None and identity != expected:
        raise lg_tv.TVError('Capture session changed during the plan')
    return identity


def check_foreground(state, app):
    if state.get('power', {}).get('state') != 'Active':
        raise lg_tv.TVError('Display is no longer Active')
    if state.get('foreground', {}).get('appId') != app:
        raise lg_tv.TVError('Foreground app changed before navigation')


def key_batches(keys):
    """Recheck the foreground after a button that can enter or leave a view."""
    batch = []
    for key in keys:
        batch.append(key)
        if key in {'HOME', 'BACK', 'ENTER'}:
            yield batch
            batch = []
    if batch:
        yield batch


def execute_plan(client, plan, output, session_path, host, device, sleeper=time.sleep):
    """Run one batch. The caller must hold the root's command lock."""
    validate_plan(plan)
    identity = read_active_session(session_path, host, device)
    output = Path(output)
    slug, app = plan['app_slug'], plan['app_id']
    run_id = lg_tv.stamp().replace(':', '').replace('+', '_') + '-' + uuid.uuid4().hex[:8]
    run_path = output / 'runs' / (run_id + '-' + slug + '.json')
    result_path = run_path.with_suffix('.result.json')
    lg_tv.atomic_json(run_path, plan)
    result = {'schema_version': 1, 'run_id': run_id, 'app_slug': slug, 'app_id': app,
              'session': str(Path(session_path)), 'started_at': lg_tv.stamp(),
              'status': 'running', 'completed_steps': 0, 'plan_file': str(run_path)}

    def log(**fields):
        lg_tv.append_jsonl(output / 'actions.jsonl', {'time': lg_tv.stamp(), 'run_id': run_id,
                                                    'app_slug': slug, **fields})

    active_index = None
    try:
        state = client.status()
        if state.get('power', {}).get('state') in lg_tv.OFF_STATES:
            read_active_session(session_path, host, device, identity)
            log(action='enable_display', phase='start')
            client.request('ssap://com.webos.service.tvpower/power/turnOnScreen', {'standbyMode': 'active'})
            sleeper(1.2)
            state = client.status()
            if state.get('power', {}).get('state') != 'Active':
                raise lg_tv.TVError('Display did not become Active')
            log(action='enable_display', phase='completed', observed_state='Active')
        elif state.get('power', {}).get('state') != 'Active':
            raise lg_tv.TVError('Display is not active or in a restorable screen-off state')
        for index, step in enumerate(plan['steps']):
            active_index = index
            read_active_session(session_path, host, device, identity)
            log(step_index=index, step=step, phase='start')
            if 'launch' in step:
                value = client.launch(app, settle=bounded_number(step.get('wait', 12), 0, 30, 'Launch wait'))
                if not value.get('foreground_matches'):
                    raise lg_tv.TVError('App launch was not confirmed')
            elif 'keys' in step:
                sent = []
                for batch_index, batch in enumerate(key_batches(step['keys'])):
                    # HOME/BACK/ENTER can change the active app. Never send
                    # subsequent input based on the state before that action.
                    read_active_session(session_path, host, device, identity)
                    check_foreground(client.status(), app)
                    log(step_index=index, key_batch=batch_index, keys=batch, phase='start')
                    batch_value = client.keys(batch, interval=step.get('interval', 0.4))
                    sent.extend(batch)
                    log(step_index=index, key_batch=batch_index, phase='completed', result=batch_value)
                value = {'keys_sent': sent}
                sleeper(step.get('wait', 1.3))
            elif 'capture' in step:
                value = client.capture(output, slug, step['capture'], note=step.get('note', ''), expected_app_id=app)
            else:
                sleeper(step['wait'])
                value = {'wait_seconds': step['wait']}
            log(step_index=index, phase='completed', result=value)
            result['completed_steps'] += 1
            lg_tv.emit({'run_id': run_id, 'step_index': index, 'result': value})
        result['status'] = 'completed'
        return result
    except BaseException as exc:
        result.update({'status': 'interrupted' if isinstance(exc, KeyboardInterrupt) else 'failed',
                       'failed_step': active_index, 'error_type': type(exc).__name__})
        log(step_index=active_index, phase='failed', error_type=type(exc).__name__)
        raise
    finally:
        result['ended_at'] = lg_tv.stamp()
        result['session_cleanup'] = 'managed_by_calling_controller'
        lg_tv.atomic_json(result_path, result)
        client.close()


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', help='Existing LGWebOSRemote root; auto-detect when omitted')
    p.add_argument('--host', help='TV hostname/IP; defaults to LGTV_HOST when set')
    p.add_argument('--device', default='LG_OLED55G42LW')
    p.add_argument('--timeout', type=float, default=8)
    p.add_argument('--output', required=True, help='Private capture run directory')
    p.add_argument('--session', required=True, help='Existing active session receipt; not created or ended here')
    choice = p.add_mutually_exclusive_group(required=True)
    choice.add_argument('--plan', help='Path to a JSON plan')
    choice.add_argument('--plan-json', help='Literal JSON plan; prefer --plan for larger inputs')
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    bounded_number(args.timeout, 0.5, 30, 'Timeout')
    if args.plan:
        with Path(args.plan).open('rb') as source:
            raw = source.read(MAX_PLAN_BYTES + 1)
    else:
        raw = args.plan_json.encode('utf-8')
    if len(raw) > MAX_PLAN_BYTES:
        raise lg_tv.TVError('Plan exceeds the 256 KiB limit')
    plan = validate_plan(json.loads(raw))
    args.host = lg_tv.configured_host(args.host)
    read_active_session(args.session, args.host, args.device)
    root = lg_tv.resolve_root(args.root)
    with (root / '.capture-control.lock').open('a') as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise lg_tv.TVError('Another local process controls this TV; wait for it to finish') from exc
        client = lg_tv.TVClient(root, args.host, args.device, args.timeout)
        try:
            result = execute_plan(client, plan, args.output, args.session, args.host, args.device)
            lg_tv.emit(result)
        finally:
            client.close()
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        lg_tv.emit({'error': 'Interrupted; the owning controller must restore the active session with lg_tv.py end.'})
        raise SystemExit(130)
    except (lg_tv.TVError, ValueError, OSError) as exc:
        message = str(exc) if isinstance(exc, lg_tv.TVError) else 'Plan could not complete; inspect actions.jsonl and the result receipt.'
        lg_tv.emit({'error_type': type(exc).__name__, 'error': message,
                    'next_step': 'Check the actual app state before retrying; restore the session when the audit ends.'})
        raise SystemExit(2)
