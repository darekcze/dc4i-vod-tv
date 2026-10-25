#!/usr/bin/env python3
"""Fix disconnected TMDB and Xtream title catalogs; preserve exact verified source links."""
from pathlib import Path
import shutil,json
R=Path(__file__).resolve().parents[1]
A=R/'build/dc4i-vodtv'
for fn in ('vod-title-mapping.js','vod-source-index.js'):
 shutil.copy2(R/'src'/fn,A/fn)
h=A/'index.html';html=h.read_text(encoding='utf-8')
anchor='<script src="features/search.js"></script>'
assert html.count(anchor)==1
html=html.replace(anchor,'<script src="vod-title-mapping.js"></script>\n<script src="vod-source-index.js"></script>\n'+anchor)
assert '1.2.16 · 25.10.2026' in html
html=html.replace('1.2.16 · 25.10.2026','1.2.17 · 25.10.2026')
h.write_text(html,encoding='utf-8')
meta=A/'appinfo.json';obj=json.loads(meta.read_text())
assert obj['version']=='1.2.16'
obj['version']='1.2.17';meta.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=A/'app.js';s=p.read_text()
assert "currentVersion: '1.2.16'" in s
p.write_text(s.replace("currentVersion: '1.2.16'","currentVersion: '1.2.17'"))
p=A/'vod-version-check.js';s=p.read_text()
assert "var CURRENT_VERSION = '1.2.16';" in s
p.write_text(s.replace("var CURRENT_VERSION = '1.2.16';","var CURRENT_VERSION = '1.2.17';"))
# Map all matches once in a single result list; do not discard a source once a TMDB
# card has been matched.
p=A/'features/search.js';s=p.read_text()
needle="TV.xtream.searchCatalog(term,{kind:xtMode,language:language})"
assert needle in s
s=s.replace(needle,"TV.xtream.searchCatalog(term,{kind:xtMode,language:'all'})")
needle="xtResults=(items||[]).filter(function(x){return matchesLanguage(x,true);});"
assert needle in s
s=s.replace(needle,"xtResults=items||[];")
start=s.index('    var list=(filter===')
end=s.index("    chosen=chosen.slice(0,MAX);",start)
replacement="""    var list=(filter==='vod'?results.filter(function(r){return r.info.available;}):results).slice(0,MAX);
    var infos={};
    list.forEach(function(r){infos[getType(r.item)+':'+String(r.item.id)]=r;});
    var combined=window.DC4ITitleMapping.merge(list.map(function(r){return r.item;}),filter==='vod'?[]:xtResults);
    var chosen=[];
    combined.forEach(function(x){
      if(x.tmdb) {
        var mt=getType(x.tmdb);
        var info=infos[mt+':'+String(x.tmdb.id)];
        if(!info)return;
        if(x.sources.length && TV.titleSources)TV.titleSources.remember(x.tmdb,x.sources);
        chosen.push({tmdb:info,sources:x.sources});
      } else if(x.sources.length) {
        var src=x.sources[0];
        if(filter==='vod')return;
        if((filter==='movie'&&src.type!=='movie')||(filter==='series'&&src.type!=='series'))return;
        if((filter==='tv'||filter==='iptv')&&src.type!=='live')return;
        var localized=matchesLanguage(src,true);
        // Exact typed searches should still expose an otherwise unavailable
        // foreign-language Xtream title; do not mislabel it as Polish.
        if(language!=='all'&&!localized)return;
        if(filter==='all' && src.type==='live' && chosen.filter(function(y){return y.xtream && y.xtream.type==='live';}).length>=8)return;
        chosen.push({xtream:src});
      }
    });
"""
s=s[:start]+replacement+s[end:]
needle="var r=entry.tmdb,item=TV.fromTmdb(r.item),card=TV.card(item);"
assert needle in s
s=s.replace(needle,"var r=entry.tmdb,item=TV.fromTmdb(r.item),card=TV.card(item);\n        if(entry.sources && entry.sources.length)item.xtreamSources=entry.sources;")
needle="var source=TV.el('div','swhere vod-status');source.textContent='Xtream · '+(x.group||'');card.appendChild(source);"
assert needle in s
s=s.replace(needle,"""var source=TV.el('div','swhere vod-status');
        source.textContent='Xtream '+({movie:'Filmy',series:'Seriale',live:'TV'})[x.type]+' · '+(x.group||'');
        card.appendChild(source);
        if(x.rating)card.appendChild(TV.el('div','xtream-score','★ '+TV.esc(String(x.rating))));
        if(!x.icon && x.tmdb && /^\\d+$/.test(String(x.tmdb))){
          TV.tmdb((x.type==='series'?'tv':'movie')+'/'+x.tmdb).then(function(meta){
            if(!meta || !meta.poster_path && !meta.backdrop_path)return;
            var img=document.createElement('img');
            img.src=TV.IMG+'w500'+(meta.backdrop_path||meta.poster_path);
            img.alt='';img.loading='lazy';
            if(card.parentNode)pic.insertBefore(img,pic.firstChild);
          },function(){});
        }""")
