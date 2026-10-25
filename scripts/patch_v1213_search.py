#!/usr/bin/env python3
"""1.2.13 release: one search-in-provider bar for search and details plus Labs/repo URLs."""
from pathlib import Path
import shutil,json
R=Path(__file__).resolve().parents[1]
A=R/'build/dc4i-vodtv'
assert A.is_dir()
VERSION='1.2.13'

# Use existing actions. The availability header and external sources must remain separate.
shutil.copy2(R/'src/vod-external-search.js', A/'vod-external-search.js')
shutil.copy2(R/'src/vod-external-search.css', A/'vod-external-search.css')
markup=A/'index.html';s=markup.read_text(encoding='utf-8')
anchor='<script src="features/details.js"></script>'
assert s.count(anchor)==1
s=s.replace(anchor,'<script src="vod-external-search.js"></script>\n'+anchor)
anchor='<link rel="stylesheet" href="vod-root.css">'
assert s.count(anchor)==1
s=s.replace(anchor,anchor+'\n<link rel="stylesheet" href="vod-external-search.css">')
assert 'href="https://lg.darc.dev"' in s
assert 'href="https://www.dc4i.com"' in s
s=s.replace('href="https://lg.darc.dev"','href="https://lg.darc.dev/browse/"')
s=s.replace('href="https://www.dc4i.com"','href="https://www.dc4i.com/labs"')
assert s.count('1.2.12 · 25.10.2026')==1
s=s.replace('1.2.12 · 25.10.2026','1.2.13 · 25.10.2026',1)
markup.write_text(s,encoding='utf-8')

js=A/'app.js';a=js.read_text(encoding='utf-8')
assert "target:'https://lg.darc.dev'" in a
assert "target:'https://www.dc4i.com'" in a
a=a.replace("target:'https://lg.darc.dev'","target:'https://lg.darc.dev/browse/'")
a=a.replace("target:'https://www.dc4i.com'","target:'https://www.dc4i.com/labs'")
a=a.replace("currentVersion: '1.2.12'","currentVersion: '1.2.13'")
js.write_text(a,encoding='utf-8')
version_module=A/'vod-version-check.js'
v=version_module.read_text(encoding='utf-8')
assert "var CURRENT_VERSION = '1.2.12';" in v
version_module.write_text(v.replace("var CURRENT_VERSION = '1.2.12';","var CURRENT_VERSION = '1.2.13';"),encoding='utf-8')

# Search: keep the filter/availability logic, but move the five provider actions BELOW VOD.
search=A/'features/search.js';t=search.read_text(encoding='utf-8')
first='<div id="syt"></div><h3 id="sresTitle"></h3><div id="sres" class="strip"></div>'
assert t.count(first)==1
last='<h3 id="sresTitle"></h3><div id="sres" class="strip"></div><div id="syt"></div>'
t=t.replace(first,last)
start=t.index('  var yt = TV.el(')
end=t.index("  $('sxclose').onok",start)
replacement="""  var externalButtons=[];
  function refreshExternal() {
    externalButtons=TV.vodExternalSearch.render($('syt'),{title:q.trim()});
  }
  refreshExternal();
"""
t=t[:start]+replacement+t[end:]
old="    yt.innerHTML='<b>&#9654;</b> '+tr('Szukaj w YouTube','Search YouTube')+(q.trim() ? ': '+esc(q.trim()) : '');"
assert t.count(old)==1
t=t.replace(old,'    refreshExternal();')
old='''      var offers=(region.flatrate||[]).concat(region.free||[],region.ads||[]);
      var seen={}, names=[];
      offers.forEach(function(p) {if(p.provider_name && !seen[p.provider_name]) {seen[p.provider_name]=1;names.push(p.provider_name);}});'''
assert t.count(old)==1
new='''      var offers=(region.flatrate||[]).concat(region.free||[],region.ads||[]);
      var seen={},names=[],selected=TV.S.services||[];
      offers.forEach(function(p) {
        var svc=TV.svcFor(p.provider_name);
        if(svc && selected.indexOf(svc.name)>=0 && !seen[svc.name]) {
          seen[svc.name]=1;names.push(svc.name);
        }
      });'''
t=t.replace(old,new)
old="return TV.C.REGION+':'+getType(item)+':'+item.id;"
assert t.count(old)==1
t=t.replace(old,"return TV.C.REGION+':'+(TV.S.services||[]).join(',')+':'+getType(item)+':'+item.id;")
old="      $('sresTitle').textContent=tr('Brak ofert streamingu '+regionLabel()+'. Wybierz „Pozostałe”.',\n         'No streaming offers '+regionLabel()+'. Choose “Others”.');"
assert t.count(old)==1
t=t.replace(old,"      $('sresTitle').textContent=tr('Brak w wybranych serwisach','Not available in selected services');")
old="[filterEls, [yt], [].slice.call($('sres').children)]"
assert t.count(old)==1
t=t.replace(old,"[filterEls, [].slice.call($('sres').children), externalButtons]")
search.write_text(t,encoding='utf-8')

# Details: remove prior scattered external launches, and use the exact same provider toolbar.
details=A/'features/details.js';d=details.read_text(encoding='utf-8')
old='<div class="dbtns"></div><div class="dextra"></div>'
assert d.count(old)==1
d=d.replace(old,'<div class="davailability-title">'+"' + (TV.S.uiLang==='en'?'VOD in selected services':'VOD w wybranych serwisach') + '"+'</div><div class="dbtns"></div><div class="dexternal"></div><div class="dextra"></div>')
start=d.index('      var subscriptions=(here.flatrate||[]).concat(')
end=d.index('      var tr = ((d.videos || {}).results',start)
d=d[:start]+d[end:]
anchor="    var wl = btn(inList(it) ? '✓ Na liście' : '＋ Do obejrzenia', function () { wl.textContent = toggle(it) ? '✓ Na liście' : '＋ Do obejrzenia'; });"
assert d.count(anchor)==1
d=d.replace(anchor,"    if (d && TV.vodExternalSearch) TV.vodExternalSearch.render(box.querySelector('.dexternal'),{title:it.title,tmdb:it.tmdb,details:d});\n"+anchor)
old="return [[].slice.call(box.querySelectorAll('.dbtns .f')), strip ? [].slice.call(strip.children) : []];"
assert d.count(old)==1
d=d.replace(old,"return [[].slice.call(box.querySelectorAll('.dbtns .f')), [].slice.call(box.querySelectorAll('.dexternal .f')), strip ? [].slice.call(strip.children) : []];")
details.write_text(d,encoding='utf-8')

meta=A/'appinfo.json';obj=json.loads(meta.read_text(encoding='utf-8'))
assert obj.get('id')=='com.dc4i.vodtv' and obj.get('version')=='1.2.12'
obj['version']=VERSION
meta.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('V1213_PATCH_READY',VERSION,'Search and details use identical five providers; links to Labs and Browse')
