#!/usr/bin/env python3
"""Build a private, standalone HTML atlas and separate app notes from LG captures."""
from __future__ import annotations

import argparse
import base64
import csv
import datetime as dt
import html
import json
import os
from pathlib import Path
import re
from zoneinfo import ZoneInfo

VIEWS = ('home', 'settings', 'details', 'recommendations', 'profiles', 'search')
LABELS = {'home': 'Home menu', 'settings': 'Settings menu', 'details': 'Title details',
          'recommendations': 'Recommendations', 'profiles': 'Profiles', 'search': 'Search'}
UI = {
    'en': {
        'labels': LABELS, 'title': 'DC4I VOD TV: streaming app screen atlas',
        'intro': ('Screenshots were captured from the actual LG TV using its paired SSAP connection. '
                  'View labels use verified reclassification when available. Only rows marked verified '
                  'have been visually checked. Missing, unavailable and sign-in-blocked screens remain explicit.'),
        'counts': '{apps} apps; {verified} verified views; {captured} image-backed rows; {requested} requested views.',
        'generated': 'Generated', 'application': 'Application', 'app_id': 'Application ID',
        'unresolved': 'not resolved', 'observations': 'Observed interface patterns', 'limitations': 'Limitations',
        'evidence': 'Evidence', 'not_documented': 'This screen has not been documented.',
        'missing_file': 'Capture receipt exists, but its image file is missing.',
        'awaiting_review': 'Captured, awaiting visual verification of the requested menu.',
        'statuses': {},
    },
    'pl': {
        'labels': {'home': 'Menu główne', 'settings': 'Ustawienia', 'details': 'Szczegóły tytułu',
                   'recommendations': 'Rekomendacje', 'profiles': 'Profile', 'search': 'Wyszukiwanie'},
        'title': 'DC4I VOD TV: atlas ekranów aplikacji streamingowych',
        'intro': ('Zrzuty pochodzą z rzeczywistego telewizora LG i jego sparowanego połączenia SSAP. '
                  'Nazwy widoków uwzględniają potwierdzoną klasyfikację. Tylko pozycje oznaczone jako '
                  'Potwierdzono zostały sprawdzone wizualnie. Braki, niedostępne menu i ekrany logowania są opisane osobno.'),
        'counts': '{apps} aplikacji; {verified} potwierdzonych widoków; {captured} pozycji z obrazem; {requested} wymaganych widoków.',
        'generated': 'Wygenerowano', 'application': 'Aplikacja', 'app_id': 'Identyfikator aplikacji',
        'unresolved': 'nie ustalono', 'observations': 'Zaobserwowane elementy interfejsu', 'limitations': 'Ograniczenia',
        'evidence': 'Dane źródłowe', 'not_documented': 'Ten ekran nie został jeszcze udokumentowany.',
        'missing_file': 'Istnieją metadane zrzutu, ale brakuje pliku obrazu.',
        'awaiting_review': 'Zrzut zapisano. Oczekuje na wizualne potwierdzenie wskazanego menu.',
        'statuses': {'verified': 'Potwierdzono', 'unreviewed': 'Do weryfikacji', 'blocked': 'Zablokowane',
                     'incorrect': 'Niewłaściwy widok', 'not-installed': 'Brak aplikacji',
                     'login-required': 'Wymagane logowanie', 'not-available': 'Niedostępne',
                     'not-observed': 'Nie zaobserwowano', 'error': 'Błąd', 'missing-file': 'Brak pliku'},
    },
}


def locale(language):
    if language not in UI:
        raise ValueError('Language must be en or pl')
    return UI[language]


def read_jsonl(path):
    if not path.exists():
        return []
    result = []
    for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if line.strip():
            try:
                result.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f'Invalid JSON on line {number} of {path.name}') from exc
    return result


def safe_file(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('A screenshot path points outside the capture directory')
    return path


def read_targets(path, captures):
    value = json.loads(path.read_text(encoding='utf-8')) if path and path.exists() else []
    targets = value.get('apps', []) if isinstance(value, dict) else value
    targets = [dict(item) for item in targets]
    for item in targets:
        if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,79}', item.get('slug', '')):
            raise ValueError('An application slug is not a safe directory name')
    known = {item['slug'] for item in targets}
    for capture in captures:
        if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,79}', capture.get('app_slug', '')):
            raise ValueError('A capture application slug is not a safe directory name')
        if capture['app_slug'] not in known:
            targets.append({'slug': capture['app_slug'], 'title': capture['app_slug'], 'app_id': capture.get('app_id')})
            known.add(capture['app_slug'])
    return targets


