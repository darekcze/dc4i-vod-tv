/* Default is deliberately unconfigured: no provider transport or archive probe. */
(function(){
 'use strict';var TV=window.TV,model=window.DC4IArchive;if(!TV||!model)return;
 function describe(entry,configured){
  var controller=model.create();var state=controller.offer({providerEnabled:configured===true,
   archiveHint:!!(entry&&entry.archiveFlag),providerId:'configured-provider',
   streamId:entry&&String(entry.channelId||''),start:entry&&entry.time&&entry.time.start,end:entry&&entry.time&&entry.time.end});
  var unverified=state.status==='unverified';
  return {status:state.status,playable:false,label:TV.S.uiLang==='en'?
   (unverified?'CatchUp unverified':'CatchUp unavailable'):(unverified?'CatchUp niezweryfikowane':'CatchUp niedostępne')};
 }
 TV.archive={describe:describe,request:function(entry,configured){TV.toast(describe(entry,configured).label);return false;}};
})();
