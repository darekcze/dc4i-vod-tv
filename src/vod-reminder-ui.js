/* In-app foreground reminders only; no Luna/system toast, wake or background API. */
(function(){
 'use strict';var TV=window.TV,api=window.DC4IReminders;if(!TV||!api)return;
 var model=api.create({read:function(k){if(typeof TV.readReminderStorage!=='function')throw Error('Reminder storage unavailable');return TV.readReminderStorage(k);},write:function(k,v){TV.store(k,v);}});
 function tr(pl,en){return TV.S.uiLang==='en'?en:pl;}
 function foreground(){return document.visibilityState==='visible'&&typeof document.hasFocus==='function'&&document.hasFocus();}
 var panel=TV.el('main','reminder-settings');panel.hidden=true;panel.setAttribute('translate','no');document.body.appendChild(panel);
 var controls=[],selectedKey='back',selectedIndex=0;
 function focus(){var index=controls.findIndex(function(row){return row[0].dataset.key===selectedKey;});
  TV.rebuild(index>=0?index:Math.max(0,Math.min(selectedIndex,controls.length-1)),0);}
 function time(n){return ('0'+Math.floor(n/60)).slice(-2)+':'+('0'+n%60).slice(-2);}
 function change(values){var result=model.setPrefs(values);if(!result.ok)TV.toast(tr('Nie zapisano ustawień','Settings not saved'));render();focus();}
 function shift(key,delta){var p=model.prefs(),value={};value[key]=(p[key]+delta+1440)%1440;change(value);}
 function render(){
  panel.innerHTML='';controls=[];
  var heading=TV.el('h1','');heading.textContent=tr('Przypomnienia w aplikacji','In-app reminders');panel.appendChild(heading);
  var hint=TV.el('p','');hint.textContent=tr('Tylko widoczna aplikacja na pierwszym planie. Godziny ciszy według lokalnego czasu TV. OK: zmień/anuluj; lewo/prawo: godzina.','Visible foreground app only. Quiet hours use local TV time. OK: change/cancel; left/right: hour.');panel.appendChild(hint);
  function button(key,text,action){var el=TV.el('div','f reminder-control');el.dataset.key=key;el.textContent=text;el.onok=action;controls.push([el]);panel.appendChild(el);}
  var p=model.prefs();
  if(p.storageError){var error=TV.el('p','');error.textContent=tr('Nie można odczytać preferencji; powiadomienia wstrzymane','Preferences unreadable; notifications paused');panel.appendChild(error);}
  button('back',tr('Wróć','Back'),function(){TV.closeView();});
  button('enabled',tr('Przypomnienia: ','Reminders: ')+(p.enabled?tr('Włączone','On'):tr('Wyłączone','Off')),function(){change({enabled:!p.enabled});});
  button('quiet',tr('Cisza: ','Quiet hours: ')+(p.quiet?tr('Włączona','On'):tr('Wyłączona','Off')),function(){change({quiet:!p.quiet});});
  button('start',tr('Początek ciszy: ','Quiet start: ')+time(p.start),function(){shift('start',60);});
  button('end',tr('Koniec ciszy: ','Quiet end: ')+time(p.end)+(p.start===p.end?tr(' (cała doba)',' (all day)'):''),function(){shift('end',60);});
  var result=model.list();
  result.items.slice(0,100).forEach(function(item){var when=new Date(item.start).toLocaleString(TV.S.uiLang==='en'?'en-GB':'pl-PL');
   button('reminder:'+item.key,when+' · '+item.title+' · '+item.channel+' · '+tr('OK: anuluj','OK: cancel'),function(){
    if(!model.cancel(item.key).ok)TV.toast(tr('Nie anulowano przypomnienia','Reminder not cancelled'));render();focus();
   });});
  if(!result.ok||!result.items.length||result.items.length>100){var note=TV.el('p','');note.textContent=!result.ok?tr('Nie można odczytać przypomnień','Could not read reminders'):
   result.items.length>100?tr('Pokazano pierwsze 100; pozostałe pozostają zapisane','Showing first 100; remaining reminders are preserved'):tr('Brak zapisanych przypomnień','No saved reminders');panel.appendChild(note);}
 }
 function run(){
  var result=model.tick({foreground:foreground()});
  if(result.delivered.length){var names=result.delivered.slice(0,3).map(function(x){return x.title+' · '+x.channel;}).join('; ');
   TV.toast(tr('Teraz w TV: ','On TV now: ')+names+(result.delivered.length>3?' · +'+(result.delivered.length-3):''));}
  if((result.delivered.length||result.expired)&&TV.view()==='reminders'){render();focus();}
 }
 TV.addView('reminders',{nav:function(){return controls;},show:function(){panel.hidden=false;selectedKey='back';selectedIndex=0;render();},hide:function(){panel.hidden=true;},
  back:function(){TV.closeView();return true;},onFocus:function(el){selectedKey=el.dataset.key;selectedIndex=Math.max(0,controls.findIndex(function(r){return r[0]===el;}));if(el.scrollIntoView)el.scrollIntoView({block:'nearest'});},
  keydown:function(e){if((e.keyCode===37||e.keyCode===39)&&(selectedKey==='start'||selectedKey==='end')){shift(selectedKey,e.keyCode===39?60:-60);return true;}return false;}});
 TV.addSetting({key:'reminderSettings',title:tr('Przypomnienia: preferencje i lista','Reminders: preferences and list'),
  hint:tr('Tylko pierwszy plan, bez budzenia TV','Foreground only; does not wake TV'),opts:[['edit',tr('Konfiguruj','Configure')]]},'');
 TV.reminders={backgroundSupported:false,openSettings:function(){TV.openView('reminders');},add:function(event){var result=model.add(event);
  TV.toast(result.ok?(model.prefs().enabled?tr('Przypomnienie zapisane — tylko na pierwszym planie','Reminder saved — foreground only'):tr('Zapisano; przypomnienia są wyłączone','Saved; reminders are off')):tr('Przypomnienie nie zostało zapisane','Reminder not saved'));return result.ok;}};
 setInterval(run,60000);document.addEventListener('visibilitychange',run);window.addEventListener('focus',run);
})();
