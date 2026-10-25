#!/usr/bin/env python3
"""DVR capability information only; no recording backend or version bump."""
from pathlib import Path
import shutil
R=Path(__file__).resolve().parents[1];A=R/'build/dc4i-vodtv'
for name in ('vod-dvr-scheduler.js','vod-dvr-ui.js'):
    shutil.copy2(R/'src'/name,A/name)
p=A/'index.html';s=p.read_text();anchor='<script src="vod-home-ui.js"></script>'
assert s.count(anchor)==1
p.write_text(s.replace(anchor,anchor+'\n<script src="vod-dvr-scheduler.js"></script>\n<script src="vod-dvr-ui.js"></script>'))
p=A/'app.js';s=p.read_text();anchor="    if(row.key==='homeRailsLayout')"
assert s.count(anchor)==1
s=s.replace(anchor,"    if(row.key==='dvrStatus'){if(TV.dvr)TV.dvr.explain();return;}\n"+anchor);p.write_text(s)
print('DVR_CAPABILITY_INFO_READY no backend or recording controls')
