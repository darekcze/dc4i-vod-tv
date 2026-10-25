#!/usr/bin/env python3
"""Replace archive-flag playback with an honest unconfigured capability boundary."""
from pathlib import Path
import shutil
R=Path(__file__).resolve().parents[1];A=R/'build/dc4i-vodtv'
for name in ('vod-archive-capabilities.js','vod-archive-ui.js'):
    shutil.copy2(R/'src'/name,A/name)
p=A/'index.html';s=p.read_text();anchor='<script src="vod-xtream.js"></script>'
assert s.count(anchor)==1
p.write_text(s.replace(anchor,'<script src="vod-archive-capabilities.js"></script>\n<script src="vod-archive-ui.js"></script>\n'+anchor))
p=A/'vod-xtream.js';s=p.read_text();start=s.index('function playEpg(entry){');end=s.index('function errorMsg(e){',start)
assert s[start:end].count("'/timeshift/'")==1
s=s[:start]+'''function playEpg(entry){
 if(!entry || !entry.channel)return false;
 if(entry.state==='now')return choose(entry.channel);
 if(entry.state==='future')return remindEpg(entry);
 if(entry.state==='past' && TV.archive)return TV.archive.request(entry,!!account());
 return false;
}
function archiveStatus(entry){return TV.archive?TV.archive.describe(entry,!!account()):{status:'unverified',playable:false,label:'CatchUp'};}
'''+s[end:]
anchor='searchEpg:searchEpg,remindEpg:remindEpg,playEpg:playEpg,'
assert s.count(anchor)==1
s=s.replace(anchor,anchor+'archiveStatus:archiveStatus,');p.write_text(s)
p=A/'features/details.js';s=p.read_text();anchor="else if(e.archiveFlag)row.appendChild(btn('Sprawdź CatchUp',function(){TV.xtream.playEpg(e);}));"
assert s.count(anchor)==1
s=s.replace(anchor,"else if(e.archiveFlag){var capability=TV.xtream.archiveStatus(e);var hint=TV.el('span','depg-noarchive');hint.setAttribute('translate','no');hint.textContent=capability.label;row.appendChild(hint);}")
p.write_text(s)
p=A/'features/search.js';s=p.read_text();anchor="e.archiveFlag?'Archiwum (sprawdź odtwarzanie)':'Archiwalna emisja'"
assert s.count(anchor)==1
s=s.replace(anchor,"TV.xtream.archiveStatus(e).label");p.write_text(s)
print('ARCHIVE_CAPABILITY_GATE_READY no provider transport configured; live path unchanged')
