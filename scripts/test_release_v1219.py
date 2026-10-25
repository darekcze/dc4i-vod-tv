#!/usr/bin/env python3
"""Ensure exact release manifest + same collection of third-party apps."""
from pathlib import Path
import hashlib,json,subprocess,tarfile,io,re
R=Path(__file__).resolve().parents[1]
old=json.loads((R/'private/release-backups/2026-10-25-pre-1219/apps.json').read_text())
new=json.loads((R/'dist/api/apps.json').read_text())
assert len(old['packages'])==len(new['packages'])==33
old_external={p['id']:p for p in old['packages'] if p['id']!='com.dc4i.vodtv'}
new_external={p['id']:p for p in new['packages'] if p['id']!='com.dc4i.vodtv'}
assert old_external==new_external,'Unrelated Homebrew entries changed'
entry=next(x['manifest'] for x in new['packages'] if x['id']=='com.dc4i.vodtv')
assert entry['version']=='1.2.19'
assert entry['id']=='com.dc4i.vodtv'
assert entry['releaseDate']=='2026-10-25'
assert re.fullmatch(r'[0-9a-f]{64}',entry['ipkHash']['sha256'])
ipk=R/'dist/packages/com.dc4i.vodtv_1.2.19_all.ipk'
assert ipk.exists() and ipk.stat().st_size==entry['ipkSize']
assert hashlib.sha256(ipk.read_bytes()).hexdigest()==entry['ipkHash']['sha256']
assert (R/'dist/_worker.js').read_bytes()==(R/'private/release-backups/2026-10-25-pre-1219/_worker.js').read_bytes()
assert (R/'manifests/dc4i-vodtv.manifest.json').read_text()==(R/'dist/manifests/dc4i-vodtv.manifest.json').read_text()
html=(R/'dist/about.html').read_text()
assert 'com.dc4i.vodtv_1.2.19_all.ipk' in html
with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['ar','p',str(ipk),'data.tar.gz'])),mode='r:gz') as tf:
    folder='usr/palm/applications/com.dc4i.vodtv/'
    metadata=json.load(tf.extractfile(folder+'appinfo.json'))
    assert metadata['version']=='1.2.19'
    for asset in ['vod-personalization-ui.js','vod-recommendations.js','vod-channel-guide.js','vod-channel-guide.css','vod-guide-model.js','vod-guide-epg.js','vod-i18n.js']:
        assert tf.getmember(folder+asset).size>300
    js=tf.extractfile(folder+'vod-personalization-ui.js').read()
    assert b'recommendationOpensV1' in js and b'dc4iXtreamPlaylistsV1' not in js
    html=tf.extractfile(folder+'index.html').read()
    assert b'vod-recommendations.js' in html and b'vod-channel-guide.js' in html
    assert html.find(b'vod-xtream.js') < html.find(b'vod-channel-guide.js')
    guide=tf.extractfile(folder+'vod-channel-guide.js').read()
    assert b'gd-groups' in guide and b'gd-channels' in guide and b'gd-now' in guide
    assert b'guideFavoritesV1' in guide and b'guideSelectedGroupV1' in guide
    bridge=tf.extractfile(folder+'vod-xtream.js').read()
    assert b'guideEpg:guideEpg' in bridge and b'get_short_epg' in bridge

print('RELEASE_V1219_TEST_PASS','entries',len(new['packages']),'unchanged_other_apps',len(new_external),'sha256',entry['ipkHash']['sha256'])
