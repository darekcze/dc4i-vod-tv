/* User-triggered local preferences text export/import. Never enumerates storage. */
(function(){'use strict';var TV=window.TV,api=window.DC4IMetadataBackup;if(!TV||!api)return;
 var model=api.create({profile:function(){return String(TV.P&&TV.P.prefix||'');},read:function(k){return TV.backupRead(k);},write:function(k,v){TV.backupWrite(k,v);}}),section='home',controls=[],selected=0;
 function tr(pl,en){return TV.S.uiLang==='en'?en:pl;}
 var panel=TV.el('main','metadata-backup'),text=TV.el('textarea','f backup-text'),status=TV.el('p','backup-preview');panel.hidden=true;text.maxLength=16384;text.setAttribute('aria-label','Preferences JSON');document.body.appendChild(panel);
 function fieldLabel(k){return ({active:tr('Własne sekcje','Custom sections'),order:tr('Kolejność','Order'),enabled:section==='home'?tr('Widoczne sekcje','Visible sections'):tr('Przypomnienia','Reminders'),quiet:tr('Godziny ciszy','Quiet hours'),start:tr('Początek ciszy','Quiet start'),end:tr('Koniec ciszy','Quiet end'),region:tr('Region','Region'),category:tr('Kategoria','Category')})[k];}
 function valueLabel(k,v){if(typeof v==='boolean')return v?tr('Włączone','On'):tr('Wyłączone','Off');
  if(k==='start'||k==='end')return ('0'+Math.floor(v/60)).slice(-2)+':'+('0'+v%60).slice(-2);
  if(Array.isArray(v))return v.length?v.map(function(id){var labels=window.DC4IHomeRails&&window.DC4IHomeRails.labels;return labels&&labels[id]?labels[id][TV.S.uiLang==='en'?1:0]:id;}).join(', '):tr('Brak','None');
  return ({poland:tr('Polska','Poland'),global:tr('Świat','Global'),film:tr('Filmy','Films'),tv:tr('Seriale','TV')})[v];}
 function previewLabel(r){return tr('Podgląd zmian (przed → po):','Change preview (before → after):')+'\n'+r.changes.map(function(change){var before=change.before.state==='value'?valueLabel(change.field,change.before.value):change.before.state==='missing'?tr('Nie zapisano','Not saved'):tr('Nieprawidłowa wartość (ukryta)','Invalid value (hidden)');
  return fieldLabel(change.field)+': '+before+' → '+valueLabel(change.field,change.after)+(change.changed?'':tr(' (bez zmian)',' (unchanged)'));}).join('\n');}
 function report(ok){status.textContent=ok?tr('Potwierdzono zapis wybranej sekcji. Pozostałe dane bez zmian.','Selected section write confirmed. Other data unchanged.'):tr('Nie potwierdzono zapisu. Sprawdź dane i przygotuj podgląd ponownie.','Write not confirmed. Check data and prepare preview again.');}
 function render(){panel.innerHTML='';controls=[];var title=TV.el('h1','');title.textContent=tr('Kopia ustawień — tylko metadane','Preferences backup — metadata only');panel.appendChild(title);
  var hint=TV.el('p','');hint.textContent=tr('Tylko układ Home, cisza przypomnień i wybór rankingów. Bez kont, list, historii i tytułów. Import jednej sekcji po podglądzie; cofnięcie tylko w tej sesji, jeśli nic się nie zmieniło.','Home layout, reminder preferences and chart selection only. No accounts, playlists, histories or titles. Import one section after preview; undo within this session only if unchanged.');panel.appendChild(hint);
  function button(label,fn){var el=TV.el('div','f backup-control');el.textContent=label;el.onok=fn;controls.push([el]);panel.appendChild(el);}
  button(tr('Wróć','Back'),function(){TV.closeView();});
  button(tr('Eksportuj zapisane ustawienia do pola','Export saved preferences into text field'),function(){model.invalidate();try{text.value=model.exportText();status.textContent=tr('Skopiuj tekst, aby zachować kopię. Nie wysłano danych.','Copy the text to retain a backup. No data was sent.');}catch(e){status.textContent=tr('Brak poprawnych zapisanych ustawień do eksportu','No valid saved preferences to export');}});
  button(tr('Sekcja importu: ','Import section: ')+section,function(){section=['home','reminders','charts'][(['home','reminders','charts'].indexOf(section)+1)%3];model.invalidate();status.textContent='';render();TV.rebuild(selected,0);});
  text.onok=function(){text.focus();};controls.push([text]);panel.appendChild(text);
  button(tr('Sprawdź i pokaż podgląd','Validate and preview'),function(){var r=model.prepare(text.value,section);status.textContent=r.ok?previewLabel(r):tr('Odrzucono dane lub nie można odczytać bieżącej sekcji','Data rejected or current section unreadable');});
  button(tr('Zastosuj ostatni podgląd','Apply last preview'),function(){report(model.apply().ok);});
  button(tr('Cofnij ostatni import','Undo last import'),function(){report(model.rollback().ok);});panel.appendChild(status);
 }
 text.addEventListener('input',function(){model.invalidate();status.textContent='';});
 TV.addView('metadata-backup',{nav:function(){return controls;},show:function(){model.invalidate();text.value='';status.textContent='';selected=0;panel.hidden=false;render();},hide:function(){model.invalidate();text.value='';panel.hidden=true;},back:function(){if(document.activeElement===text){text.blur();return true;}TV.closeView();return true;},onFocus:function(el){selected=Math.max(0,controls.findIndex(function(r){return r[0]===el;}));if(el.scrollIntoView)el.scrollIntoView({block:'nearest'});},keydown:function(e){if(document.activeElement===text){if(e.keyCode===461||e.keyCode===27){text.blur();return true;}return true;}return false;}});
 TV.addSetting({key:'metadataBackup',title:tr('Kopia wybranych ustawień profilu','Selected profile preferences backup'),hint:tr('Eksport/import tekstu bez kont i historii','Text export/import without accounts or history'),opts:[['edit',tr('Otwórz','Open')]]},'');
 TV.metadataBackup={openSettings:function(){TV.openView('metadata-backup');}};
})();
