#!/usr/bin/env python3
"""1.2.18 app patch: TV-local recommendation scoring, metadata and settings."""
from pathlib import Path
import json,shutil
R=Path(__file__).resolve().parents[1]
APP=R/'build/dc4i-vodtv'
for name in ['vod-recommendations.js','vod-personalization-ui.js']:
 shutil.copyfile(R/'src'/name,APP/name)
p=APP/'index.html'
s=p.read_text(encoding='utf-8')
needle='<script src="vod-i18n.js"></script>'
assert s.count(needle)==1, 'Missing script entrypoint'
s=s.replace(needle,needle+'\n<script src="vod-recommendations.js"></script>\n<script src="vod-personalization-ui.js"></script>')
old='1.2.17 · 25.10.2026'
assert s.count(old)==1
p.write_text(s.replace(old,'1.2.18 · 25.10.2026'),encoding='utf-8')
p=APP/'appinfo.json'
d=json.loads(p.read_text())
assert d['id']=='com.dc4i.vodtv' and d['version']=='1.2.17'
d['version']='1.2.18'
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=APP/'app.js'
s=p.read_text(encoding='utf-8')
def replace(before,after):
 global s
 assert s.count(before)==1, ('Cannot locate exact patch anchor',before[:100],s.count(before))
 s=s.replace(before,after,1)
old="src: svc ? svc.name : pickLabel(), svc: svc, tmdb: {type: type, id: m.id}"
new=old+""",
      genre_ids: Array.isArray(m.genre_ids)?m.genre_ids:[],
      vote_average: typeof m.vote_average==='number'?m.vote_average:null,
      vote_count: typeof m.vote_count==='number'?m.vote_count:0,
      popularity: typeof m.popularity==='number'?m.popularity:0,
      release_date: date,media_type:type,original_language:m.original_language||''"""
replace(old,new)
old="    var extra = rowProviders.map(function (fn) { return fn(); }).filter(Boolean);"
new=old+"""
    var personalized=extra.filter(function(x){return x.title==='Dopasowane do profilu';});
    extra=extra.filter(function(x){return x.title!=='Dopasowane do profilu';});"""
replace(old,new)
old="rowsData = base.slice(0, 2).concat([{title: 'Kontynuuj oglądanie', items: recent}], extra, base.slice(2))"
new="rowsData = personalized.concat(base.slice(0, 2), [{title: 'Kontynuuj oglądanie', items: recent}], extra, base.slice(2))"
replace(old,new)
old="    c.item = it; c.onok = function () { TV.itemOk(it); };"
new="""    if(it.recoScore!=null){
      var recommendationBadge=el('div','reco-match');
      recommendationBadge.textContent='Dopasowanie '+String(it.recoScore)+'/100 · '+String(it.recoReason||'');
      c.appendChild(recommendationBadge);
    }
"""+old
replace(old,new)
old="    heroItems: function () { return heroItems; },"
new=old+"""
    homeCandidates: function() {
      var out=heroItems.slice();
      base.forEach(function(row){if(row.items)row.items.forEach(function(item){out.push(item);});});
      return out;
    },"""
replace(old,new)
old="    if (row.key === 'clear') { recent = []; store('recent', []); buildRows(); return toast('Historia oglądania wyczyszczona'); }"
new=old+"""
    if (row.key === 'recoClearHistory') {
      if(window.TV && window.TV.personalized)window.TV.personalized.clear();
      return;
    }"""
replace(old,new)
old="currentVersion: '1.2.17'"
replace(old,"currentVersion: '1.2.18'")
p.write_text(s,encoding='utf-8')
p=APP/'vod-version-check.js'
s=p.read_text(encoding='utf-8')
old="var CURRENT_VERSION = '1.2.17';"
assert s.count(old)==1
p.write_text(s.replace(old,"var CURRENT_VERSION = '1.2.18';"),encoding='utf-8')
p=APP/'dc4i.css'
s=p.read_text(encoding='utf-8')
s+="""
/* Profile-only recommendation match badge, clear attribution to computed score. */
#home .reco-match {
  position:absolute;top:10px;bottom:auto;left:10px;right:10px;
  z-index:3;padding:7px 9px;background:rgba(9,30,61,.94);
  border:1px solid rgba(160,214,245,.50);border-radius:9px;
  color:#e2f5ff;font-size:16px;font-weight:650;line-height:1.25;
  overflow:hidden;max-height:48px;
}
#home .card:focus-visible .reco-match,#home .card.focus .reco-match {
  background:#194a61;color:#fff;border-color:#b4f34c;
}
#home .row:first-child h3 {font-size:28px;}
"""
p.write_text(s,encoding='utf-8')
print('PROFILE_UI_V1218_PATCHED','id',d['id'],'version',d['version'])
