#!/usr/bin/env python3
"""Add allowlisted official weekly-chart links, never a feed."""
from pathlib import Path
import shutil
R=Path(__file__).resolve().parents[1];A=R/'build/dc4i-vodtv'
for name in ('vod-chart-links.js','vod-chart-ui.js'):shutil.copy2(R/'src'/name,A/name)
p=A/'index.html';s=p.read_text();anchor='<script src="vod-reminder-ui.js"></script>';assert s.count(anchor)==1
p.write_text(s.replace(anchor,anchor+'\n<script src="vod-chart-links.js"></script>\n<script src="vod-chart-ui.js"></script>'))
p=A/'app.js';s=p.read_text();anchor="    if(row.key==='reminderSettings')";assert s.count(anchor)==1
p.write_text(s.replace(anchor,"    if(row.key==='chartLinks'){if(TV.chartLinks)TV.chartLinks.openSettings();return;}\n"+anchor))
p=A/'dc4i.css';p.write_text(p.read_text()+'''
.chart-links{position:fixed;inset:110px 0 0;padding:32px 60px;background:#071638;color:#eef5ff;z-index:30;overflow:auto;}
.chart-links[hidden]{display:none!important;}
.chart-control{padding:14px;margin:5px 0;background:#152d50;border-radius:9px;font-size:23px;}
.chart-control.focus{outline:4px solid #b4f34c;background:#245180;}
''')
print('CHART_LINKS_READY weekly outbound only; feed disabled, rights unverified')
