#!/usr/bin/env python3
"""Publish compatible Homebrew Channel catalog for DC4I VOD TV.
Public .ipk contains a bundled TMDB client key. No key values written to git-tracked source files.
"""
from pathlib import Path
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parent
APP='com.dc4i.boringtv'
VERSION='1.1.1'
BASE='https://lg.darc.dev'
IPK=ROOT/'private'/f'{APP}_{VERSION}_all.ipk'
assert IPK.exists(), 'Build the IPK before publishing'
size=IPK.stat().st_size
sha=hashlib.sha256(IPK.read_bytes()).hexdigest()
icon_uri=BASE+'/icons/dc4i-vod-tv.png'
package_uri=BASE+'/packages/'+IPK.name
manifest={
 'id':APP,'version':VERSION,'type':'web','title':'DC4I VOD TV',
 'appDescription':'Spersonalizowany katalog filmów i seriali dla Polski, z ocenami TMDB, nowościami VOD i łatwym otwieraniem aplikacji streamingowych.',
 'iconUri':icon_uri,
 'sourceUrl':'https://github.com/darekcze/dc4i-vod-tv',
 'rootRequired':False,
 'ipkUrl':package_uri,
 'ipkHash':{'sha256':sha},
 'ipkSize':size
}
entry={
 'id':APP,
 'title':'DC4I VOD TV',
 'iconUri':icon_uri,
 'manifest':manifest,
 'shortDescription':'Filmy, seriale i oceny w jednym miejscu | Polska | TMDB skonfigurowane',
 'fullDescriptionUrl':BASE+'/about.html'
}
# Merge the verified DC4I VOD TV update without deleting DStore or other existing catalogue entries.
previous=json.loads((ROOT/'api/apps.json').read_text(encoding='utf8')) if (ROOT/'api/apps.json').exists() else {}
extras=[x for x in previous.get('packages',[]) if x.get('id')!=APP]
package_list=[entry]+extras
catalog={'paging':{'page':1,'count':len(package_list),'maxPage':1,'itemsTotal':len(package_list)}, 'packages':package_list}
formatted=json.dumps(catalog,ensure_ascii=False,indent=2)+'\n'
formatted_manifest=json.dumps(manifest,ensure_ascii=False,indent=2)+'\n'
DIST=ROOT/'dist'
for folder in ['api','icons','packages','manifests']:
 (DIST/folder).mkdir(parents=True,exist_ok=True)
for old_package in (DIST/'packages').glob('*.ipk'):
 if old_package.name.startswith(APP+'_') and old_package.name not in (IPK.name, 'com.dc4i.boringtv_1.1.0_all.ipk'): old_package.unlink()
for p in [ROOT/'index.html', ROOT/'apps.json', ROOT/'api/apps.json',DIST/'index.html',DIST/'apps.json',DIST/'api/apps.json']:
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(formatted,encoding='utf-8')
for p in [ROOT/'manifests/dc4i-boringtv.manifest.json',DIST/'manifests/dc4i-boringtv.manifest.json']:
 p.write_text(formatted_manifest,encoding='utf-8')
