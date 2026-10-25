/* Local metadata adapter only: no ingestion, storage, network or playback grants. */
(function(){
 'use strict';
 var TV=window.TV,model=window.DC4IRichEpg;
 if(!TV||!model)return;
 function tr(pl,en){return TV.S.uiLang==='en'?en:pl;}
 function create(options){
  options=options||{};
  var clock=options.now||Date.now,cache=model.createCache(options),source=null;
  function label(entry){
   return 'XMLTV · '+entry.snapshot.source+' · '+
    (entry.status==='fresh'?tr('Aktualne','Fresh'):tr('Nieaktualne','Stale'))+
    (entry.partial?' · '+tr('Niepełne','Partial'):'')+' · '+
    tr('Ścieżki audio/napisy niezweryfikowane','Audio/subtitle tracks unverified');
  }
  function providerLabel(){return tr('EPG dostawcy · aktualność nieznana',
    'Provider EPG · freshness unknown');}
  function guide(channel,provider){
   provider=Array.isArray(provider)?provider:[];
   var entry=cache.get(source),mapping=entry.snapshot&&channel&&model.mapChannel(
     {epg_channel_id:channel.epgId,title:channel.title},entry.snapshot.channels);
   if(mapping&&mapping.status==='mapped'){
    var now=clock(),events=model.timeline(entry.snapshot,mapping.channelId,now,now+10*86400000);
    if(events.length)return {events:events.map(function(e){
     return {title:e.title,description:e.description,time:{start:e.start,end:e.end},playable:false};
    }),label:label(entry)};
   }
   return {events:provider,label:provider.length?providerLabel():''};
  }
  function renderDetails(host,title,provider){
   // Caller owns clearing and selection/race guards. No innerHTML from source data.
   function line(text){var el=document.createElement('div');el.className='depg-metadata';el.setAttribute('translate','no');
    el.textContent=text;host.appendChild(el);}
   if(Array.isArray(provider)&&provider.length)line(providerLabel()+' · '+
     tr('Dopasowanie tytułu niezweryfikowane','Title match unverified'));
   var entry=cache.get(source);if(!entry.snapshot||typeof title!=='string'||!title.trim())return;
   var now=clock(),query=title.trim().toLocaleLowerCase();
   entry.snapshot.events.filter(function(e){return e.end>now&&e.start<now+10*86400000&&
     e.title.trim().toLocaleLowerCase()===query;}).slice(0,8).forEach(function(e){
    line(e.title+' · '+e.channelId+' · '+new Date(e.start).toLocaleString(TV.S.uiLang==='en'?'en-GB':'pl-PL')+
     ' · '+label(entry)+' · '+tr('Dopasowanie tytułu niezweryfikowane','title match unverified'));
   });
  }
  return {guide:guide,renderDetails:renderDetails,
   // Explicit adapter boundary for a locally supplied normalized snapshot. No public loader.
   acceptLocal:function(snapshot){var result=cache.put(snapshot);if(result.accepted)source=snapshot.source;return result;},
   clear:function(){source=null;cache.clear();}};
 }
 TV.epgMetadata=create();TV.epgMetadata.create=create;
})();
