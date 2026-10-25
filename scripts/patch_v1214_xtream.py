#!/usr/bin/env python3
"""Add self-contained Xtream playlist management to v1.2.13 webOS build."""
from pathlib import Path
import json, shutil
R=Path(__file__).resolve().parents[1]
A=R/'build/dc4i-vodtv'
VERSION='1.2.14'
for name in ('vod-xtream.js','vod-xtream.css'):
    shutil.copy2(R/'src'/name,A/name)
html=A/'index.html'
text=html.read_text(encoding='utf-8')
assert '<script src="features/search.js"></script>' in text
assert '<link rel="stylesheet" href="vod-external-search.css">' in text
text=text.replace('<script src="features/search.js"></script>','<script src="features/search.js"></script>\n<script src="vod-xtream.js"></script>')
text=text.replace('<link rel="stylesheet" href="vod-external-search.css">','<link rel="stylesheet" href="vod-external-search.css">\n<link rel="stylesheet" href="vod-xtream.css">')
assert '1.2.13 · 25.10.2026' in text
text=text.replace('1.2.13 · 25.10.2026','1.2.14 · 25.10.2026')
html.write_text(text,encoding='utf-8')
meta=A/'appinfo.json'
info=json.loads(meta.read_text())
assert info['id']=='com.dc4i.vodtv' and info['version']=='1.2.13',info
info['version']=VERSION
meta.write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n')
app=A/'app.js';s=app.read_text()
assert "currentVersion: '1.2.13'" in s
app.write_text(s.replace("currentVersion: '1.2.13'","currentVersion: '1.2.14'"))
v=A/'vod-version-check.js';s=v.read_text()
assert "var CURRENT_VERSION = '1.2.13';" in s
v.write_text(s.replace("var CURRENT_VERSION = '1.2.13';","var CURRENT_VERSION = '1.2.14';"))
assert 'vod-xtream.js' in html.read_text() and 'vod-xtream.css' in html.read_text()
print('XTREAM_V1214_PATCH_OK', VERSION)