for p in [ROOT/'packages.json',DIST/'packages.json']:
 p.write_text(json.dumps([entry],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for p in [ROOT/'icons/dc4i-vod-tv.png',DIST/'icons/dc4i-vod-tv.png']:
 shutil.copy2(ROOT/'assets/brand/dc4i-vod-tv-icon-1024.png',p)
shutil.copy2(IPK, DIST/'packages'/IPK.name)
# An attractive human-readable landing page lives separately from the machine-readable catalog.
html='''<!DOCTYPE html>
<html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>DC4I VOD TV | LG webOS</title>
<style>
:root{color-scheme:dark}*{box-sizing:border-box}body{font:16px/1.65 system-ui,-apple-system,Arial;background:radial-gradient(ellipse at 85% 12%,#1b326d 0%,transparent 48%),linear-gradient(140deg,#071638,#030917 85%);color:#e9f3ff;margin:0;min-height:100vh}
header,main,footer{max-width:1020px;margin:auto;padding:25px}header{display:flex;align-items:center;gap:20px;padding-top:35px}
header strong{font-size:16px;letter-spacing:3px;color:#b4f34c}h1{font-size:clamp(32px,7vw,66px);line-height:1.04;letter-spacing:-2px;margin:25px 0}h2{font-size:25px}p{color:#bdcfe8}b{color:white}
.hero{padding:35px 0 55px;display:grid;grid-template-columns:210px 1fr;align-items:center;gap:40px}
.hero img{width:100%;border-radius:34px;box-shadow:0 30px 80px #0007}a{color:#b4f34c}
.btn{display:inline-block;background:#b4f34c;color:#071638;font-weight:750;border-radius:12px;padding:14px 22px;text-decoration:none}
code{display:block;padding:16px 20px;background:#101f40;border:1px solid #334d7f;border-radius:12px;overflow-wrap:anywhere;color:#e7f0ff}
.tags{display:flex;gap:9px;flex-wrap:wrap}.tags span{background:#193766;border-radius:999px;padding:5px 13px;font-size:13px;color:#d0e6ff}
.card{padding:30px;border:1px solid #2b4272;border-radius:20px;background:#091933d9;margin:22px 0}
footer{font-size:12px;color:#8ea1bd;padding-bottom:35px}
@media(max-width:650px){.hero{grid-template-columns:1fr;text-align:center}.hero img{max-width:210px;margin:auto}header{padding-top:18px}}
</style></head><body>
<header><strong>DC4I</strong><span>DRIVING COMPANIES FOR AI</span></header>
<main><section class="hero"><img src="/icons/dc4i-vod-tv.png" alt="DC4I VOD TV">
<div><div class="tags"><span>LG webOS</span><span>Polska</span><span>TMDB gotowe</span></div>
<h1>DC4I<br>VOD TV</h1>
<p>Twoje centrum filmów, seriali i ocen. Odkrywaj nowości VOD i przechodź do aplikacji streamingowych bez szukania po wielu katalogach.</p>
<a class="btn" href="/packages/com.dc4i.boringtv_1.1.1_all.ipk">Pobierz aplikację .IPK</a></div></section>
<div class="card"><h2>Instalacja w Homebrew Channel</h2>
<p>Wejdź w Settings, Repositories, Add Repository i dodaj poniższy adres:</p>
<code>https://lg.darc.dev/</code>
<p>Repozytorium wyświetli <b>DC4I VOD TV</b>. Wybierz Install. Nie trzeba wpisywać TMDB Key na telewizorze.</p>
<p>Jeśli już masz oryginalne TheBoringTV, nowe DC4I VOD TV instaluje się jako osobna aplikacja.</p></div>
<div class="card"><h2>Co działa?</h2>
<p>Filmowe rekomendacje TMDB, polski region, personalizacja DC4I, ulubione, wyszukiwanie i otwieranie serwisów VOD. YouTube Trending jest ukryte do chwili skonfigurowania osobnego klucza YouTube Data API v3.</p>
<p>Niektóre przyciski otwierania bezpośrednio konkretnego filmu zależą od obsługi przez daną aplikację i wersji systemu webOS.</p>
</div></main><footer>DC4I VOD TV jest spersonalizowanym wariantem społecznościowej aplikacji TheBoringTV. Źródło: <a href="https://github.com/theboringhumane/theboringtv-lgwebos">theboringhumane/theboringtv-lgwebos</a>. Informacje o filmach: TMDB (projekt nie jest z nim powiązany).</footer></body></html>'''
(DIST/'about.html').write_text(html,encoding='utf-8')
(ROOT/'about.html').write_text(html,encoding='utf-8')
(DIST/'_headers').write_text('/\n  Content-Type: application/json; charset=utf-8\n/index.html\n  Content-Type: application/json; charset=utf-8\n/api/apps.json\n  Content-Type: application/json; charset=utf-8\n',encoding='utf-8')
README='''# DC4I LG webOS Homebrew Repository

Canonical TV repository: https://lg.darc.dev/

Homebrew Channel expects JSON at the root URL. A browser-friendly project page is at https://lg.darc.dev/about.html.

## DC4I VOD TV 1.1.1

- Identifier: com.dc4i.boringtv (installs alongside original)
- Market: Poland (PL), interface: Polish-first
- Artwork: the official DC4I transparent company logo
- TMDB v3: bundled and tested, no TV setup
- YouTube Trending: disabled until Google YouTube Data API v3 credentials become available
- Package (Cloudflare Pages): '''+package_uri+'''
- SHA256: '''+sha+'''

Package and catalog are deployed on Cloudflare Pages. The binary is intentionally **not committed to GitHub** as it embeds a client-side TMDB key. Anyone downloading the public IPK can extract that client key, so usage must be monitored and the key rotated if misused.

This personalized build is derived from the upstream project [theboringhumane/theboringtv-lgwebos](https://github.com/theboringhumane/theboringtv-lgwebos). It is not endorsed by LG or TMDB.

Reproducible local preparation scripts: build_dc4i.py (base), build_vod_tv.py (branding and PL/EN), test_vod_tv.py, publish_vod_tv.py. They read a privately stored keys.js and do not write secrets to git-tracked plaintext files.

To release changes, build the app IPK, run test_vod_tv.py, run publish_vod_tv.py, and deploy dist via Cloudflare Pages. Test Homebrew and app startup on a real LG webOS TV before claiming end-to-end compatibility.
'''
(ROOT/'README.md').write_text(README,encoding='utf-8')
print('HOMEBREW_CATALOG_READY',entry['id'],entry['manifest']['version'],len(catalog['packages']))
print('IPK_PUBLISHED_FILE',str(DIST/'packages'/IPK.name))
print('IPK_HASH',sha,'BYTES',size)


# DC4I_DSTORE_CATALOG_HOOK: do not overwrite the multi-app catalog on the next VOD release.
if (ROOT/'data/dstore-verified.json').exists():
 import subprocess,sys,os
 # Rebuild the third-party catalog ONLY on a deliberate DStore refresh, not every VOD release.
 if os.environ.get('DC4I_REFRESH_DSTORE') == '1':
  for stage in ['mirror_dstore.py','build_catalog.py','test_catalog.py']:
   subprocess.run([sys.executable,str(ROOT/'scripts'/stage)],check=True)
 with (ROOT/'README.md').open('a',encoding='utf-8') as notes:
  notes.write('\n## Multiplatform webOS repository\n\n- Browser interface: https://lg.darc.dev/browse/\n- Homebrew Channel feed: https://lg.darc.dev/ (JSON for TVs) or https://lg.darc.dev/api/apps.json\n- DStore import and operational details: docs/DSTORE-CATALOG.md\n')
with (ROOT/'README.md').open('a',encoding='utf-8') as notes:
 notes.write('\n## Version history and known issues\n\n- [Changelog](CHANGELOG.md) and [Polish changelog](docs/pl/CHANGELOG.md)\n- [Delivery evidence](DELIVERY.md) and [Project charter](PROJECT.md)\n- Stremio and IPTV Smarters handoff needs real LG TV validation.\n')
