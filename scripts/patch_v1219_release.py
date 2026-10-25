#!/usr/bin/env python3
"""Final 1.2.19 app metadata patch; all earlier minor-version updates are retained."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
A=R/'build/dc4i-vodtv'
APP='com.dc4i.vodtv'
def edit(file,before,after):
    p=A/file
    s=p.read_text(encoding='utf-8')
    assert s.count(before)==1,(file,'expected one version anchor',s.count(before))
    p.write_text(s.replace(before,after,1),encoding='utf-8')
meta=A/'appinfo.json'
d=json.loads(meta.read_text(encoding='utf-8'))
assert d['id']==APP and d['version']=='1.2.18',d
d['version']='1.2.19'
meta.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
edit('index.html','1.2.18 · 25.10.2026','1.2.19 · 25.10.2026')
edit('app.js',"currentVersion: '1.2.18'","currentVersion: '1.2.19'")
edit('vod-version-check.js',"var CURRENT_VERSION = '1.2.18';","var CURRENT_VERSION = '1.2.19';")
print('RELEASE_METADATA_READY',d['id'],d['version'])