needle="card.onok=function(){ROOT.hidden=true;TV.xtream.openItem(x);};"
assert needle in s
s=s.replace(needle,"card.onok=function(){ROOT.hidden=true;TV.xtream.openItem(x);};")
p.write_text(s,encoding='utf-8')
# Detail view can open exact Xtream source, while retaining regional VOD offers.
p=A/'features/details.js';s=p.read_text()
needle="    if (d && TV.vodExternalSearch) TV.vodExternalSearch.render(box.querySelector('.dexternal'),{title:it.title,tmdb:it.tmdb,details:d});"
assert s.count(needle)==1
s=s.replace(needle,needle+"""
    if (d && TV.titleSources && it.tmdb) {
      var existing=it.xtreamSources||TV.titleSources.get(d)||[];
      function showSources(sources) {
        if(box.hidden||stack[stack.length-1]!==it || !sources || !sources.length)return;
        var host=box.querySelector('.dbtns');
        sources.forEach(function(source){
          if(host.querySelector('[data-xtream-id="'+source.id+'"]'))return;
          var b=btn('▶ Xtream '+(source.type==='series'?'Seriale':source.type==='live'?'TV':'Filmy'),
            function(){TV.xtream.openItem(source);});
          b.dataset.xtreamId=source.id;
          host.appendChild(b);
        });
        var empty=host.querySelector('.dnone');
        if(empty)empty.textContent='Brak w wybranych serwisach VOD';
        if(TV.view()==='details')TV.rebuild();
      }
      showSources(existing);
      TV.titleSources.forTmdb(Object.assign({media_type:it.tmdb.type},d)).then(showSources);
    }
""")
p.write_text(s,encoding='utf-8')
# Provider browse visual enrichment (existing archive lacks IMDb but has rating + cover).
p=A/'vod-xtream.js';s=p.read_text()
old="e.append(b,d);return e;"
assert s.count(old)==1
s=s.replace(old,"""if(item.icon && /^https?:\\/\\//.test(item.icon)){
  var cover=document.createElement('img');cover.className='dx-cover';
  cover.src=item.icon;cover.loading='lazy';cover.alt='';
  e.appendChild(cover);
 }
 if(item.rating){
  var rate=document.createElement('span');rate.className='dx-rating';
  rate.textContent='★ '+String(item.rating).slice(0,5);
  e.appendChild(rate);
 }
 e.append(b,d);return e;""")
p.write_text(s)
p=A/'vod-xtream.css';s=p.read_text()
s+='''\n/* Identity mapping: provider posters and numeric provider ratings. */\n#dc4i-xtream .dx-item{position:relative;justify-content:flex-end;min-height:234px;overflow:hidden;gap:5px;background:#10244c;}\n#dc4i-xtream .dx-cover{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:.68;z-index:0;}\n#dc4i-xtream .dx-item:has(.dx-cover){background:linear-gradient(0deg,#08102c,#10244c)}\n#dc4i-xtream .dx-item b,#dc4i-xtream .dx-item small{position:relative;z-index:1;overflow:hidden;text-overflow:ellipsis;text-shadow:0 2px 5px #000;}\n#dc4i-xtream .dx-item b{white-space:normal;max-height:72px;font-size:21px;}\n#dc4i-xtream .dx-item small{white-space:normal;font-size:16px;color:#e2edff;}\n#dc4i-xtream .dx-rating{position:absolute;z-index:1;right:10px;top:10px;padding:4px 8px;border-radius:7px;background:#061b39;color:#ffd17b;font-size:19px;}\n#search .xtream-result .xtream-score{position:absolute;z-index:1;top:12px;right:16px;background:#0a223e;color:#ffda81;padding:4px 9px;border-radius:7px;font-size:18px;}\n'''
p.write_text(s)
print('IDENTITY_MAPPING_V1217_PATCHED')
