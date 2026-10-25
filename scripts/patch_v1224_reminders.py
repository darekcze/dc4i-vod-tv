#!/usr/bin/env python3
"""Extend the existing reminder key/entrypoints; remove the legacy duplicate timer."""
from pathlib import Path
import shutil
R=Path(__file__).resolve().parents[1];A=R/'build/dc4i-vodtv'
for name in ('vod-reminders.js','vod-reminder-ui.js'):
    shutil.copy2(R/'src'/name,A/name)
p=A/'index.html';s=p.read_text();anchor='<script src="vod-dvr-ui.js"></script>'
assert s.count(anchor)==1
p.write_text(s.replace(anchor,anchor+'\n<script src="vod-reminders.js"></script>\n<script src="vod-reminder-ui.js"></script>'))
p=A/'vod-xtream.js';s=p.read_text();start=s.index("var reminders=TV.store('dc4iEpgRemindersV1')||[];");end=s.index('function chosenEpgChannels(){',start)
assert s[start:end].count('setInterval(')==1
s=s[:start]+"function remindEpg(event){return TV.reminders?TV.reminders.add(event):false;}\n"+s[end:];p.write_text(s)
p=A/'app.js';s=p.read_text();anchor="    if(row.key==='dvrStatus')"
assert s.count(anchor)==1
p.write_text(s.replace(anchor,"    if(row.key==='reminderSettings'){if(TV.reminders)TV.reminders.openSettings();return;}\n"+anchor))
p=A/'dc4i.css';p.write_text(p.read_text()+'''
.reminder-settings{position:fixed;inset:110px 0 0;padding:32px 60px;background:#071638;color:#eef5ff;z-index:30;overflow:auto;}
.reminder-settings[hidden]{display:none!important;}
.reminder-control{padding:14px;margin:5px 0;background:#152d50;border-radius:9px;font-size:23px;overflow-wrap:anywhere;}
.reminder-control.focus{outline:4px solid #b4f34c;background:#245180;}
''')
print('FOREGROUND_REMINDERS_READY existing key preserved; legacy timer removed')
