/* Pure Home rows and caller-scoped metadata cache. No network or playback API. */
(function(root){
 'use strict';
 var engine=root.DC4IRecommender;
 var IDS=['now','today','week','missedToday','missedWeek','films','series','favourite','scifi','reality','family'];
 var GENRES={scifi:[878,10765],reality:[10764],family:[10751,10762]};
 var LABELS={now:['Teraz','Now'],today:['Jeszcze dzisiaj','Later today'],week:['Kolejne dni','Coming days'],
  missedToday:['Minęło dzisiaj — metadane','Missed today — metadata'],missedWeek:['Minęło w tygodniu — metadane','Missed this week — metadata'],
  films:['Filmy','Films'],series:['Seriale','Series'],favourite:['Ulubiony gatunek','Favourite genre'],scifi:['Sci-Fi','Sci-Fi'],reality:['Reality','Reality'],family:['Familijne','Family']};
 function bounds(now){
  var start=new Date(now);start.setHours(0,0,0,0);
  var end=new Date(start);end.setDate(end.getDate()+1);
  var future=new Date(start);future.setDate(future.getDate()+7);
  var past=new Date(start);past.setDate(past.getDate()-7);
  return {start:+start,end:+end,future:+future,past:+past};
 }
 function candidates(input){
  if(!Array.isArray(input)||input.length>2000)return [];
  return input.filter(function(x){return x&&x.tmdb&&Number.isSafeInteger(x.tmdb.id)&&x.tmdb.id>0&&
    ['movie','tv'].indexOf(x.tmdb.type)>=0&&typeof x.title==='string';}).slice(0,2000).map(function(x){
   return {title:x.title.slice(0,500),tmdb:{id:x.tmdb.id,type:x.tmdb.type},
    genre_ids:engine.genres(x).slice(0,30),vote_average:Number.isFinite(x.vote_average)?x.vote_average:null,
    vote_count:Number.isSafeInteger(x.vote_count)&&x.vote_count>=0?x.vote_count:0,
    popularity:Number.isFinite(x.popularity)&&x.popularity>=0?x.popularity:0,
    release_date:typeof x.release_date==='string'?x.release_date.slice(0,10):'',
    first_air_date:typeof x.first_air_date==='string'?x.first_air_date.slice(0,10):''};
  });
 }
 function events(input){
  if(!Array.isArray(input)||input.length>20000)return [];
  var seen=Object.create(null);
  return input.filter(function(x){return x&&typeof x.title==='string'&&typeof x.channelId==='string'&&
    Number.isSafeInteger(x.start)&&x.start>=0&&Number.isSafeInteger(x.end)&&x.end>x.start&&
    x.provenance&&/^[a-zA-Z0-9_.-]{1,64}$/.test(x.provenance.source||'');}).map(function(x){
   return {kind:'airing',title:x.title.slice(0,500),channelId:x.channelId.slice(0,200),start:x.start,end:x.end,
    source:x.provenance.source,freshness:x.freshness==='fresh'||x.freshness==='stale'?x.freshness:'unknown',playable:false};
  }).filter(function(x){var key=JSON.stringify(x);if(seen[key])return false;seen[key]=true;return true;})
    .sort(function(a,b){return a.start-b.start||a.channelId.localeCompare(b.channelId)||a.title.localeCompare(b.title);});
 }
 function configuration(value){
  value=value||{};
  var order=[],enabled=Array.isArray(value.enabled)?value.enabled:IDS;
  (Array.isArray(value.order)?value.order:[]).concat(IDS).forEach(function(id){if(IDS.indexOf(id)>=0&&order.indexOf(id)<0)order.push(id);});
  return order.filter(function(id){return enabled.indexOf(id)>=0;});
 }
 function build(options){
  options=options||{};var now=options.now;
  if(!Number.isSafeInteger(now)||now<0)return [];
  var pref=engine.settings(options.pref);if(!pref.enabled)return [];
  var b=bounds(now),air=events(options.events),ranked=engine.rank(candidates(options.candidates),pref,options.history,now);
  function cards(filter){return ranked.filter(function(r){return filter(r.item);}).slice(0,20).map(function(r){
   return Object.assign({},r.item,{kind:'title',recoScore:r.score,recoReason:r.reason,ratingSource:'TMDB'});
  });}
  function genre(item,name){var ids=GENRES[name]||({romance:[10749],comedy:[35],drama:[18],action:[28,10759],documentary:[99],horror:[27]})[name]||[];
   return engine.genres(item).some(function(g){return ids.indexOf(g)>=0;});}
  var sections={now:air.filter(function(e){return e.start<=now&&e.end>now;}),
   today:air.filter(function(e){return e.start>now&&e.start<b.end;}),
   week:air.filter(function(e){return e.start>=b.end&&e.start<b.future;}),
   missedToday:air.filter(function(e){return e.end<=now&&e.end>b.start;}).reverse(),
   missedWeek:air.filter(function(e){return e.end<=b.start&&e.end>b.past;}).reverse(),
   films:cards(function(x){return x.tmdb.type==='movie';}),series:cards(function(x){return x.tmdb.type==='tv';}),
   favourite:cards(function(x){return pref.favouriteGenre==='auto'||genre(x,pref.favouriteGenre);})};
  Object.keys(GENRES).forEach(function(g){sections[g]=cards(function(x){return genre(x,g);});});
  return configuration(options.config).map(function(id){return {id:id,title:LABELS[id][options.lang==='en'?1:0],
   items:sections[id].slice(0,20),ranking:IDS.indexOf(id)<5?'time':'profile'};}).filter(function(r){return r.items.length;});
 }
 function createCache(options){
  options=options||{};var ttl=options.ttlMs===undefined?3600000:options.ttlMs,stale=options.staleMs===undefined?86400000:options.staleMs;
  if(typeof options.read!=='function'||typeof options.write!=='function'||!Number.isSafeInteger(ttl)||ttl<=0||!Number.isSafeInteger(stale)||stale<0)throw Error('invalid cache limits');
  var clock=options.now||Date.now;
  return {put:function(input,fetchedAt){var at=fetchedAt===undefined?clock():fetchedAt;
    if(!Number.isSafeInteger(at)||at<0||at>clock()||clock()-at>=ttl+stale)return false;
    var items=candidates(input).slice(0,300);if(!items.length)return false;
    try{options.write(JSON.stringify({schema:1,at:at,items:items}));return true;}catch(e){return false;}},
   get:function(){var missing={status:'missing',items:[]};try{
    var raw=options.read();if(typeof raw!=='string'||raw.length>1000000)return missing;
    var data=JSON.parse(raw),age=clock()-data.at;
    if(data.schema!==1||!Number.isSafeInteger(data.at)||age<0||age>=ttl+stale||!Array.isArray(data.items)||data.items.length>300)return missing;
    var items=candidates(data.items);if(!items.length||items.length!==data.items.length)return missing;
    return {status:age<ttl?'fresh':'stale',items:items,fetchedAt:data.at};
   }catch(e){return missing;}},clear:function(){try{options.write(null);return true;}catch(e){return false;}}};
 }
 root.DC4IHomeRails={ids:IDS.slice(),labels:LABELS,build:build,bounds:bounds,configuration:configuration,createCache:createCache};
})(window);
