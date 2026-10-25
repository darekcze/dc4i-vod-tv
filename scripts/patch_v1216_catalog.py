#!/usr/bin/env python3
"""VODTV 1.2.16: fixed top nav, TV-independent playlist persistence and mixed search."""
from pathlib import Path
import json,re
R=Path(__file__).resolve().parents[1]
A=R/'build/dc4i-vodtv'
VERSION='1.2.16'
def edit(name,fn):
 p=A/name
 s=p.read_text(encoding='utf-8')
 t=fn(s)
 assert t!=s,name
 p.write_text(t,encoding='utf-8')

def menu(s):
 start=s.index('  <nav class="pill">')
 end=s.index('  </nav>',start)+len('  </nav>')
 new='''  <nav class="pill dc4i-top-navigation">
    <span class="tab f" data-tab="home">VOD</span>
    <span class="tab f" data-act="live">TV</span>
    <span class="tab f" data-xtream="all">IPTV</span>
    <span class="tab f" data-xtream="movie">Filmy</span>
    <span class="tab f" data-xtream="series">Seriale</span>
    <span class="tab f" data-view="search">Szukaj</span>
    <span class="tab f" data-tab="apps">Aplikacje</span>
  </nav>'''
 s=s[:start]+new+s[end:]
 assert s.count('1.2.15 · 25.10.2026')==1
 return s.replace('1.2.15 · 25.10.2026','1.2.16 · 25.10.2026')
edit('index.html',menu)

def app(s):
 anchor="    if (e.dataset.tab) return setView(e.dataset.tab);"
 assert s.count(anchor)==1
 s=s.replace(anchor,anchor+"\n    if (e.dataset.xtream) return TV.xtream.open(e.dataset.xtream);")
 assert "currentVersion: '1.2.15'" in s
 return s.replace("currentVersion: '1.2.15'","currentVersion: '1.2.16'")
edit('app.js',app)
edit('vod-version-check.js',lambda s:s.replace("var CURRENT_VERSION = '1.2.15';","var CURRENT_VERSION = '1.2.16';"))
def css(s):
 return s+'''
/* Exactly seven 1920x1080 remote-focused top tabs, no horizontal clipping. */
#top .dc4i-top-navigation {flex:none;gap:0;padding:5px;margin-right:10px;}
#top .dc4i-top-navigation .tab {padding:12px 14px;font-size:21px;margin:0 1px;white-space:nowrap;}
#top .dc4i-brand {max-width:205px;flex-shrink:0;}
#top .dc4i-brand img {max-width:195px;object-fit:contain;}
#top .avatar {margin-right:12px;flex-shrink:0;}
#top .icons {margin-right:6px;}
@media (max-width:1450px) {#top .dc4i-top-navigation .tab{font-size:19px;padding:10px 8px;}}
'''
edit('dc4i.css',css)

