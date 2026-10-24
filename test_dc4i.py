#!/usr/bin/env python3
"""Smoke tests for DC4I BoringTV. Never prints credentials."""
from pathlib import Path
from PIL import Image
import json,re,subprocess,tarfile,io,urllib.request,urllib.error,hashlib
R=Path(__file__).resolve().parent
A=R/'build'/'dc4i-boringtv'
P=R/'private'/'com.dc4i.boringtv_1.0.1_all.ipk'
meta=json.loads((A/'appinfo.json').read_text())
assert meta['id']=='com.dc4i.boringtv'
assert meta['title']=='DC4I BoringTV'
assert meta['version']=='1.0.1'
assert Image.open(A/'icon.png').size==(80,80)
assert Image.open(A/'largeIcon.png').size==(130,130)
assert Image.open(A/'splash.png').size==(1920,1080)
html=(A/'index.html').read_text()
assert 'dc4i.css' in html and 'dc4i-wordmark.png' in html
assert html.index('keys.js')<html.index('config.js')<html.index('app.js')
js=(A/'app.js').read_text()
assert "if (!C.YT_KEY) S.youtube = false;" in js
assert "if (!C.YT_KEY) return Promise.resolve(null);" in js
config=(A/'config.js').read_text()
assert "REGION: 'PL'" in config and "LANG: 'pl-PL'" in config
km=re.search(r'[a-f0-9]{32}',(A/'keys.js').read_text(),re.I)
assert km,'TMDB is not configured'
print('METADATA_AND_BRANDING_OK')
for f in ['app.js','config.js']:
  p=subprocess.run(['node','--check',str(A/f)],capture_output=True,text=True)
  assert p.returncode==0,p.stderr
print('JAVASCRIPT_SYNTAX_OK')
data=subprocess.check_output(['ar','p',str(P),'data.tar.gz'])
with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as tf:
  names=[x.name for x in tf.getmembers()]
  for f in ['keys.js','appinfo.json','splash.png','dc4i.css','dc4i-wordmark.png']:
    assert any(n.endswith('/'+f) or n==f for n in names),f+' not in IPK'
print('IPK_CONTENTS_OK',len(names),'files')
try:
  u='https://api.themoviedb.org/3/configuration?api_key='+km.group(0)
  with urllib.request.urlopen(u,timeout=15) as response:
    obj=json.load(response);assert response.status==200 and 'images' in obj
  print('TMDB_API_OK HTTP_200')
except Exception as e:
  print('TMDB_API_UNVERIFIED',str(e)[:150])
print('PACKAGE_SIZE',P.stat().st_size,'SHA256',hashlib.sha256(P.read_bytes()).hexdigest())
