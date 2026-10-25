#!/usr/bin/env python3
"""Bounded LOCAL XMLTV-to-metadata import. No download, account or publish path.

Supported subset: complete second-resolution timestamps, numeric offsets or UTC
default per XMLTV DTD. Unknown ends/abbreviated times are skipped, not invented.
DOCTYPE/entity declarations are deliberately unsupported. No feed is licensed
or enabled by this utility; callers must establish their own data rights.
"""
import argparse
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

MAX_BYTES = 2_000_000
MAX_ROWS = 20_000
MAX_CHANNELS = 1_000

def timestamp(value):
    match = re.fullmatch(r'(\d{14})(?:\s+([+-]\d{4}|Z))?', value or '')
    if not match:
        raise ValueError('unsupported timestamp')
    offset = match[2] or 'Z'
    minutes = 0
    if offset != 'Z':
        hours, mins = int(offset[1:3]), int(offset[3:5])
        if hours > 23 or mins > 59:
            raise ValueError('invalid offset')
        minutes = (hours * 60 + mins) * (-1 if offset[0] == '-' else 1)
    parsed = datetime.strptime(match[1], '%Y%m%d%H%M%S')
    return int(parsed.replace(tzinfo=timezone(timedelta(minutes=minutes))).timestamp() * 1000)

def text(element, path, limit=500):
    node = element.find(path)
    return ' '.join(''.join(node.itertext()).split())[:limit] if node is not None else ''

def parse_xmltv(data, source, fetched_at):
    if not isinstance(data, bytes) or len(data) > MAX_BYTES:
        raise ValueError('XMLTV size limit')
    if not re.fullmatch(r'[a-zA-Z0-9_.-]{1,64}', source or ''):
        raise ValueError('source must be a non-secret identifier, not a URL')
    if isinstance(fetched_at, bool) or not isinstance(fetched_at, int) or fetched_at < 0:
        raise ValueError('invalid fetchedAt')
    # Decode before checking declarations so UTF-16 cannot bypass the guard.
    try:
        xml = data.decode('utf-8-sig')
        if '\x00' in xml or re.search(r'<!\s*(DOCTYPE|ENTITY)', xml, re.I):
            raise ValueError('XML declarations unsupported')
        parser = ET.XMLPullParser(events=('start', 'end'))
        depth, nodes, root = 0, 0, None
        for offset in range(0, len(xml), 4096):
            parser.feed(xml[offset:offset + 4096])
            for kind, node in parser.read_events():
                if kind == 'start':
                    if root is None:
                        root = node
                    depth += 1
                    nodes += 1
                    if depth > 16 or nodes > 200_000:
                        raise ValueError('XMLTV structure limit')
                else:
                    depth -= 1
        parser.close()
    except (UnicodeError, ET.ParseError) as exc:
        raise ValueError('invalid XMLTV document') from exc
    if root is None or root.tag != 'tv':
        raise ValueError('expected tv document')
    channels, conflicts = {}, set()
    channel_rows = root.findall('channel')
    programme_rows = root.findall('programme')
    if len(channel_rows) > MAX_CHANNELS or len(programme_rows) > MAX_ROWS:
        raise ValueError('XMLTV record limit')
    diagnostics = {'skipped': 0, 'duplicates': 0, 'conflictingChannels': 0}
    for row in channel_rows:
        identity = row.get('id', '')
        names = list(dict.fromkeys(' '.join(''.join(n.itertext()).split())[:200]
                                  for n in row.findall('display-name')))
        names = [n for n in names if n]
        if not identity or len(identity) > 200 or not names:
            diagnostics['skipped'] += 1
            continue
        channel = {'id': identity, 'names': names}
        if identity in channels and channels[identity] != channel:
            conflicts.add(identity)
        channels[identity] = channel
    for identity in conflicts:
        channels.pop(identity, None)
    diagnostics['conflictingChannels'] = len(conflicts)
    events, seen = [], set()
    for row in programme_rows:
        try:
            identity = row.get('channel', '')
            title = text(row, 'title')
            start, end = timestamp(row.get('start')), timestamp(row.get('stop'))
            if not identity or len(identity) > 200 or identity in conflicts or not title or end <= start:
                raise ValueError('invalid programme')
        except ValueError:
            diagnostics['skipped'] += 1
            continue
        # Whitelist fields; URLs, provider accounts and arbitrary attributes never copy.
        rating = row.find('star-rating')
        event = {'channelId': identity, 'title': title, 'start': start, 'end': end,
                 'description': text(row, 'desc', 2000), 'year': text(row, 'date', 8)[:4],
                 'categories': [text(n, '.', 100) for n in row.findall('category')][:20],
                 'originalLanguage': text(row, 'orig-language', 50),
                 'rating': {'value': text(rating, 'value', 50),
                            'system': rating.get('system', 'unspecified')[:100],
                            'verified': False} if rating is not None else None,
                 'tracks': {'audio': 'unknown', 'subtitles': 'unknown'},
                 'provenance': {'source': source, 'kind': 'xmltv', 'fetchedAt': fetched_at}}
        fingerprint = json.dumps(event, sort_keys=True, ensure_ascii=False)
        if fingerprint in seen:
            diagnostics['duplicates'] += 1
            continue
        seen.add(fingerprint)
        events.append(event)
    events.sort(key=lambda e: (e['start'], e['end'], e['channelId'], e['title']))
    return {'schemaVersion': 1, 'source': source, 'fetchedAt': fetched_at,
            'channels': sorted(channels.values(), key=lambda c: c['id']),
            'events': events, 'diagnostics': diagnostics}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--source', required=True)
    parser.add_argument('--fetched-at', type=int, required=True, help='UTC milliseconds')
    args = parser.parse_args()
    with args.input.open('rb') as stream:
        data = stream.read(MAX_BYTES + 1)
    print(json.dumps(parse_xmltv(data, args.source, args.fetched_at), ensure_ascii=False))

if __name__ == '__main__':
    main()