def xtream(s):
 # Existing key remains unchanged. Backup stays local, scoped to each user profile.
 old="var saved=TV.store(KEY)||[];"
 assert old in s
 s=s.replace(old,"""var BACKUP='dc4iXtreamAccountsBackupV1';
var saved=TV.store(KEY)||TV.store(BACKUP)||[];
// webOS update with unchanged application ID normally retains localStorage.
// If the primary key is missing, recover from this same-profile backup.
if(Array.isArray(saved) && saved.length && !(TV.store(KEY)||[]).length)TV.store(KEY,saved);
if(Array.isArray(saved) && saved.length && !(TV.store(BACKUP)||[]).length)TV.store(BACKUP,saved);""")
 s=s.replace("var library={}, selected='', records=[]","var library={}, selected=(saved.length?saved[0].id:''), records=[]")
 old=" try{TV.store(KEY,saved);return true;}"
 assert old in s
 s=s.replace(old,""" try {
  TV.store(KEY,saved);
  TV.store(BACKUP,saved);
  var verify=TV.store(KEY);
  return !!(Array.isArray(verify) && verify.length===saved.length &&
    verify.every(function(item,i){return item.id===saved[i].id;}));
 }""")
 s=s.replace('Aktualizacja aplikacji może usunąć te dane.','Aktualizacja tej samej aplikacji zachowuje te dane, o ile webOS nie usunie pamięci aplikacji. Eksport kopii zapasowej jest zalecany.')
 s=s.replace('  isLoading=false;msg(errorMsg(e));return false;','  isLoading=false;msg(errorMsg(e));return restoreCatalog().then(function(restored){if(restored){displayCategories();runSearch(true);}return restored;});')
 # Additional metadata from provider, never in the public IPK.
 old="icon:kind==='live'?(i.stream_icon||''):(i.cover||i.stream_icon||'')});"
 assert old in s
 s=s.replace(old,"""icon:kind==='live'?(i.stream_icon||''):(i.cover||i.stream_icon||''),
             rating:i.rating||i.rating_5based||'',tmdb:String(i.tmdb_id||i.tmdb||''),
             year:i.year||i.releaseDate||'',languageTag:/\\[(PL|POL|EN|ENG|UK|US|AU)\\]/i.exec(name+' '+(catmap[String(i.category_id)]||''))?.[1]||''});""")
 # IndexedDB cache for large catalogs, unlike localStorage's low quota.
 needle="function sync(force){"
 assert needle in s
 helper="""function catalogKey(){return String((TV.P&&TV.P.prefix)||'')+selected;}
function cacheDb(){
 return new Promise(function(resolve){
  if(!window.indexedDB)return resolve(null);
  var q=indexedDB.open('dc4i-vodtv-user-catalog-v1',1);
  q.onupgradeneeded=function(){if(!q.result.objectStoreNames.contains('catalogs'))q.result.createObjectStore('catalogs');};
  q.onsuccess=function(){resolve(q.result);};q.onerror=function(){resolve(null);};
 });
}
function restoreCatalog(){
 var a=account();if(!a)return Promise.resolve(false);
 return cacheDb().then(function(db){
  if(!db)return false;
  return new Promise(function(resolve){
   var tx=db.transaction('catalogs','readonly'),q=tx.objectStore('catalogs').get(catalogKey());
   q.onsuccess=function(){
    var item=q.result;
    if(item&&Array.isArray(item.records)&&item.accountId===a.id){
     library[selected]=item;records=item.records;categories=item.categories||[];resolve(true);
    }else resolve(false);
   };q.onerror=function(){resolve(false);};tx.oncomplete=function(){db.close();};
  });
 });
}
function persistCatalog(){
 var item=library[selected];if(!item)return;
 cacheDb().then(function(db){
  if(!db)return;
  try{
   var tx=db.transaction('catalogs','readwrite');
   tx.objectStore('catalogs').put({records:item.records,categories:item.categories,loadedAt:item.loadedAt,accountId:selected},catalogKey());
   tx.oncomplete=function(){db.close();};tx.onerror=function(){db.close();};
  }catch(e){db.close();}
 });
}
"""
 s=s.replace(needle,helper+needle)
 needle="  library[selected]={records:found,categories:categories,loadedAt:Date.now()};"
 assert needle in s
 s=s.replace(needle,needle+"\n  persistCatalog();")
 # opening tabs should switch mode, using the existing view with result lists.
 old="show:function(){root.hidden=false;redrawAccounts();if(!selected&&saved.length)selected=saved[0].id;"
 assert old in s
 s=s.replace(old,"show:function(mode){root.hidden=false;if(mode==='movie'||mode==='series'||mode==='live'||mode==='all'){$('type').value=mode;filter=mode;displayCategories();}redrawAccounts();if(!selected&&saved.length)selected=saved[0].id;")
 old="  else if(selected)sync(false);else msg('Dodaj playlistę Xtream.');TV.rebuild(0,0);},"
 assert old in s
 s=s.replace(old,"  else if(selected)restoreCatalog().then(function(ok){if(ok){displayCategories();runSearch(true);}else sync(false);});else msg('Dodaj playlistę Xtream.');TV.rebuild(0,0);},")
 # Nav when opened directly from search (not already cached) must remember kind.
 needle="TV.addTab(tr('IPTV','IPTV'),'xtream');"
 assert needle in s
 s=s.replace(needle,'// IPTV, Movies and Series tabs are installed in the static top menu.')
 needle=" sync:sync,search:runSearch,select:choose,open:function(){TV.openView('xtream');},"
 assert needle in s
 s=s.replace(needle,""" sync:sync,search:runSearch,select:choose,
 open:function(kind){TV.openView('xtream',kind||'all');},
 getRecords:function(){return records.slice();},
 searchCatalog:function(term,opts){
  var options=opts||{},query=norm(term),language=options.language||'all',mode=options.kind||'all';
  if(!query)return Promise.resolve([]);
  function match(x){
   if(mode==='live'&&x.type!=='live'||mode==='movie'&&x.type!=='movie'||mode==='series'&&x.type!=='series')return false;
   var tags=(x.title||'')+' '+(x.group||'');
   var pl=/\\[(?:PL|POL)\\]/i.test(tags),en=/\\[(?:EN|ENG|UK|US|AU)\\]/i.test(tags);
   if(language==='pl'&&!pl||language==='en'&&!en)return false;
   return norm(x.title).indexOf(query)>=0||norm(x.group).indexOf(query)>=0;
  }
  function result(){return records.filter(match).slice(0,80);}
  if(records.length)return Promise.resolve(result());
  return restoreCatalog().then(function(ok){return ok?result():sync(false).then(function(){return result();});});
 },
 openItem:function(i){selected=i.accountId||selected;TV.openView('xtream',i.type);choose(i);},""")
 return s
