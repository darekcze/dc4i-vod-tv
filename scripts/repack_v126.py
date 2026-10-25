#!/usr/bin/env python3
"""Repack an owner-authorized webOS 1.2.5 IPK into 1.2.6, preserving the approved binary assets."""
from pathlib import Path
import subprocess,tarfile,io,json,os,hashlib,shutil,tempfile
R=Path(__file__).resolve().parents[1]
BASE=R/'private/com.dc4i.vodtv_1.2.15_all.ipk'
DEST=R/'private/com.dc4i.vodtv_1.2.16_all.ipk'
SRC=R/'build/dc4i-vodtv'
assert BASE.exists() and json.loads((SRC/'appinfo.json').read_text())['version']=='1.2.16'
def read_ar(entry):return subprocess.check_output(['ar','p',str(BASE),entry])
control=read_ar('control.tar.gz');data=read_ar('data.tar.gz')
def make_tar(original,overlay):
 inp=tarfile.open(fileobj=io.BytesIO(original),mode='r:gz')
 out=io.BytesIO()
 with tarfile.open(fileobj=out,mode='w:gz') as tf:
  present=set()
  for member in inp.getmembers():
   name=member.name
   if not member.isfile():tf.addfile(member);continue
   source=inp.extractfile(member).read()
   if name in overlay:source=overlay[name];present.add(name)
   member.size=len(source)
   tf.addfile(member,io.BytesIO(source))
  for name,content in overlay.items():
   if name in present:continue
   item=tarfile.TarInfo(name);item.size=len(content);item.mode=0o644;item.uid=0;item.gid=0
   tf.addfile(item,io.BytesIO(content))
 inp.close()
 return out.getvalue()
app='usr/palm/applications/com.dc4i.vodtv/'
new_files=['appinfo.json','index.html','features/details.js','vod-handoff.js','DC4I-FORK-NOTES.md','app.js','dc4i.css','vod-version-check.js','vod-external-search.js','vod-external-search.css','features/search.js','vod-xtream.js','vod-xtream.css']
replace={app+f:(SRC/f).read_bytes() for f in new_files}
old_pkg='usr/palm/packages/com.dc4i.vodtv/packageinfo.json'
with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as tf:
 meta=json.load(tf.extractfile(old_pkg))
meta['version']='1.2.16'
replace[old_pkg]=(json.dumps(meta,ensure_ascii=False,indent=2)+'\n').encode()
new_data=make_tar(data,replace)
with tarfile.open(fileobj=io.BytesIO(control),mode='r:gz') as tf:
 cm=tf.extractfile('control').read().decode()
assert 'Version: 1.2.15' in cm
cm=cm.replace('Version: 1.2.15','Version: 1.2.16',1)
new_control=make_tar(control,{'control':cm.encode()})
# Write the System V ar container directly: Apple ar only accepts object libraries.
parts=[('debian-binary',read_ar('debian-binary')),('control.tar.gz',new_control),('data.tar.gz',new_data)]
with open(DEST,'wb') as out:
 out.write(b'!<arch>\n')
 for name,blob in parts:
  header=(f'{name:<16}{0:<12}{0:<6}{0:<6}{100644:<8}{len(blob):<10}`\n').encode('ascii')
  assert len(header)==60
  out.write(header);out.write(blob)
  if len(blob)%2:out.write(b'\n')
assert DEST.exists()
with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['ar','p',str(DEST),'data.tar.gz'])),mode='r:gz') as tf:
 d=json.load(tf.extractfile(app+'appinfo.json'))
 js=tf.extractfile(app+'vod-handoff.js').read()
 html=tf.extractfile(app+'index.html').read()
 details=tf.extractfile(app+'features/details.js').read()
 assert d['version']=='1.2.16'
 assert b'vod-handoff.js' in html and b'vod-external-search.js' in html
 assert b'vodExternalSearch.render' in details
 search=tf.extractfile(app+'features/search.js').read()
 assert b'vodExternalSearch.render' in search and b'Brak w wybranych serwisach' in search
 assert b'params:{dc4i:payload}' in js
print('REPACK_OK',DEST.name,'BYTES',DEST.stat().st_size,'SHA256',hashlib.sha256(DEST.read_bytes()).hexdigest())
