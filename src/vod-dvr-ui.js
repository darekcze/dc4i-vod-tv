/* Informational capability only. No backend, scheduler timer or record action. */
(function(){
 'use strict';var TV=window.TV,model=window.DC4IDvr;if(!TV||!model)return;
 var controller=model.create();
 function label(){return TV.S.uiLang==='en'?'DVR unavailable — recording backend unverified':'DVR niedostępne — backend nagrywania niezweryfikowany';}
 TV.dvr={capability:function(){return controller.capability();},explain:function(){TV.toast(label());}};
 TV.addSetting({key:'dvrStatus',title:TV.S.uiLang==='en'?'DVR: availability':'DVR: dostępność',
  hint:TV.S.uiLang==='en'?'Browsing works without a recording service':'Przeglądanie działa bez serwera nagrywania',
  opts:[['info',TV.S.uiLang==='en'?'Unavailable':'Niedostępne']]},'');
})();
