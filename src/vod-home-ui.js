/* Home integration: existing profile storage/navigation, metadata-only airings. */
(function(){
 'use strict';
 var TV=window.TV,model=window.DC4IHomeRails;if(!TV||!model)return;
 var layoutKey='homeRailsLayoutV1',cacheKey='homeRailsMetadataV1';
 function tr(pl,en){return TV.S.uiLang==='en'?en:pl;}
 function write(key,value){TV.store(key,value);if(JSON.stringify(TV.store(key))!==JSON.stringify(value))throw Error('storage unavailable');}
 var cache=model.createCache({read:function(){return TV.store(cacheKey);},write:function(v){write(cacheKey,v);}});
 function config(){var raw=TV.store(layoutKey)||{};return {active:raw.active!==false,
  order:model.configuration({order:raw.order}),enabled:model.configuration({enabled:raw.enabled})};}
 function save(value){try{write(layoutKey,value);TV.refresh();return true;}catch(e){TV.toast(tr('Nie można zapisać ustawień','Could not save settings'));return false;}}
 function rows(){
  var cfg=config();if(!cfg.active)return [];
  var source=typeof TV.homeCandidates==='function'?TV.homeCandidates():[],stamp=typeof TV.homeCandidatesStamp==='function'?TV.homeCandidatesStamp():0;
  if(source.length&&stamp>0)cache.put(source,stamp);
  var stored=cache.get(),age=Date.now()-stamp;
  // Persistence is optional: a quota/storage failure must never suppress live data.
  var useSource=source.length&&(!stamp||(age>=0&&age<90000000));
  var items=useSource?source:stored.items;
  var freshness=useSource?(!stamp?tr('Aktualność nieznana','Freshness unknown'):
   age>=3600000?tr('Nieaktualne metadane','Stale metadata'):tr('Metadane katalogu','Catalogue metadata')):
   stored.status==='stale'?tr('Nieaktualny cache','Stale cache'):stored.status==='fresh'?tr('Cache metadanych','Metadata cache'):'';
  var events=TV.epgMetadata&&TV.epgMetadata.homeEvents?TV.epgMetadata.homeEvents():[];
  var result=model.build({now:Date.now(),candidates:items,events:events,config:cfg,lang:TV.S.uiLang,
   pref:TV.personalized?TV.personalized.settings():{},history:TV.personalized?TV.personalized.history():[]});
  result.forEach(function(row){
   if(row.ranking==='profile'&&freshness)row.title+=' · '+freshness;
   row.items=row.items.map(function(item){return Object.assign({},item,{homeRail:true,homeRowId:row.id});});
  });
  if(!result.length)result=[{id:'home-status',title:tr('Twój Home','Your Home'),items:[{homeRail:true,kind:'status',
   title:tr('Brak propozycji dla bieżących ustawień','No suggestions for current settings'),
   meta:tr('Sprawdź sekcje Home lub poczekaj na dane','Check Home sections or wait for data')}]}];
  return result;
 }
 function reason(text){
  if(TV.S.uiLang!=='en')return text;
  return ({'Wieczorne familijne / romantyczne':'Evening family / romance','Familijne':'Family','Romantyczne':'Romance',
   'Komedia':'Comedy','Akcja':'Action','Dokument':'Documentary','Ulubiony gatunek':'Favourite genre',
   'Podobne do Twoich wyborów':'Similar to your choices','Wysoko oceniane':'Highly rated','Nowa produkcja':'New release',
   'Dopasowanie do profilu':'Profile match'})[text]||text;
 }
 function card(item){
  var el=TV.el('div','card f home-rail-card'),pic=TV.el('div','pic'),title=TV.el('b','ttl'),caption=TV.el('div','cap');
  el.homeRailRow=item.homeRowId||'home-status';
  el.homeRailKey=item.kind==='title'?'title:'+item.tmdb.type+':'+item.tmdb.id:item.kind==='airing'?JSON.stringify(['airing',item.channelId,item.start,item.end,item.source]):'status';
  el.item=item;
  el.setAttribute('translate','no');title.textContent=item.title||'';pic.appendChild(title);el.appendChild(pic);
  if(item.kind==='title'){
   var loaded=TV.homeCandidates().find(function(x){return x.tmdb&&x.tmdb.id===item.tmdb.id&&x.tmdb.type===item.tmdb.type;});
   el.item=Object.assign({},loaded||{},item);
   if(loaded&&/^https:\/\/image\.tmdb\.org\//.test(loaded.img||'')){var img=document.createElement('img');img.src=loaded.img;img.alt='';img.loading='lazy';pic.appendChild(img);}
   caption.textContent='TMDB '+item.vote_average+'/10 · '+tr('Dopasowanie ','Match ')+item.recoScore+'/100 · '+reason(item.recoReason);
   el.onok=function(){TV.itemOk(Object.assign({},loaded||{},item));};
  }else if(item.kind==='airing'){
   caption.textContent=new Date(item.start).toLocaleString(TV.S.uiLang==='en'?'en-GB':'pl-PL')+' · '+item.source+' · '+(item.freshness==='stale'?tr('Nieaktualne','Stale'):item.freshness==='fresh'?tr('Aktualne','Fresh'):tr('Aktualność nieznana','Freshness unknown'))+' · '+tr('Metadane; odtwarzanie niezweryfikowane','Metadata; playback unverified');
   el.onok=function(){TV.toast(caption.textContent);};
  }else{caption.textContent=item.meta||'';el.onok=function(){TV.homeRails.openSettings();};}
  el.appendChild(caption);return el;
 }
 var panel=TV.el('main','home-layout');panel.hidden=true;panel.setAttribute('translate','no');document.body.appendChild(panel);
 var controls=[],selected=0;
 function render(){
  panel.innerHTML='';controls=[];var cfg=config();
  var heading=TV.el('h1','');heading.textContent=tr('Sekcje Home','Home sections');panel.appendChild(heading);
  var hint=TV.el('p','');hint.textContent=tr('OK: włącz/wyłącz. Lewo/prawo: przesuń sekcję. Wstecz: wróć.','OK: toggle. Left/right: move section. Back: return.');panel.appendChild(hint);
  function button(text,fn,index){var el=TV.el('div','f home-layout-row');el.textContent=text;el.dataset.index=String(index);el.onok=fn;controls.push([el]);panel.appendChild(el);}
  button(tr('Wróć','Back'),function(){TV.closeView();},0);
  button(tr('Własne sekcje: ','Custom sections: ')+(cfg.active?tr('Włączone','On'):tr('Wyłączone','Off')),function(){cfg.active=!cfg.active;save(cfg);render();TV.rebuild(selected,0);},1);
  cfg.order.forEach(function(id,i){var label=model.labels[id][TV.S.uiLang==='en'?1:0];button((i+1)+'. '+label+' · '+
   (cfg.enabled.indexOf(id)>=0?tr('Włączone','On'):tr('Wyłączone','Off')),function(){
    var index=cfg.enabled.indexOf(id);if(index>=0)cfg.enabled.splice(index,1);else cfg.enabled.push(id);
    save(cfg);render();TV.rebuild(selected,0);
   },i+2);});
 }
 TV.addView('home-layout',{nav:function(){return controls;},show:function(){selected=0;panel.hidden=false;render();},
  hide:function(){panel.hidden=true;},back:function(){TV.closeView();return true;},
  onFocus:function(el){selected=Number(el.dataset.index)||0;if(el.scrollIntoView)el.scrollIntoView({block:'nearest'});},
  keydown:function(ev){if((ev.keyCode!==37&&ev.keyCode!==39)||selected<2)return false;
   var cfg=config(),i=selected-2,j=Math.max(0,Math.min(cfg.order.length-1,i+(ev.keyCode===39?1:-1)));
   if(i!==j){var id=cfg.order.splice(i,1)[0];cfg.order.splice(j,0,id);if(save(cfg))selected=j+2;render();TV.rebuild(selected,0);}return true;}
 });
 TV.addSetting({key:'homeRailsLayout',title:tr('Home: sekcje i kolejność','Home: sections and order'),
  hint:tr('Ustawienia bieżącego profilu','Current profile settings'),opts:[['edit',tr('Konfiguruj','Configure')]]},'');
 function captureFocus(){var el=document.querySelector('.focus');return el&&el.homeRailKey?{key:el.homeRailKey,row:el.homeRailRow}:null;}
 function restoreFocus(saved){
  if(!saved||typeof TV.focusHomeCard!=='function')return;
  var cards=[].slice.call(document.querySelectorAll('.home-rail-card'));
  var target=cards.find(function(el){return el.homeRailKey===saved.key&&el.homeRailRow===saved.row;})||
    cards.find(function(el){return el.homeRailKey===saved.key;})||cards.find(function(el){return el.homeRailRow===saved.row;});
  if(target)TV.focusHomeCard(target);
 }
 TV.homeRails={captureFocus:captureFocus,restoreFocus:restoreFocus,rows:rows,card:card,config:config,enabled:function(){return config().active;},openSettings:function(){TV.openView('home-layout');}};
 // Reclassify now/upcoming/missed and cache age without any network requests.
 setInterval(function(){if(TV.view()==='home'&&TV.homeRails.enabled())TV.refresh();},60000);
 TV.refresh();
})();
