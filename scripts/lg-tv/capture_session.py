#!/usr/bin/env python3
"""Run validated, already-observed TV plans in one owned session, then restore it."""
from __future__ import annotations

import argparse
import fcntl
import json
from pathlib import Path
import sys
import uuid

import lg_tv
import run_plan


class SessionOwnershipError(lg_tv.TVError):
    pass


def read_plans(paths):
    if not 1 <= len(paths) <= 100:
        raise lg_tv.TVError('Provide between 1 and 100 --plan files')
    plans = []
    for path in paths:
        with Path(path).open('rb') as handle:
            raw = handle.read(run_plan.MAX_PLAN_BYTES + 1)
        if len(raw) > run_plan.MAX_PLAN_BYTES:
            raise lg_tv.TVError('Plan exceeds the 256 KiB limit')
        plans.append(run_plan.validate_plan(json.loads(raw)))
    return plans


def identity(session):
    return {key: session.get(key) for key in ('session_id', 'created_at', 'host', 'device')}


def read_owned_session(path, owned, active=False):
    try:
        session = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise SessionOwnershipError('Owned session receipt cannot be verified') from exc
    if not isinstance(session, dict) or identity(session) != owned:
        raise SessionOwnershipError('Session receipt was replaced; no cleanup commands will be sent')
    if active and session.get('status') != 'active':
        raise lg_tv.TVError('Owned capture session is no longer active')
    return session


def execute_owned_session(client, plans, output, session_path, host, device,
                          plan_paths=None, runner=run_plan.execute_plan):
    """Caller holds the local TV command lock. Never resumes or adopts another session."""
    for plan in plans:
        run_plan.validate_plan(plan)
    path = Path(session_path)
    if path.exists():
        raise lg_tv.TVError('Choose a fresh --session path; existing receipts are never adopted or overwritten')
    output = Path(output)
    wrapper_id = uuid.uuid4().hex
    summary_path = output / 'session-runs' / (wrapper_id + '.json')
    summary = {'schema_version': 1, 'wrapper_id': wrapper_id, 'started_at': lg_tv.stamp(),
               'status': 'running', 'session_file': str(path), 'plan_count': len(plans),
               'plan_files': list(map(str, plan_paths or [])), 'completed_plans': [],
               'restore_status': 'not_started', 'live_validation': 'not_asserted_by_runner'}
    owned = None
    failure = None
    try:
        started = client.begin(path)
        if not isinstance(started.get('session_id'), str) or not started['session_id']:
            raise lg_tv.TVError('Session client did not provide an ownership token')
        owned = identity(started)
        summary['owned_session'] = owned
        read_owned_session(path, owned, active=True)
        for index, plan in enumerate(plans):
            read_owned_session(path, owned, active=True)
            result = runner(client, plan, output, path, host, device)
            summary['completed_plans'].append({'index': index, 'app_slug': plan['app_slug'], 'result': result})
            lg_tv.atomic_json(summary_path, summary)
        summary['status'] = 'completed'
    except BaseException as exc:
        failure = exc
        summary.update({'status': 'interrupted' if isinstance(exc, KeyboardInterrupt) else 'failed',
                        'error_type': type(exc).__name__})
    finally:
        if owned is not None:
            try:
                current = read_owned_session(path, owned)
                if current.get('status') == 'restored':
                    summary['restore_status'] = 'already_restored'
                elif current.get('status') in ('active', 'needs_restore'):
                    restored = client.end(path)
                    if identity(restored) != owned or restored.get('status') != 'restored':
                        raise lg_tv.TVError('Session client did not confirm restoration')
                    summary['restore_status'] = 'restored'
                else:
                    raise lg_tv.TVError('Unknown owned-session status; cleanup was not attempted')
            except SessionOwnershipError:
                summary['restore_status'] = 'skipped_ownership_changed'
                summary['status'] = 'failed'
            except Exception as exc:
                summary.update({'restore_status': 'failed', 'restore_error_type': type(exc).__name__, 'status': 'failed'})
        elif path.exists():
            # lg_tv.begin owns setup-failure cleanup. Without its returned token,
            # this wrapper must not infer ownership or repeat restoration actions.
            summary['restore_status'] = 'begin_failed_see_session_receipt'
            try:
                summary['session_status_on_exit'] = json.loads(path.read_text(encoding='utf-8')).get('status')
            except (OSError, ValueError):
                pass
        client.close()
        summary['ended_at'] = lg_tv.stamp()
        summary['summary_file'] = str(summary_path)
        lg_tv.atomic_json(summary_path, summary)
    if failure is not None:
        raise failure
    if summary['restore_status'] not in ('restored', 'already_restored'):
        raise lg_tv.TVError('Session restoration was not confirmed; inspect the session-run summary')
    return summary


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', help='Existing LGWebOSRemote root; auto-detect on the selected Mac when omitted')
    p.add_argument('--host', help='TV hostname/IP; defaults to LGTV_HOST when set')
    p.add_argument('--device', default='LG_OLED55G42LW')
    p.add_argument('--timeout', type=float, default=8)
    p.add_argument('--output', required=True, help='Private evidence destination, for example private/lg-tv-captures/RUN')
    p.add_argument('--session', required=True, help='Fresh receipt path owned only by this invocation')
    p.add_argument('--plan', action='append', required=True, help='Already-observed JSON plan; repeat for each app or batch')
    p.add_argument('--dry-run', action='store_true', help='Validate all plans without resolving pairing, creating a session or contacting the TV')
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    run_plan.bounded_number(args.timeout, 0.5, 30, 'Timeout')
    # Every file and step is validated before private configuration or TV access.
    plans = read_plans(args.plan)
    if args.dry_run:
        lg_tv.emit({'status': 'dry_run', 'plan_count': len(plans),
                    'applications': [plan['app_slug'] for plan in plans],
                    'step_count': sum(len(plan['steps']) for plan in plans),
                    'session_file': args.session, 'output': args.output,
                    'tv_contacted': False, 'session_created': False,
                    'live_validation': 'unverified'})
        return 0
    args.host = lg_tv.configured_host(args.host)
    path = Path(args.session).expanduser().resolve()
    if path.exists():
        raise lg_tv.TVError('Choose a fresh --session path; existing receipts are never adopted or overwritten')
    root = lg_tv.resolve_root(args.root)
    output = Path(args.output).expanduser().resolve()
    with (root / '.capture-control.lock').open('a') as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise lg_tv.TVError('Another local process controls this TV; wait for it to finish') from exc
        if path.exists():
            raise lg_tv.TVError('Session path appeared while waiting; it will not be adopted')
        client = lg_tv.TVClient(root, args.host, args.device, args.timeout)
        try:
            result = execute_owned_session(client, plans, output, path, args.host, args.device, args.plan)
            lg_tv.emit(result)
        finally:
            client.close()
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        lg_tv.emit({'error': 'Interrupted; inspect the owned session receipt to verify restoration.'})
        raise SystemExit(130)
    except (lg_tv.TVError, ValueError, OSError) as exc:
        lg_tv.emit({'error_type': type(exc).__name__,
                    'error': str(exc) if isinstance(exc, lg_tv.TVError) else 'Capture session did not complete; inspect its private summary.',
                    'next_step': 'Check the actual TV and receipt state before retrying. Mutations are never automatically replayed.'})
        raise SystemExit(2)
