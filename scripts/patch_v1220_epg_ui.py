#!/usr/bin/env python3
"""Wire reviewed local metadata boundary; no public ingestion or version bump."""
from pathlib import Path
import shutil
R=Path(__file__).resolve().parents[1]
A=R/'build/dc4i-vodtv'
for name in ('vod-rich-epg.js','vod-epg-metadata-ui.js'):
    shutil.copy2(R/'src'/name,A/name)
p=A/'index.html';s=p.read_text()
anchor='<script src="vod-channel-guide.js"></script>'
assert s.count(anchor)==1
s=s.replace(anchor,'<script src="vod-rich-epg.js"></script>\n<script src="vod-epg-metadata-ui.js"></script>\n'+anchor)
p.write_text(s)
p=A/'features/details.js';s=p.read_text()
anchor='    if(d && TV.xtream && TV.xtream.getAccounts().length && TV.xtream.searchEpg)'
assert s.count(anchor)==1
s=s.replace(anchor,"    if(TV.epgMetadata)TV.epgMetadata.renderDetails(box.querySelector('.depg'),it.title,[]);\n"+anchor)
anchor="          epgHost.textContent='EPG: brak dopasowania w sprawdzonych kanałach (niepełny indeks).';"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\n          if(TV.epgMetadata)TV.epgMetadata.renderDetails(epgHost,it.title,[]);")
anchor="        if(TV.view()==='details')TV.rebuild();"
assert s.count(anchor)==1
s=s.replace(anchor,"        if(TV.epgMetadata)TV.epgMetadata.renderDetails(epgHost,it.title,events);\n"+anchor)
anchor="        if(stack[stack.length-1]===it)epgHost.textContent='EPG jest obecnie niedostępne.';"
assert s.count(anchor)==1
s=s.replace(anchor,"        if(!box.hidden && stack[stack.length-1]===it){\n"+
 "          epgHost.textContent='EPG jest obecnie niedostępne.';\n"+
 "          if(TV.epgMetadata)TV.epgMetadata.renderDetails(epgHost,it.title,[]);\n        }")
p.write_text(s)
p=A/'features/details.css';p.write_text(p.read_text()+
 '\n#details .depg-metadata{font-size:17px;line-height:1.4;color:#a9bfdc;margin:6px 0;overflow-wrap:anywhere;}\n')
print('LOCAL_EPG_METADATA_UI_READY public ingestion disabled; production version unchanged')
