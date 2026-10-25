#!/usr/bin/env python3
"""Check real build structure/branding separately from credentials and IPK release gates."""
import argparse
import json
from pathlib import Path
import subprocess
from PIL import Image, ImageChops

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('fixture_root', type=Path)
args = parser.parse_args()
root = args.fixture_root.resolve()
assert (root / 'OFFLINE_FIXTURE_ONLY.txt').is_file(), 'Not an offline fixture'
app = root / 'build/dc4i-vodtv'
metadata = json.loads((app / 'appinfo.json').read_text())
assert metadata['id'] == 'com.dc4i.vodtv.offlinefixture'
assert metadata['version'] == '1.2.19'
assert metadata['title'] == 'DC4I VOD TV OFFLINE FIXTURE'
for name, size in [('icon.png', (80, 80)), ('largeIcon.png', (130, 130)), ('splash.png', (1920, 1080))]:
    assert Image.open(app / name).size == size, name
official = Image.open(root / 'assets/brand/DC4I_VOD_TV_Neon_Approved_2026-10-24.png').convert('RGB')
actual = Image.open(app / 'icon.png').convert('RGB')
assert ImageChops.difference(official.resize((80, 80), Image.Resampling.LANCZOS), actual).getbbox() is None
html = (app / 'index.html').read_text()
assert html.index('keys.js') < html.index('config.js') < html.index('app.js')
assert html.index('vod-xtream.js') < html.index('vod-channel-guide.js')
from html.parser import HTMLParser
class Styles(HTMLParser):
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs)
        if tag=='link' and attrs.get('rel')=='stylesheet':
            assert 'onload' not in attrs
            assert attrs.get('media','all')=='all'
Styles().feed(html)
keys = (app / 'keys.js').read_text()
assert "TMDB_KEY: '', YT_KEY: ''" in keys and 'OFFLINE REGRESSION FIXTURE ONLY' in keys
assert 'Offline fixture: network disabled' in keys
assert "typeof PalmSystem !== 'undefined'" in keys
assert html.index('Content-Security-Policy') < html.index('src="keys.js"')
assert "connect-src 'none'" in html and "default-src 'none'" in html
assert 'script-src \'nonce-' in html
assert json.loads((root / 'fixture-provenance.json').read_text())['inputPolicy'] == 'committed-tree-only'
paths = sorted(app.rglob('*.js'))
for path in paths:
    subprocess.run(['node', '--check', str(path)], check=True, capture_output=True)
assert 'dc4iXtreamPlaylistsV1' in (app / 'vod-xtream.js').read_text()
assert '192.168.1.11' not in (app / 'vod-xtream.js').read_text()
print('OFFLINE_BUILD_STRUCTURE_BRANDING_SYNTAX_PASS', len(paths), 'JS files; no API or package verification')