def select_rows(root, targets, captures, reviews, statuses, language='en'):
    ui = locale(language)
    review_map = {row['capture_id']: row for row in reviews}
    status_map = {(row['app_slug'], row['view']): row for row in statuses}
    candidates = {}
    for capture in captures:
        if capture.get('view') not in VIEWS:
            continue
        review = review_map.get(capture['capture_id'], {})
        state = review.get('status', capture.get('visual_status', 'unreviewed'))
        if state == 'incorrect':
            continue
        verified_view = review.get('verified_view')
        view = verified_view if state == 'verified' and verified_view in VIEWS else capture['view']
        key = (capture['app_slug'], view)
        candidate = {**capture, 'requested_view': capture['view'], 'view': view,
                     'review': review, 'review_status': state}
        current = candidates.get(key)
        if current is None or state == 'verified' or current['review_status'] != 'verified':
            candidates[key] = candidate
    rows = []
    for app in targets:
        for view in VIEWS:
            key = (app['slug'], view)
            capture = candidates.get(key)
            status = status_map.get(key) or status_map.get((app['slug'], 'all'))
            item = {'app_slug': app['slug'], 'title': app['title'], 'view': view,
                    'status': 'not-observed', 'note': ui['not_documented'], 'capture': None}
            if status:
                item.update({'status': status['status'], 'note': status.get('note', '')})
            if capture:
                path = safe_file(root, capture['file'])
                item['capture'] = capture
                item['path'] = path
                if not path.is_file():
                    item.update({'status': 'missing-file', 'note': ui['missing_file']})
                elif capture['review_status'] == 'verified':
                    item.update({'status': 'verified', 'note': capture['review'].get('note') or capture.get('note', '')})
                elif not status:
                    item.update({'status': capture['review_status'], 'note': capture['review'].get('note') or capture.get('note', '') or
                                 ui['awaiting_review']})
            rows.append(item)
    return rows


def escaped(value):
    return html.escape(str(value), quote=True)


def relative_file(path, base):
    return Path(os.path.relpath(path, base)).as_posix()


