#!/usr/bin/env python3
"""Release 1.2.12: compare public Homebrew catalog version with locally installed version."""
from pathlib import Path
import json, shutil
R=Path(__file__).resolve().parents[1]
APP=R/'build/dc4i-vodtv'
VERSION='1.2.12'

meta=APP/'appinfo.json'
d=json.loads(meta.read_text(encoding='utf-8'))
assert d.get('id')=='com.dc4i.vodtv'
assert d.get('version')=='1.2.11',d.get('version')
d['version']=VERSION
meta.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

markup=APP/'index.html'
s=markup.read_text(encoding='utf-8')
old_badge='<span class="dc4i-build-badge">v1.2.11</span>'
assert s.count(old_badge)==1
s=s.replace(old_badge,'<span id="dc4i-build-badge" class="dc4i-build-badge">Sprawdzanie...</span>')
assert s.count('1.2.11 · 25.10.2026')==1
s=s.replace('1.2.11 · 25.10.2026',VERSION+' · 25.10.2026')
script_tag='<script src="vod-version-check.js"></script>\n'
assert s.count('<script src="app.js"></script>')==1
s=s.replace('<script src="app.js"></script>', script_tag+'<script src="app.js"></script>')
markup.write_text(s,encoding='utf-8')

source=(R/'src/vod-version-check.js').read_text(encoding='utf-8')
assert source.count('__DC4I_CURRENT_VERSION__')==1
(APP/'vod-version-check.js').write_text(source.replace('__DC4I_CURRENT_VERSION__',VERSION),encoding='utf-8')

app=APP/'app.js'
t=app.read_text(encoding='utf-8')
start=t.index('  function refreshLatestQuick() {')
end=t.index('  function refreshQuick() {',start)
new='''  function refreshLatestQuick() {
    if (window.DC4IVersions) {
      return window.DC4IVersions.refresh({
        currentVersion: '1.2.12',
        latestElement: $('dc4i-latest-version'),
        statusElement: $('dc4i-build-badge')
      });
    }
    $('dc4i-latest-version').textContent='Moduł aktualizacji niedostępny';
  }
'''
t=t[:start]+new+t[end:]
assert t.count('refreshLatestQuick();')==1
app.write_text(t,encoding='utf-8')

css=APP/'dc4i.css'
style=css.read_text(encoding='utf-8')
style+='''
/* Freshness states from the public Homebrew repository. */
#quick #dc4i-build-badge {font-size:18px;white-space:nowrap;max-width:300px;}
#quick #dc4i-build-badge[data-state="current"] {border-color:rgba(127,224,192,.55);color:#9cf5cb;}
#quick #dc4i-build-badge[data-state="update"] {border-color:rgba(255,208,123,.7);color:#ffdd97;}
#quick #dc4i-build-badge[data-state="ahead"] {border-color:rgba(176,196,240,.45);color:#c1d6ff;}
#quick #dc4i-build-badge[data-state="offline"],
#quick #dc4i-build-badge[data-state="unknown"] {color:#d1d7e4;}
'''
css.write_text(style,encoding='utf-8')
print('VERSION_PATCH_READY',VERSION,'Homebrew manifest dynamic check')
