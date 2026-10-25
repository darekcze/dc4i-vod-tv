#!/usr/bin/env python3
"""Journaled metadata restore boundary; consumers pause on unresolved journal."""
from pathlib import Path
import shutil
R=Path(__file__).resolve().parents[1];A=R/'build/dc4i-vodtv'
shutil.copy2(R/'src/vod-backup-transaction.js',A/'vod-backup-transaction.js')
p=A/'index.html';s=p.read_text();anchor='<script src="vod-backup-ui.js"></script>';assert s.count(anchor)==1
p.write_text(s.replace(anchor,'<script src="vod-backup-transaction.js"></script>\n'+anchor))
p=A/'app.js';s=p.read_text();anchor='  function profileSettingsReadable() {';assert s.count(anchor)==1
s=s.replace(anchor,"""  function metadataRestorePending() {
    try{return localStorage.getItem((P.prefix || '')+'metadataRestoreJournalV1')!==null;}catch(e){return true;}
  }
  function restoreRead(k) {
    if(['metadataRestoreJournalV1','homeRailsLayoutV1','dc4iReminderPrefsV1','dc4iChartLinksV1','settings','recommendationOpensV1','playbackLearningV1'].indexOf(k)<0)throw Error('Unsupported restore key');
    var raw=localStorage.getItem((P.prefix || '')+k);if(raw!==null&&raw.length>(k==='metadataRestoreJournalV1'?524288:262144))throw Error('Restore limit');return raw;
  }
  function restoreWrite(k,raw) {
    restoreRead(k);if(raw===null)localStorage.removeItem((P.prefix || '')+k);
    else {if(typeof raw!=='string'||raw.length>(k==='metadataRestoreJournalV1'?524288:262144))throw Error('Restore limit');localStorage.setItem((P.prefix || '')+k,raw);}
  }
"""+anchor+"\n    if(metadataRestorePending())return false;")
for name,args in [('readReminderStorage','k'),('readChartStorage',''),('readPlaybackStorage',''),('readMetadataStorage','k'),('backupRead','k'),('backupWrite','k,raw')]:
    anchor='  function '+name+'('+args+') {';assert s.count(anchor)==1
    s=s.replace(anchor,anchor+"\n    if(metadataRestorePending())throw Error('Restore recovery required');")
anchor='    try {\n      if (arguments.length > 1)';assert s.count(anchor)==1
s=s.replace(anchor,"    try {\n      if(metadataRestorePending()&&['settings','homeRailsLayoutV1','dc4iReminderPrefsV1','dc4iChartLinksV1','recommendationOpensV1','playbackLearningV1'].indexOf(k)>=0)throw Error('Restore recovery required');\n      if (arguments.length > 1)")
anchor='store: store,';assert s.count(anchor)==1;s=s.replace(anchor,anchor+' restoreRead: restoreRead, restoreWrite: restoreWrite, metadataRestorePending: metadataRestorePending,')
anchor='if(!profileSettingsReadable()){toast';assert s.count(anchor)==1
s=s.replace(anchor,"if(!profileSettingsReadable()&&(!SROWS[+e.dataset.r]||SROWS[+e.dataset.r].key!=='metadataBackup')){toast")
anchor='  function openSettings() {';assert s.count(anchor)==1
s=s.replace(anchor,"  var settingsEditBaseline=null;\n"+anchor+"\n    settingsEditBaseline=JSON.stringify(store('settings'));")
anchor="    if (dirty) { store('settings', draft);";assert s.count(anchor)==1
s=s.replace(anchor,"    if (dirty) { if(JSON.stringify(store('settings'))!==settingsEditBaseline){toast(S.uiLang==='en'?'Settings changed elsewhere; reopen before saving':'Ustawienia zmieniono; otwórz ponownie przed zapisem');return;} store('settings', draft);")
p.write_text(s)
print('JOURNALED_RESTORE_READY metadata-only; unresolved journals pause consumers; browser locking required')
