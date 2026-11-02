#!/usr/bin/env python3
"""Repeat private streaming-app entry checkpoints using the existing session wrapper."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

KIT = Path(__file__).resolve().parent


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', help='Existing configured LGWebOSRemote root; wrapper auto-detects when omitted')
    p.add_argument('--host', default=os.environ.get('LGTV_HOST'), help='TV host, or set LGTV_HOST locally')
    p.add_argument('--device', default='LG_OLED55G42LW', help='Existing paired profile')
    p.add_argument('--output', required=True, help='New private run directory; must not already exist')
    p.add_argument('--tools', default=str(KIT.parent / 'scripts' / 'lg-tv'),
                   help='Directory containing canonical capture_session.py, lg_tv.py and run_plan.py')
    p.add_argument('--apps', help='Comma-separated exact registry slugs; default: all 19 apps in registry order')
    p.add_argument('--dry-run', action='store_true', help='Pass through wrapper validation without TV contact or file creation')
    return p


def main(argv=None):
    p = parser()
    args = p.parse_args(argv)
    tools = Path(args.tools).expanduser().resolve()
    for name in ('capture_session.py', 'lg_tv.py', 'run_plan.py'):
        if not (tools / name).is_file():
            p.error('Missing canonical tool: ' + str(tools / name))
    registry = json.loads((KIT / 'targets.json').read_text(encoding='utf-8'))
    entries = {app['slug']: app for app in registry['apps']}
    slugs = list(entries) if args.apps is None else [value.strip() for value in args.apps.split(',')]
    if not slugs or any(not slug for slug in slugs) or len(set(slugs)) != len(slugs):
        p.error('--apps must contain nonempty, unique slugs')
    unknown = [slug for slug in slugs if slug not in entries]
    if unknown:
        p.error('Unknown app slug(s): ' + ', '.join(unknown) + '. Available: ' + ', '.join(entries))
    output = Path(args.output).expanduser().resolve()
    if output.exists():
        p.error('--output must be a new run directory, including after an earlier restored session')
    if not args.dry_run and (not args.host or not args.host.strip()):
        p.error('Provide --host or set LGTV_HOST; pairing is never created by this launcher')
    command = [sys.executable, '-B', str(tools / 'capture_session.py'),
               '--output', str(output), '--session', str(output / 'session.json'),
               '--device', args.device]
    if args.root:
        command += ['--root', str(Path(args.root).expanduser().resolve())]
    if args.host:
        command += ['--host', args.host]
    for slug in slugs:
        plan_path = KIT / 'plans' / (slug + '.json')
        plan = json.loads(plan_path.read_text(encoding='utf-8'))
        if plan.get('app_slug') != slug or plan.get('app_id') != entries[slug]['app_id']:
            p.error('Plan identity differs from the exact registry: ' + slug)
        command += ['--plan', str(plan_path)]
    if args.dry_run:
        command.append('--dry-run')
    else:
        # Reserve a fresh run. Only the canonical wrapper owns the session.
        output.mkdir(parents=True, exist_ok=False)
    # Replace this launcher so signals and exit status belong directly to the wrapper.
    os.execv(sys.executable, command)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({'error': str(exc), 'tv_client': 'canonical capture_session.py'}), file=sys.stderr)
        raise SystemExit(2)
