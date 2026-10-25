/* No fetch, iframe, chart artwork or copied ranking data. */
(function(){'use strict';var TV=window.TV,api=window.DC4IChartLinks;if(!TV||!api)return;
 var key='dc4iChartLinksV1',panel=TV.el('main','chart-links'),controls=[],selected='back',generation=0,pending=false,timer=null;
 panel.hidden=true;document.body.appendChild(panel);
 function tr(pl,en){return TV.S.uiLang==='en'?en:pl;}
 function prefs(){try{var p=TV.store(key);return p===null||p===undefined?{region:'poland',category:'film'}:api.resolve(p)?{region:p.region,category:p.category}:null;}catch(e){return null;}}
 function focus(){if(TV.view()==='chart-links')TV.rebuild(Math.max(0,controls.findIndex(function(r){return r[0].dataset.key===selected;})),0);}
 function save(p){try{TV.store(key,p);var value=prefs();if(!value||value.region!==p.region||value.category!==p.category)throw Error();}catch(e){TV.toast(tr('Nie zapisano wyboru','Selection not saved'));}render();focus();}
 function stop(){generation++;pending=false;if(timer!==null)clearTimeout(timer);timer=null;}
 function launch(){
  var p=prefs(),url=api.resolve(p);if(!api.allowed(url)){TV.toast(tr('Nieobsługiwany wybór','Unsupported selection'));return;}
  if(pending)return;
  if(!window.PalmSystem||typeof TV.luna!=='function'){TV.toast(tr('Otwieranie zewnętrznej przeglądarki jest niedostępne','External browser opening is unavailable'));focus();return;}
  pending=true;var token=++generation;TV.toast(tr('Wysyłanie prośby o otwarcie przeglądarki','Requesting external browser opening'));
  function finish(result){if(token!==generation)return;stop();if(TV.view()!=='chart-links')return;
   TV.toast(result===true?tr('Przeglądarka przyjęła żądanie; zawartość strony niezweryfikowana','Browser accepted request; page content is unverified'):result===false?tr('Nie udało się otworzyć przeglądarki','Could not open browser'):tr('Brak potwierdzenia otwarcia przeglądarki','Browser opening was not confirmed'));focus();}
  timer=setTimeout(function(){finish(null);},8000);
  try{Promise.resolve(TV.luna('com.webos.applicationManager/launch',{id:'com.webos.app.browser',params:{target:url,fullMode:true}})).then(function(r){finish(r&&r.returnValue===true?true:false);},function(){finish(false);});}catch(e){finish(false);}
 }
 function render(){panel.innerHTML='';controls=[];var h=TV.el('h1','');h.textContent=tr('Netflix: oficjalne rankingi tygodniowe — linki','Netflix: official weekly charts — links');panel.appendChild(h);
  var hint=TV.el('p','');hint.textContent=tr('Otwiera zewnętrzną stronę. Brak zintegrowanego źródła rankingów; prawa do ich kopiowania niezweryfikowane. Trendy TMDB są osobną estymacją popularności, nie rankingiem Netflix.','Opens an external page. No integrated chart feed; redistribution rights unverified. TMDB trending is a separate popularity estimate, not a Netflix ranking.');panel.appendChild(hint);
  function button(k,text,fn){var el=TV.el('div','f chart-control');el.dataset.key=k;el.textContent=text;el.onok=fn;controls.push([el]);panel.appendChild(el);}
  var p=prefs();button('back',tr('Wróć','Back'),function(){TV.closeView();});
  button('region',tr('Region: ','Region: ')+(p?(p.region==='poland'?tr('Polska','Poland'):tr('Świat','Global')):tr('Nieobsługiwany','Unsupported')),function(){save({region:p&&p.region==='poland'?'global':'poland',category:p?p.category:'film'});});
  button('category',tr('Kategoria: ','Category: ')+(p?(p.category==='film'?tr('Filmy','Films'):tr('Seriale','TV')):tr('Nieobsługiwana','Unsupported')),function(){save({region:p?p.region:'poland',category:p&&p.category==='film'?'tv':'film'});});
  button('open',tr('Otwórz oficjalny ranking tygodniowy','Open official weekly chart'),launch);
 }
 TV.addView('chart-links',{nav:function(){return controls;},show:function(){stop();selected='back';panel.hidden=false;render();},hide:function(){stop();panel.hidden=true;},back:function(){TV.closeView();return true;},onFocus:function(el){selected=el.dataset.key;if(el.scrollIntoView)el.scrollIntoView({block:'nearest'});}});
 TV.addSetting({key:'chartLinks',title:tr('Rankingi tygodniowe: oficjalne linki','Weekly charts: official links'),hint:tr('Netflix · zewnętrzna strona, bez źródła danych','Netflix · external page, no data feed'),opts:[['edit',tr('Konfiguruj','Configure')]]},'');
 TV.chartLinks={feedEnabled:false,rightsStatus:'unverified',openSettings:function(){TV.openView('chart-links');}};
 window.addEventListener('focus',focus);
})();
