#!/usr/bin/env python3
"""Strict scoped storage and metadata-only in-app backup; no migration."""
from pathlib import Path
import shutil
R=Path(__file__).resolve().parents[1];A=R/'build/dc4i-vodtv'
for name in ('vod-metadata-backup.js','vod-backup-ui.js'):shutil.copy2(R/'src'/name,A/name)
p=A/'index.html';s=p.read_text();anchor='<script src="vod-playback-ui.js"></script>';assert s.count(anchor)==1
p.write_text(s.replace(anchor,anchor+'\n<script src="vod-metadata-backup.js"></script>\n<script src="vod-backup-ui.js"></script>'))
p=A/'app.js';s=p.read_text();anchor='  // ---------- settings (saved on the TV in localStorage) ----------';assert s.count(anchor)==1
s=s.replace(anchor,"""  function profileSettingsReadable() {
    try {var raw=localStorage.getItem((P.prefix || '')+'settings');if(raw===null)return true;
      var value=JSON.parse(raw);if(!value||typeof value!=='object'||Array.isArray(value))return false;
      return ['recoLearnPlayback','recoLearnHistory','recoEnabled'].every(function(k){return value[k]===undefined||typeof value[k]==='boolean';});
    }catch(e){return false;}
  }
  function readMetadataStorage(k) {
    if(['homeRailsLayoutV1','homeRailsMetadataV1','recommendationOpensV1','guideFavoritesV1','guideSelectedGroupV1','guideLastChannelV1'].indexOf(k)<0)throw Error('Unsupported metadata key');
    var raw=localStorage.getItem((P.prefix || '')+k);if(raw===null)return null;
    if(raw.length>2000000)throw Error('Metadata limit');var value=JSON.parse(raw);
    if(value===null&&k!=='homeRailsMetadataV1')throw Error('Invalid metadata');return value;
  }
  function backupRead(k) {
    if(['homeRailsLayoutV1','dc4iReminderPrefsV1','dc4iChartLinksV1'].indexOf(k)<0)throw Error('Unsupported backup key');
    var raw=localStorage.getItem((P.prefix || '')+k);if(raw!==null&&raw.length>16384)throw Error('Backup limit');return raw;
  }
  function backupWrite(k,raw) {
    backupRead(k);
    if(raw===null)localStorage.removeItem((P.prefix || '')+k);
    else {if(typeof raw!=='string'||raw.length>16384)throw Error('Backup limit');localStorage.setItem((P.prefix || '')+k,raw);}
  }
"""+anchor)
anchor="      if (arguments.length > 1) localStorage[(P.prefix || '') + k] = JSON.stringify(v);";assert s.count(anchor)==1
s=s.replace(anchor,"      if (arguments.length > 1) {if(k==='settings'&&!profileSettingsReadable())throw Error('Unreadable settings');localStorage[(P.prefix || '') + k] = JSON.stringify(v);}")
anchor='store: store,';assert s.count(anchor)==1;s=s.replace(anchor,anchor+' readMetadataStorage: readMetadataStorage, profileSettingsReadable: profileSettingsReadable, backupRead: backupRead, backupWrite: backupWrite,')
anchor="    if(row.key==='playbackClear')";assert s.count(anchor)==1;s=s.replace(anchor,"    if(row.key==='metadataBackup'){if(TV.metadataBackup)TV.metadataBackup.openSettings();return;}\n"+anchor);anchor='  function choose(e) {'
if anchor not in s: anchor='  function choose(e){'
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\n    if(!profileSettingsReadable()){toast(S.uiLang==='en'?'Settings unreadable; not saved':'Nie można odczytać ustawień; nie zapisano');return;}")
p.write_text(s)
p=A/'dc4i.css' ;p.write_text(p.read_text()+'''
.metadata-backup{position:fixed;inset:110px 0 0;padding:24px 60px;background:#071638;color:#eef5ff;z-index:30;overflow:auto;}
.metadata-backup[hidden]{display:none!important;}
.backup-control{padding:10px;margin:4px;background:#152d50;font-size:22px;}
.backup-control.focus,.backup-text.focus{outline:4px solid #b4f34c;}
.backup-text{width:90%;height:180px;color:#eef5ff;background:#152d50;font-size:18px;}
''')
print('HARDENING_READY scoped strict readers; metadata-only preview/import/undo')
