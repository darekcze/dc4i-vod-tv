#!/usr/bin/env python3
"""Final 1.2.15 metadata/TV remote navigation correction after the 1.2.14 layer."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
A=R/'build/dc4i-vodtv'
meta=A/'appinfo.json';o=json.loads(meta.read_text());assert o['version']=='1.2.14'
o['version']='1.2.15';meta.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
substitutions={'index.html':('1.2.14 · 25.10.2026','1.2.15 · 25.10.2026'),
'app.js':("currentVersion: '1.2.14'","currentVersion: '1.2.15'"),
'vod-version-check.js':("var CURRENT_VERSION = '1.2.14';","var CURRENT_VERSION = '1.2.15';")}
for file,(old,new) in substitutions.items():
 p=A/file;s=p.read_text();assert old in s,file;p.write_text(s.replace(old,new))
assert "$('name'),$('url')" in (A/'vod-xtream.js').read_text()
print('XTREAM_1215_TV_REMOTE_NAV_READY')
