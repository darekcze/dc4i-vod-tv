import json, hashlib
from pathlib import Path
from datetime import datetime, timezone
p=next(Path('packages').glob('com.boring.tvhome_*.ipk'))
version=p.name.split('_')[1]
sha=hashlib.sha256(p.read_bytes()).hexdigest()
base='https://lg-webos-repo.pages.dev'
manifest={'id':'com.boring.tvhome','version':version,'type':'web','title':'TheBoringTV (TV Home)','appDescription':'Google TV-style launcher for LG webOS. Requires your TMDB and YouTube API keys for recommendations. Root required only to replace the native LG home screen.','iconUri':f'{base}/icons/theboringtv.png','sourceUrl':'https://github.com/theboringhumane/theboringtv-lgwebos','rootRequired':False,'ipkUrl':f'{base}/packages/{p.name}','ipkHash':{'sha256':sha},'ipkSize':p.stat().st_size}
package={'id':f'com-boring-tvhome-{version.replace(".","-")}','title':'TheBoringTV','iconUri':manifest['iconUri'],'manifestUrl':f'{base}/manifests/theboringtv.manifest.json','manifest':manifest,'pool':'main','shortDescription':'Google TV-style home screen and cross-streaming recommendations','requirements':{'webosRelease':'>=6.0'}}
Path('manifests/theboringtv.manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
Path('api/apps.json').write_text(json.dumps({'paging':{'page':1,'count':1,'maxPage':1,'itemsTotal':1,'prevUrl':None,'nextUrl':None},'packages':[package]},indent=2)+'\n')
Path('apps.json').write_text(Path('api/apps.json').read_text())
Path('packages.json').write_text(json.dumps([package],indent=2)+'\n')
Path('index.html').write_text("""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LG Homebrew Apps | darc.dev</title><style>body{font:16px system-ui;background:#0e1424;color:#eef3ff;max-width:820px;margin:7vh auto;padding:24px}a{color:#81b4ff}article{padding:24px;border:1px solid #36435f;border-radius:16px;background:#18223a}code{overflow-wrap:anywhere;color:#aef5db}h1{font-size:2.2rem}</style><h1>LG webOS Homebrew Repository</h1><p>Independent third-party app catalog for LG Homebrew Channel.</p><article><img src="/icons/theboringtv.png" width="90" alt=""><h2>TheBoringTV 0.25.0</h2><p>Google TV-style launcher, streaming recommendations, search, watch links and trailers.</p><p><a href="/packages/"""+p.name+"""">Download .ipk</a> | <a href="https://github.com/theboringhumane/theboringtv-lgwebos">Source and setup</a></p><p>Configure your own TMDB and YouTube API credentials for content features. Root is only required for replacing the system home launcher.</p></article><h2>Homebrew Channel source</h2><p>Add this repository URL:</p><p><code>https://lg.darc.dev/</code></p><p>Direct catalog: <a href="/api/apps.json">/api/apps.json</a></p><small>Unofficial community packaging. Not affiliated with LG or the upstream developer.</small></html>""")
Path('README.md').write_text(f"""# LG Homebrew Repository (darc.dev)

Custom Homebrew Channel catalog including [TheBoringTV](https://github.com/theboringhumane/theboringtv-lgwebos).

Add `https://lg.darc.dev/` as a repository in Homebrew Channel. Direct manifest: `https://lg.darc.dev/api/apps.json`.

## Packaging and limitations
Current app version: {version}. SHA256: `{sha}`.
The .ipk was built from the upstream source without including personal API keys. TMDB and YouTube features require user configuration; consult upstream README. Normal app use does not require root, replacing the LG home screen does.

Files: `api/apps.json`, `manifests/`, `packages/`, `icons/`. Regenerate metadata with `python3 generate.py`.
This is an unofficial third-party build. Test on your TV at your own risk.
""")
print('MANIFEST READY',version,p.stat().st_size,sha)
