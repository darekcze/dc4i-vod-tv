/* Metadata-only EPG foundation. No network, device calls or persistent user data.
   Name matches are suggestions; only explicit XMLTV IDs establish a mapping. */
(function(root){
'use strict';
var DAY=86400000;
function clone(value){return JSON.parse(JSON.stringify(value));}
function normalize(value){return String(value||'').normalize('NFKD').replace(/[\u0300-\u036f]/g,'')
 .replace(/ł/g,'l').replace(/Ł/g,'L').toLowerCase().replace(/\s+/g,' ').trim();}
function mapChannel(channel,channels){
 channel=channel||{};channels=Array.isArray(channels)?channels:[];
 var id=String(channel.epg_channel_id||''),name=normalize(channel.title);
 var matches=channels.filter(function(c){return !!c && typeof c.id==='string' && (id?c.id===id:
   !!name && Array.isArray(c.names) && c.names.some(function(n){return normalize(n)===name;}));});
 if(matches.length!==1)return {status:matches.length?'ambiguous':'unmapped',channelId:null};
 return {status:id?'mapped':'suggested',channelId:matches[0].id,method:id?'explicit-id':'name'};
}
function bounded(value,max){return typeof value==='string'?value.slice(0,max):'';}
function validTime(value){return Number.isSafeInteger(value)&&value>=0;}
function sanitize(snapshot){
 if(!snapshot || snapshot.schemaVersion!==1 || !/^[a-zA-Z0-9_.-]{1,64}$/.test(snapshot.source||'') ||
    !validTime(snapshot.fetchedAt) || !Array.isArray(snapshot.events) || snapshot.events.length>20000 ||
    !Array.isArray(snapshot.channels) || snapshot.channels.length>1000)throw Error('invalid snapshot');
 var channels=[],ids=Object.create(null),conflicts=Object.create(null),events=[],seen=Object.create(null);
 var partial=!!(snapshot.partial || (snapshot.diagnostics &&
   (snapshot.diagnostics.skipped || snapshot.diagnostics.conflictingChannels)));
 snapshot.channels.forEach(function(c){
  if(!c || typeof c.id!=='string' || !c.id || c.id.length>200 || !Array.isArray(c.names)){partial=true;return;}
  var clean={id:c.id,names:c.names.filter(function(n){return typeof n==='string'&&n.trim();}).slice(0,20).map(function(n){return bounded(n,200);})};
  if(!clean.names.length){partial=true;return;}
  if(ids[c.id]){conflicts[c.id]=true;partial=true;}else{ids[c.id]=true;channels.push(clean);}
 });
 channels=channels.filter(function(c){return !conflicts[c.id];});
 snapshot.events.forEach(function(e){
  if(!e || typeof e.channelId!=='string' || !e.channelId || e.channelId.length>200 || conflicts[e.channelId] ||
     !validTime(e.start)||!validTime(e.end)||e.end<=e.start||!bounded(e.title,500).trim()){partial=true;return;}
  var rating=e.rating && typeof e.rating.value==='string'?{
   value:bounded(e.rating.value,50),system:bounded(e.rating.system,100)||'unspecified',verified:false}:null;
  var clean={channelId:e.channelId,title:bounded(e.title,500),start:e.start,end:e.end,
   description:bounded(e.description,2000),year:/^\d{4}$/.test(e.year||'')?e.year:'',
   categories:Array.isArray(e.categories)?e.categories.slice(0,20).map(function(c){return bounded(c,100);}):[],
   originalLanguage:bounded(e.originalLanguage,50),rating:rating,
   tracks:{audio:'unknown',subtitles:'unknown'},playable:false,
   provenance:{source:snapshot.source,kind:'xmltv',fetchedAt:snapshot.fetchedAt}};
  var fingerprint=JSON.stringify(clean);
  if(!seen[fingerprint]){seen[fingerprint]=true;events.push(clean);}
 });
 events.sort(function(a,b){return a.start-b.start||a.end-b.end||a.channelId.localeCompare(b.channelId)||a.title.localeCompare(b.title);});
 return {schemaVersion:1,source:snapshot.source,fetchedAt:snapshot.fetchedAt,channels:channels,events:events,partial:partial};
}
function timeline(snapshot,channelId,from,to){
 if(!validTime(from)||!validTime(to)||to<=from||to-from>10*DAY)throw Error('invalid timeline window');
 return sanitize(snapshot).events.filter(function(e){return e.channelId===channelId&&e.start<to&&e.end>from;});
}
function createCache(options){
 options=options||{};
 var now=options.now||Date.now,ttl=options.ttlMs===undefined?300000:options.ttlMs;
 var stale=options.staleMs===undefined?3600000:options.staleMs;
 var capacity=options.maxSources===undefined?4:options.maxSources;
 if(!Number.isSafeInteger(ttl)||ttl<=0||!Number.isSafeInteger(stale)||stale<0||
    !Number.isSafeInteger(capacity)||capacity<1||capacity>16)throw Error('invalid cache limits');
 var entries=Object.create(null),order=[];
 function remove(source){delete entries[source];order=order.filter(function(s){return s!==source;});}
 function get(source){
  var snapshot=entries[source];
  if(!snapshot)return {status:'missing',snapshot:null,partial:false};
  var age=now()-snapshot.fetchedAt;
  if(age<0||age>=ttl+stale){remove(source);return {status:'missing',snapshot:null,partial:false};}
  return {status:age<ttl?'fresh':'stale',snapshot:clone(snapshot),partial:snapshot.partial,ageMs:age};
 }
 function put(input){
  var value;
  try{value=sanitize(input);}catch(e){return {accepted:false,reason:'invalid'};}
  var age=now()-value.fetchedAt;
  if(age<0)return {accepted:false,reason:'future'};
  if(age>=ttl+stale)return {accepted:false,reason:'expired'};
  var previous=get(value.source).snapshot;
  if(previous&&value.fetchedAt<previous.fetchedAt)return {accepted:false,reason:'older'};
  // A partial refresh must not erase known programmes or renew their TTL.
  if(previous&&value.partial)return {accepted:false,reason:'partial'};
  remove(value.source);entries[value.source]=value;order.push(value.source);
  while(order.length>capacity)remove(order[0]);
  return {accepted:true,partial:value.partial};
 }
 return {put:put,get:get,clear:function(){entries=Object.create(null);order=[];}};
}
root.DC4IRichEpg={mapChannel:mapChannel,timeline:timeline,createCache:createCache};
})(window);
