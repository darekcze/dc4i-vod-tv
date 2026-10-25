#!/usr/bin/env python3
"""Observe native player progression, keeping external handoffs unobserved."""
from pathlib import Path
import shutil
R=Path(__file__).resolve().parents[1];A=R/'build/dc4i-vodtv'
for name in ('vod-playback-learning.js','vod-playback-ui.js'):shutil.copy2(R/'src'/name,A/name)
p=A/'index.html';s=p.read_text();anchor='<script src="vod-chart-ui.js"></script>';assert s.count(anchor)==1
p.write_text(s.replace(anchor,anchor+'\n<script src="vod-playback-learning.js"></script>\n<script src="vod-playback-ui.js"></script>'))
p=A/'app.js';s=p.read_text();anchor='  // ---------- settings (saved on the TV in localStorage) ----------';assert s.count(anchor)==1
s=s.replace(anchor,"""  function readPlaybackStorage() {
    var raw=localStorage.getItem((P.prefix || '')+'playbackLearningV1');
    if(raw===null)return null;
    var value=JSON.parse(raw);if(value===null)throw Error('Invalid playback observations');return value;
  }
"""+anchor)
anchor='store: store,';assert s.count(anchor)==1;s=s.replace(anchor,anchor+' readPlaybackStorage: readPlaybackStorage,')
anchor="    if(row.key==='chartLinks')";assert s.count(anchor)==1;s=s.replace(anchor,"    if(row.key==='playbackClear'){if(TV.playbackLearning)TV.playbackLearning.clear();return;}\n"+anchor);p.write_text(s)
p=A/'vod-xtream.js';s=p.read_text();anchor=' video.src=src;video.load();';assert s.count(anchor)==1
s=s.replace(anchor," if(TV.playbackLearning)TV.playbackLearning.begin(video,i);\n"+anchor)
anchor=" var video=$('video');video.pause();video.removeAttribute('src');video.load();";assert s.count(anchor)==1
s=s.replace(anchor," var video=$('video');if(TV.playbackLearning)TV.playbackLearning.stop(video);video.pause();video.removeAttribute('src');video.load();")
anchor="group:'Sezon '+season,ext:ext});";assert s.count(anchor)==1;s=s.replace(anchor,"group:'Sezon '+season,ext:ext,learning:i.learning});");p.write_text(s)
p=A/'features/details.js';s=p.read_text();anchor='function(){TV.xtream.openItem(source);}';assert s.count(anchor)==1
s=s.replace(anchor,"function(){TV.xtream.openItem(Object.assign({},source,{learning:{genre_ids:(d.genres||[]).map(function(g){return g.id;})}}));}");p.write_text(s)
print('PLAYBACK_LEARNING_READY native progression only; track availability unknown without media evidence')