edit('vod-xtream.js',xtream)
# Existing view code uses TV.P, which is public as part of app state.
def metadata(s):
 j=json.loads(s);assert j['version']=='1.2.15'
 j['version']=VERSION
 return json.dumps(j,ensure_ascii=False,indent=2)+'\n'
edit('appinfo.json',metadata)
print('PATCHED_MENU_AND_XTREAM',VERSION)

def search_ui(s):
 # Use a single search screen for TMDB-selected VOD and user's own Xtream.
 s=s.replace('<div id="sfilters"></div>','<div id="sfilters"></div><div id="slangs"></div>')
 old="var q = '', sequence = 0, timer = null, results = [], filter = 'available';"
 assert old in s
 s=s.replace(old,"var q = '', sequence = 0, timer = null, results = [], xtResults = [], filter = 'all', language=TV.store('searchResultLanguageV1')||'pl';")
 start=s.index('  var toggles = [')
 end=s.index('  var externalButtons=[];',start)
 s=s[:start]+"""  var toggles = [
    {mode:'all', label:tr('Wszystkie','All')},
    {mode:'vod', label:'VOD'},
    {mode:'tv', label:'TV'},
    {mode:'iptv', label:'IPTV'},
    {mode:'movie', label:tr('Filmy','Movies')},
    {mode:'series', label:tr('Seriale','Series')}
  ], filterEls=[],langEls=[];
  toggles.forEach(function(item) {
    var el=TV.el('span','schip f vod-filter',esc(item.label));
    el.onok=function(){filter=item.mode;search();renderFilters();};
    filterEls.push(el);$('sfilters').appendChild(el);
  });
  [{id:'pl',label:tr('Polskie','Polish')},{id:'en',label:tr('Angielskie','English')},{id:'all',label:tr('Wszystkie języki','All languages')}].forEach(function(v){
    var b=TV.el('span','schip f language-filter',v.label);
    b.onok=function(){language=v.id;TV.store('searchResultLanguageV1',language);search();renderFilters();};
    langEls.push(b);$('slangs').appendChild(b);
  });
  function renderFilters() {
    filterEls.forEach(function(el,i){el.classList.toggle('selected',toggles[i].mode===filter);});
    langEls.forEach(function(el,i){el.classList.toggle('selected',['pl','en','all'][i]===language);});
  }
  renderFilters();
""" + s[end:]
 start=s.index('  function search() {')
 end=s.index("  TV.addView('search',{",start)
 replacement="""  function matchesLanguage(item,fromXtream) {
    if(language==='all')return true;
    if(!fromXtream) {
      // TMDB provider availability uses selected country. Original production language
      // is NOT the localized audio language, so keep Netflix/Prime titles visible.
      return true;
    }
    var tag=String(item.title||'')+' '+String(item.group||'');
    return language==='pl'?/\\[(?:PL|POL)\\]/i.test(tag):/\\[(?:EN|ENG|UK|US|AU)\\]/i.test(tag);
  }
  function search() {
    var term=q.trim(),seq=++sequence;
    results=[];xtResults=[];
    $('sresTitle').textContent=tr('Wyszukiwanie…','Searching…');
    $('sres').innerHTML='';
    var xtMode=filter==='tv'||filter==='iptv'?'live':filter==='movie'?'movie':filter==='series'?'series':'all';
    if(term.length>=2 && filter!=='vod' && TV.xtream && TV.xtream.getAccounts().length) {
      TV.xtream.searchCatalog(term,{kind:xtMode,language:language}).then(function(items){
        if(seq!==sequence)return;
        xtResults=(items||[]).filter(function(x){return matchesLanguage(x,true);});
        draw();
      },function(){if(seq===sequence)draw();});
    }
    if(filter==='tv'||filter==='iptv'||filter==='movie'||filter==='series') {
      draw();return;
    }
    var req=term.length<2?TV.tmdb('trending/all/day'):TV.tmdb('search/multi','&include_adult=false&query='+encodeURIComponent(term));
    req.then(function(r) {
      if(seq!==sequence)return;
      var items=(r.results||[]).filter(function(m){
        return getType(m)!=='person'&&(m.backdrop_path||m.poster_path)&&matchesLanguage(m,false);
      }).slice(0,MAX);
      if(!items.length){draw();return;}
      return validateAll(items,seq).then(function(available){
        if(seq!==sequence)return;
        results=available;draw();
      });
    }).catch(function(){if(seq===sequence)draw();});
  }
  function canonical(name) {
    return String(name||'').toLowerCase().replace(/\\[(pl|pol|en|eng|uk|us|au)\\]/g,'')
      .replace(/\\b(19|20)\\d{2}\\b/g,'').replace(/[^a-z0-9\\u00c0-\\u017f]+/g,' ').trim();
  }
  function draw() {
    var list=(filter==='vod'?results.filter(function(r){return r.info.available;}):results).slice(0,MAX);
    var countTmdb=list.length;
    var used={},chosen=[];
    list.forEach(function(r) {
      var key=getType(r.item)+':'+(r.item.id||'');
      used[key]=r;
      chosen.push({tmdb:r});
    });
    if(filter!=='vod')xtResults.forEach(function(x){
      var type=x.type==='series'?'tv':x.type==='movie'?'movie':'live';
      if(filter==='movie'&&type!=='movie'||filter==='series'&&type!=='tv')return;
      if((filter==='tv'||filter==='iptv')&&type!=='live')return;
      if(filter==='all'&&type==='live'&&chosen.filter(function(y){return y.xtream&&y.xtream.type==='live';}).length>=8)return;
      var mapped=x.tmdb&&used[type+':'+x.tmdb];
      if(!mapped) {
        mapped=chosen.some(function(e){
          if(!e.tmdb)return false;
          var a=e.tmdb.item;
          return getType(a)===type && canonical(a.title||a.name)===canonical(x.title);
        });
      }
      if(mapped)return;
      chosen.push({xtream:x});
    });
    chosen=chosen.slice(0,MAX);
    var available=results.filter(function(x){return x.info.available;}).length;
    $('sresTitle').textContent=chosen.length
      ?tr('Wyniki: ','Results: ')+chosen.length+'  ·  VOD: '+available+'  ·  Xtream: '+xtResults.length
      :tr('Brak w wybranych serwisach','Not available in selected services');
    var strip=$('sres');strip.innerHTML='';strip.style.transform='';
    chosen.forEach(function(entry){
      if(entry.tmdb) {
        var r=entry.tmdb,item=TV.fromTmdb(r.item),card=TV.card(item);
        card.onok=function(){ROOT.hidden=true;TV.itemOk(item);};
        var badge=TV.el('div','swhere vod-status');
        badge.textContent=r.info.unknown?tr('Dostępność niepotwierdzona','Availability unverified')
          :r.info.available?tr('W VOD: ','Streaming: ')+r.info.names.slice(0,3).join(' · ')
          :tr('Brak w wybranych serwisach','Not available in selected services');
        card.appendChild(badge);strip.appendChild(card);
      } else {
        var x=entry.xtream;
        var card=TV.el('div','card f xtream-result');
        var title=TV.el('b','ttl');title.textContent=x.title;
        var pic=TV.el('div','pic');
        if(x.icon && /^https?:\\/\\//.test(x.icon)){
          var img=document.createElement('img');img.src=x.icon;img.alt='';img.loading='lazy';pic.appendChild(img);
        }
        pic.appendChild(title);card.appendChild(pic);
        card.appendChild(TV.el('div','cap',TV.esc(({live:'TV',movie:'Film',series:'Serial'})[x.type]||x.type)));
        var source=TV.el('div','swhere vod-status');source.textContent='Xtream · '+(x.group||'');card.appendChild(source);
        card.onok=function(){ROOT.hidden=true;TV.xtream.openItem(x);};
        strip.appendChild(card);
      }
    });
    if(TV.view()==='search')TV.rebuild();
  }
"""
 s=s[:start]+replacement+s[end:]
 # Update filters nav and remove redundant dynamic tab.
 old=".concat([filterEls, [].slice.call($('sres').children), externalButtons]);"
 assert old in s
 s=s.replace(old,".concat([filterEls,langEls, [].slice.call($('sres').children), externalButtons]);")
 old="  TV.addTab(tr('Szukaj','Search'),'search');"
 assert old in s
 s=s.replace(old,"  // Search tab is declared explicitly in the main navigation.")
 # new default should match user country and stored filter
 return s
edit('features/search.js',search_ui)
edit('vod-external-search.css',lambda s:s+'''
/* 1.2.16: two separate filter bars under the search keyboard. */
#search #sfilters,#search #slangs {display:flex;gap:9px;align-items:center;margin:7px 0;flex-wrap:wrap;}
#search #sfilters .schip,#search #slangs .schip {font-size:20px;padding:10px 20px;margin-right:0;}
#search #sres {height:255px;min-height:255px;}
#search .xtream-result .pic {background:#14294b;}
''')
print('UNIFIED_SEARCH_FILTERS_PATCHED')