def build(input_dir, output_dir, apps_path=None, notes_path=None, embed=True, language='en'):
    ui = locale(language)
    labels = ui['labels']
    status_label = lambda status: ui['statuses'].get(status, status)
    root, out = Path(input_dir).resolve(), Path(output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    app_docs = out / 'apps'; app_docs.mkdir(exist_ok=True)
    captures = read_jsonl(root / 'manifest.jsonl')
    reviews = read_jsonl(root / 'reviews.jsonl')
    statuses = read_jsonl(root / 'statuses.jsonl')
    targets = read_targets(Path(apps_path) if apps_path else None, captures)
    notes_file = Path(notes_path) if notes_path else root / 'app-notes.json'
    notes = json.loads(notes_file.read_text(encoding='utf-8')) if notes_file.is_file() else {}
    rows = select_rows(root, targets, captures, reviews, statuses, language)
    generated = dt.datetime.now(ZoneInfo('Europe/Warsaw')).isoformat(timespec='seconds')
    verified = sum(row['status'] == 'verified' for row in rows)
    captured = sum(row.get('path') is not None and row['path'].is_file() for row in rows)
    title, intro = ui['title'], ui['intro']
    counts = ui['counts'].format(apps=len(targets), verified=verified, captured=captured, requested=len(rows))
    css = '''body{font:16px/1.5 system-ui,sans-serif;background:#111827;color:#edf2f7;margin:0}main{max-width:1500px;margin:auto;padding:32px}a{color:#93c5fd}h1{font-size:2rem}h2{margin-top:48px;border-top:1px solid #475569;padding-top:24px}.summary,.card{background:#1f2937;border:1px solid #475569;border-radius:10px;padding:18px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:16px}.card img{width:100%;height:auto;border-radius:6px;background:#000}.badge{display:inline-block;font-size:.8rem;border:1px solid #94a3b8;padding:2px 8px;border-radius:12px}.verified{color:#86efac;border-color:#16a34a}.unreviewed,.blocked,.login-required{color:#fde68a;border-color:#d97706}.muted{color:#cbd5e1;font-size:.85rem}nav{display:flex;flex-wrap:wrap;gap:8px 18px;margin:24px 0}figure{margin:0}code{overflow-wrap:anywhere}@media(max-width:500px){main{padding:16px}.grid{grid-template-columns:1fr}}'''
    html_parts = ['<!doctype html><html lang="' + language + '"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">',
                  '<title>' + escaped(title) + '</title><style>' + css + '</style><main>', '<h1>' + escaped(title) + '</h1>',
                  '<div class="summary"><p>' + escaped(intro) + '</p><p><strong>' + escaped(counts) + '</strong></p><p class="muted">' + ui['generated'] + ' ' + escaped(generated) + '</p></div>',
                  '<nav>' + ''.join('<a href="#' + escaped(app['slug']) + '">' + escaped(app['title']) + '</a>' for app in targets) + '</nav>']
    index = ['# ' + title, '', intro, '', ui['generated'] + ': ' + generated, '', counts, '',
             '| ' + ui['application'] + ' | ' + ' | '.join(labels[view] for view in VIEWS) + ' |',
             '| --- | --- | --- | --- | --- | --- | --- |']
    for app in targets:
        app_rows = [row for row in rows if row['app_slug'] == app['slug']]
        note = notes.get(app['slug'], {})
        html_parts.append('<section id="' + escaped(app['slug']) + '"><h2>' + escaped(app['title']) + '</h2>')
        app_id = app.get('app_id') or next((row['capture'].get('app_id') for row in app_rows if row['capture']), None)
        app_text = ['# ' + app['title'], '', ui['app_id'] + ': `' + str(app_id or ui['unresolved']) + '`', '']
        if app_id:
            html_parts.append('<p class="muted">' + ui['app_id'] + ': <code>' + escaped(app_id) + '</code></p>')
        if note.get('summary'):
            html_parts.append('<p>' + escaped(note['summary']) + '</p>')
            app_text.extend([note['summary'], ''])
        for field, label in (('observations', ui['observations']), ('limitations', ui['limitations'])):
            if note.get(field):
                html_parts.append('<h3>' + label + '</h3><ul>' + ''.join('<li>' + escaped(x) + '</li>' for x in note[field]) + '</ul>')
                app_text.extend(['## ' + label, ''] + ['- ' + str(x) for x in note[field]] + [''])
        html_parts.append('<div class="grid">')
        for row in app_rows:
            capture = row['capture']
            html_parts.append('<article class="card"><h3>' + labels[row['view']] + '</h3><p><span class="badge ' + escaped(row['status']) + '">' + escaped(status_label(row['status'])) + '</span></p>')
            app_text.extend(['## ' + labels[row['view']], '', '**Status:** ' + status_label(row['status']), ''])
            path = row.get('path')
            if path and path.is_file():
                if embed:
                    mime = 'image/png' if path.suffix.lower() == '.png' else 'image/jpeg'
                    source = 'data:' + mime + ';base64,' + base64.b64encode(path.read_bytes()).decode('ascii')
                else:
                    source = relative_file(path, out)
                alt = app['title'] + ': ' + labels[row['view']] + ' (' + status_label(row['status']) + ')'
                html_parts.append('<figure><img loading="lazy" src="' + escaped(source) + '" alt="' + escaped(alt) + '"></figure>')
                app_text.extend(['![' + alt.replace(']', '') + '](' + relative_file(path, app_docs) + ')', ''])
            if row['note']:
                html_parts.append('<p>' + escaped(row['note']) + '</p>')
                app_text.extend([row['note'], ''])
            if capture:
                evidence = (str(capture.get('time', '')) + '; ' + str(capture.get('width', '?')) + ' x ' + str(capture.get('height', '?')) +
                            '; foreground=' + str(capture.get('app_id', 'unknown')) + '; capture=' + str(capture.get('capture_id', '')))
                if capture.get('requested_view') != capture.get('view'):
                    evidence += '; requested_view=' + capture['requested_view'] + '; verified_view=' + capture['view']
                html_parts.append('<p class="muted">' + escaped(evidence) + '</p>')
                app_text.extend([ui['evidence'] + ': `' + evidence + '`', '', 'SHA-256: `' + str(capture.get('sha256', '')) + '`', ''])
            html_parts.append('</article>')
        html_parts.append('</div></section>')
        (app_docs / (app['slug'] + '.md')).write_text('\n'.join(app_text), encoding='utf-8')
        index.append('| [' + app['title'] + '](apps/' + app['slug'] + '.md) | ' + ' | '.join(status_label(row['status']) for row in app_rows) + ' |')
    html_parts.append('</main></html>')
    (out / 'index.html').write_text('\n'.join(html_parts), encoding='utf-8')
    (out / 'index.md').write_text('\n'.join(index) + '\n', encoding='utf-8')
    with (out / 'coverage.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(('app_slug', 'title', 'view', 'status', 'image_file', 'capture_time', 'foreground_app', 'note'))
        for row in rows:
            cap = row['capture'] or {}
            writer.writerow((row['app_slug'], row['title'], row['view'], row['status'], cap.get('file', ''), cap.get('time', ''), cap.get('app_id', ''), row['note']))
    summary = {'generated_at': generated, 'applications': len(targets), 'requested_views': len(rows), 'verified_views': verified,
               'image_backed_rows': captured, 'html': str(out / 'index.html'), 'markdown': str(out / 'index.md'),
               'app_documents': str(app_docs), 'coverage': str(out / 'coverage.csv'), 'embedded_images': embed, 'language': language}
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--apps', default=str(Path(__file__).with_name('targets.json')))
    parser.add_argument('--notes')
    parser.add_argument('--language', choices=('en', 'pl'), default='en', help='Static report labels; provide --notes in the chosen language')
    parser.add_argument('--linked-images', action='store_true', help='Use relative image paths instead of a standalone embedded HTML file')
    args = parser.parse_args()
    print(json.dumps(build(args.input, args.output, args.apps, args.notes, not args.linked_images, args.language), ensure_ascii=False))
