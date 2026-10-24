#!/usr/bin/env python3
"""Add verified official Kodi webOS package to DC4I Homebrew catalog.

Do not upload the 92 MB binary to Cloudflare Pages (per-file asset limit).
The catalog links to the official Kodi distribution mirror, with checksum.
"""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parent.parent
pkg=ROOT/'private/external-packages/org.xbmc.kodi-webos_21.0.ipk'
assert pkg.is_file()
sha=hashlib.sha256(pkg.read_bytes()).hexdigest()
assert sha=='b8ac326df8ad7cf0b52e4f816ab7c39c95410254b1bc3b9b3d024035ecec58ff'
base='https://lg.darc.dev'
icon=base+'/icons/kodi-icon.png'
manifest={
 'id':'org.xbmc.kodi','version':'21.0.0','type':'native','title':'Kodi',
 'appDescription':'Oficjalne Kodi 21.0 Omega dla LG webOS. Bez root, webOS 4+ (z wyjątkiem K5LP).',
 'iconUri':icon,'sourceUrl':'https://kodi.tv/download/webos/',
 'rootRequired':False,
 'ipkUrl':'https://mirrors.kodi.tv/releases/webos/org.xbmc.kodi-webos_21.0.ipk?https=1',
 'ipkHash':{'sha256':sha},'ipkSize':pkg.stat().st_size
}
entry={
 'id':'org.xbmc.kodi','title':'Kodi','iconUri':icon,'manifest':manifest,
 'shortDescription':'Kodi 21.0 Omega | Oficjalny pakiet webOS | Native',
 'fullDescriptionUrl':'https://kodi.wiki/view/HOW-TO:Install_Kodi_for_webOS'
}
dist=ROOT/'dist'
for directory in (ROOT,dist):
 p=directory/'api/apps.json'
 feed=json.loads(p.read_text())
 packages=[x for x in feed['packages'] if x['id']!='org.xbmc.kodi']
 packages.append(entry)
 feed['packages']=packages
 feed['paging']['count']=len(packages)
 feed['paging']['itemsTotal']=len(packages)
 encoded=json.dumps(feed,ensure_ascii=False,indent=2)+'\n'
 for target in [directory/'api/apps.json',directory/'apps.json',directory/'index.html']:
  target.write_text(encoded)
 (directory/'packages.json').write_text(json.dumps(packages,ensure_ascii=False,indent=2)+'\n')
 (directory/'icons').mkdir(exist_ok=True)
 if directory != ROOT: shutil.copy2(ROOT/'icons/kodi-icon.png',directory/'icons/kodi-icon.png')
 (directory/'manifests').mkdir(exist_ok=True)
 (directory/'manifests/kodi.manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('KODI_ADDED',manifest['version'],'CATALOG_COUNT',len(packages),'SIZE',manifest['ipkSize'],'SHA256',sha)
