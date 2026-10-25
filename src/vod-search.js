// DC4I VOD TV 1.1.1: region-aware search with explicit streaming availability.
// "Dostępne" means TMDB lists an offer in selected country (flatrate/free/ads).
// No streaming availability never means content can be legally streamed elsewhere.
(function () {
  'use strict';
  var TV = window.TV, esc = TV.esc;
  var $ = function (id) { return document.getElementById(id); };
  var tr = function (pl, en) { return TV.S.uiLang === 'en' ? en : pl; };
  var ROOT = TV.el('div', '', '<div class="sq"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5 21 21"/></svg>' +
    '<span id="sqText"></span><i class="caret"></i></div><span id="sxclose" class="f" title="' + tr('Zamknij','Close') + '">&#10005;</span><div id="skb"></div><div id="sfilters"></div><div id="syt"></div><h3 id="sresTitle"></h3><div id="sres" class="strip"></div>');
  ROOT.id = 'search'; ROOT.hidden = true; document.body.appendChild(ROOT);
  var q = '', sequence = 0, timer = null, results = [], filter = 'available';
  var cache = TV.store('vodAvailability_v111') || {};
  var MAX = 16, TTL = 6 * 60 * 60 * 1000;
  var keyRows = ['abcdefghijklm', 'nopqrstuvwxyz', '1234567890'];
  function button(label, cls, fn) {
    var b = TV.el('span','skey f' + (cls ? ' ' + cls : ''),esc(label));
    b.onok = fn; return b;
  }
  keyRows.forEach(function(row, idx) {
    var line = TV.el('div','skrow');
    row.split('').forEach(function(ch) {line.appendChild(button(ch,'',function(){insert(ch);}));});
    if(idx===2) {
      line.appendChild(button(tr('Spacja','Space'),'wide',function(){insert(' ');}));
      line.appendChild(button('⌫','wide',function(){setQ(q.slice(0,-1));}));
      line.appendChild(button(tr('Wyczyść','Clear'),'wide',function(){setQ('');}));
    }
    $('skb').appendChild(line);
  });
  var toggles = [
    {mode:'available', label:tr('Dostępne w kraju','Streaming here')},
    {mode:'other', label:tr('Pozostałe','Other titles')},
    {mode:'all', label:tr('Wszystkie','All titles')}
  ], filterEls = [];
  toggles.forEach(function(item) {
    var el = TV.el('span','schip f vod-filter',esc(item.label));
    el.onok = function() {
      filter = item.mode; draw(); renderFilters();
    };
    filterEls.push(el); $('sfilters').appendChild(el);
  });
  function renderFilters() {
    filterEls.forEach(function(el, i) {el.classList.toggle('selected', toggles[i].mode === filter);});
  }
  renderFilters();
  var yt = TV.el('span','schip f');
  yt.onok = function() {
    TV.launch('youtube.leanback.v4', {contentTarget:'https://www.youtube.com/tv#/search?q='+encodeURIComponent(q.trim())});
  };
  $('syt').appendChild(yt);
  $('sxclose').onok = function() {TV.closeView();};
  function insert(ch) {if (q.length < 60) setQ(q+ch);}
  function setQ(v) {
    q = v; $('sqText').textContent=q || tr('Szukaj filmów i seriali','Search movies and shows');
    $('sqText').className=q ? '' : 'ph';
    yt.innerHTML='<b>&#9654;</b> '+tr('Szukaj w YouTube','Search YouTube')+(q.trim() ? ': '+esc(q.trim()) : '');
    clearTimeout(timer);timer=setTimeout(search,480);
  }
  function getType(item) {return item.media_type || (item.title?'movie':'tv');}
  function getKey(item) {return TV.C.REGION+':'+getType(item)+':'+item.id;}
  function providerInfo(item) {
    var k=getKey(item), c=cache[k];
    if (c && Date.now()-c.checked<TTL) return Promise.resolve(c);
    return TV.tmdb(getType(item)+'/'+item.id+'/watch/providers').then(function(d) {
      var region=(d.results || {})[TV.C.REGION] || {};
      var offers=(region.flatrate||[]).concat(region.free||[],region.ads||[]);
      var seen={}, names=[];
      offers.forEach(function(p) {if(p.provider_name && !seen[p.provider_name]) {seen[p.provider_name]=1;names.push(p.provider_name);}});
      c={checked:Date.now(),available:names.length>0,names:names,rent:!!((region.rent||[]).length || (region.buy||[]).length)};
      cache[k]=c;
      var keys=Object.keys(cache);
      if(keys.length>160) keys.sort(function(a,b){return cache[a].checked-cache[b].checked;}).slice(0,keys.length-160).forEach(function(id){delete cache[id];});
      TV.store('vodAvailability_v111',cache);
      return c;
    },function() {return {checked:Date.now(),unknown:true,available:false,names:[]};});
  }
  function validateAll(items,seq) {
    var answers=new Array(items.length), cursor=0;
    function worker() {
      var i=cursor++;
      if(i>=items.length || seq!==sequence) return Promise.resolve();
      return providerInfo(items[i]).then(function(info) {
        answers[i]={item:items[i],info:info};
        return worker();
      });
    }
    return Promise.all([worker(),worker(),worker(),worker()]).then(function(){return answers.filter(Boolean);});
  }
  function search() {
    var term=q.trim(), seq=++sequence;
    $('sresTitle').textContent=tr('Sprawdzam dostępność w polskim VOD…','Checking streaming availability…');
    $('sres').innerHTML='';
    var req=term.length<2?TV.tmdb('trending/all/day'):TV.tmdb('search/multi','&include_adult=false&query='+encodeURIComponent(term));
    req.then(function(r) {
      if(seq!==sequence)return;
      var items=(r.results||[]).filter(function(m){return getType(m)!=='person' && (m.backdrop_path||m.poster_path);}).slice(0,MAX);
      if(!items.length) {results=[];draw();return;}
      return validateAll(items,seq).then(function(available) {
        if(seq!==sequence)return;
        results=available;draw();
      });
    }).catch(function(){
      if(seq===sequence) {results=[];$('sresTitle').textContent=tr('Nie udało się wyszukać. Sprawdź sieć.','Search failed; check your connection.');}
    });
  }
  function regionLabel() {return TV.C.REGION==='PL'?tr('w Polsce','in Poland'):tr('w kraju: ','in country: ')+TV.C.REGION;}
  function draw() {
    var list=results.filter(function(r) {
      return filter==='all' || (filter==='available' && r.info.available) ||
        (filter==='other' && !r.info.available);
    });
    var available=results.filter(function(r){return r.info.available;}).length;
    var other=results.length-available;
    var status=tr('Dostępne ','Available ')+regionLabel()+': '+available+'   ·   '+
      tr('Pozostałe: ','Others: ')+other;
    $('sresTitle').textContent=results.length ? status :
      tr('Brak znalezionych tytułów','No titles found');
    if(!list.length && results.length && filter==='available')
      $('sresTitle').textContent=tr('Brak ofert streamingu '+regionLabel()+'. Wybierz „Pozostałe”.',
         'No streaming offers '+regionLabel()+'. Choose “Others”.');
    var strip=$('sres');strip.innerHTML='';strip.style.transform='';
    list.forEach(function(r) {
      var item=TV.fromTmdb(r.item);
      var card=TV.card(item);
      card.onok=function(){ROOT.hidden=true;TV.itemOk(item);};
      var badge=TV.el('div','swhere vod-status');
      if(r.info.unknown) badge.textContent=tr('Nie potwierdzono dostępności','Availability could not be verified');
      else if(r.info.available) badge.textContent=tr('W VOD: ','Streaming: ')+r.info.names.slice(0,3).join(' · ');
      else badge.textContent=tr('Brak w wybranych serwisach','Not available in selected services');
      card.appendChild(badge);strip.appendChild(card);
    });
    if(TV.view()==='search')TV.rebuild();
  }
  TV.addView('search',{
    nav:function(){
      return [[$('sxclose')]].concat([].slice.call(ROOT.querySelectorAll('.skrow')).map(function(r){return [].slice.call(r.children);}))
        .concat([filterEls, [yt], [].slice.call($('sres').children)]);
    },
    show:function(){ROOT.hidden=false;if(!results.length)setQ(q);TV.rebuild(1,0);},
    hide:function(){ROOT.hidden=true;sequence++;clearTimeout(timer);},
    keydown:function(e){
      if(e.ctrlKey||e.metaKey||e.altKey)return false;
      if(e.key && e.key.length===1 && /[\w ]/.test(e.key))insert(e.key.toLowerCase());
      else if(e.keyCode===8 && q)setQ(q.slice(0,-1));
      else return false;
      return true;
    },
    onFocus:function(el,pos){if(el.parentNode.id==='sres')el.parentNode.style.transform='translateX('+-Math.max(0,el.offsetLeft-(pos.c?40:0))+'px)';}
  });
  TV.addTab(tr('Szukaj','Search'),'search');
})();
