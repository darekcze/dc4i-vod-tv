#!/usr/bin/env python3
"""Create a standalone synthetic EPG browser fixture; no real feed/network input."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
from xmltv_metadata import parse_xmltv

ROOT = Path(__file__).resolve().parents[1]
NOW = 1792890000000

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    snapshot = parse_xmltv((ROOT / 'tests/fixtures/epg/synthetic.xml').read_bytes(), 'synthetic-test', NOW)
    # The partial input is deliberately retained and visibly labeled.
    payload = json.dumps(snapshot, ensure_ascii=False).replace('<', '\\u003c')
    script = (ROOT / 'src/vod-rich-epg.js').read_text() + '\n' + '''
var fixtureSnapshot=PAYLOAD,fixtureNow=1792890000000;
var fixtureCache=window.DC4IRichEpg.createCache({now:function(){return fixtureNow;},ttlMs:1000,staleMs:2000});
fixtureCache.put(fixtureSnapshot);
function renderFixture(){
 var state=fixtureCache.get('synthetic-test');window.fixtureState=state;
 document.getElementById('status').textContent=state.status+(state.partial?' / partial':'');
 var list=document.getElementById('events');list.replaceChildren();
 if(!state.snapshot)return;
 window.DC4IRichEpg.timeline(state.snapshot,'synthetic.one',1792886400000,1792900000000).forEach(function(event){
   var row=document.createElement('li');
   row.textContent=new Date(event.start).toISOString()+' | '+event.title+' | '+event.provenance.source+
     ' | audio/subtitles: unknown | playback unavailable';list.appendChild(row);
 });
}
document.getElementById('stale').onclick=function(){fixtureNow=1792890001000;renderFixture();};
document.getElementById('expire').onclick=function(){fixtureNow=1792890003000;renderFixture();};
renderFixture();
'''.replace('PAYLOAD', payload)
    digest = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
    page = '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'sha256-HASH'; style-src 'unsafe-inline'; connect-src 'none'; base-uri 'none'; form-action 'none'">
<title>EPG 1.2.20 — SYNTHETIC OFFLINE PREVIEW</title>
<style>body{background:#071638;color:#eef5ff;font:24px sans-serif;margin:60px}li{margin:24px 0;line-height:1.5}button{font:inherit;padding:16px;margin:12px}strong{color:#b4f34c}</style>
</head><body><h1>EPG foundation / synthetic fixture</h1>
<p>Not a release. No real programme data, device calls or source requests. UTC timestamps demonstrate the repeated DST hour.</p>
<strong id="status"></strong><ul id="events"></ul>
<button id="stale">Advance to stale</button><button id="expire">Advance to expired</button>
<script>SCRIPT</script></body></html>'''.replace('HASH', digest).replace('SCRIPT', script)
    with args.output.open('x', encoding='utf-8') as output:
        output.write(page)
    print('SYNTHETIC_PREVIEW_READY', args.output)

if __name__ == '__main__':
    main()
