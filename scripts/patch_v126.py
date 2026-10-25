#!/usr/bin/env python3
"""Metadata-aware local Kodi handoff, Plex search and YouTube title search."""
from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'build/dc4i-vodtv'
version='1.2.10'
meta_file=APP/'appinfo.json'
meta=json.loads(meta_file.read_text(encoding='utf-8'))
assert meta.get('id')=='com.dc4i.vodtv'
meta['version']=version
meta_file.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
shutil.copyfile(ROOT/'src/vod-handoff.js',APP/'vod-handoff.js')
html=APP/'index.html';s=html.read_text(encoding='utf-8')
anchor='<script src="features/details.js"></script>'
assert s.count(anchor)==1
s=s.replace(anchor,'<script src="vod-handoff.js"></script>\n'+anchor)
html.write_text(s,encoding='utf-8')
p=APP/'features/details.js';s=p.read_text(encoding='utf-8')
old="function(){TV.launch('org.xbmc.kodi');}));"
assert s.count(old)==1
s=s.replace("'Kodi (open app)':'Kodi (otwórz aplikację)'","'Play in Kodi (Xtream)':'Oglądaj w Kodi (Xtream)'",1)
s=s.replace(old,"function(){TV.vodHandoff.kodi(it.title,it.tmdb);}));",1)
needle="        if (!subscriptions.length) extra += (extra ? '  ·  ':'')+"
assert s.count(needle)==1
new="""        btns.appendChild(btn('▶ '+(TV.S.uiLang==='en'?'Plex Web (search title)':'Plex Web (szukaj tytułu)'),
          function(){TV.vodHandoff.plexSearch(it.title);}));
        btns.appendChild(btn('▶ '+(TV.S.uiLang==='en'?'YouTube (search title)':'YouTube (szukaj tytułu)'),
          function(){TV.vodHandoff.youtubeSearch(it.title);}));
"""
s=s.replace(needle,new+needle)
p.write_text(s,encoding='utf-8')
print('PATCH_V126',meta['id'],meta['version'],'Kodi TMDB, Plex search, YouTube title search')
