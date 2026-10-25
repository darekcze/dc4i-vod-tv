/* Existing reminder-array storage contract; synchronous, foreground-only delivery. */
(function(root){
 'use strict';var KEY='dc4iEpgRemindersV1',PREF='dc4iReminderPrefsV1',GRACE=300000;
 function preferences(raw){raw=raw||{};return {enabled:raw.enabled!==false,quiet:raw.quiet===true,
  start:Number.isInteger(raw.start)&&raw.start>=0&&raw.start<1440?raw.start:1320,
  end:Number.isInteger(raw.end)&&raw.end>=0&&raw.end<1440?raw.end:480};}
 function validPreferences(raw){return raw==null||(typeof raw==='object'&&!Array.isArray(raw)&&['enabled','quiet'].every(function(k){return raw[k]===undefined||typeof raw[k]==='boolean';})&&['start','end'].every(function(k){return raw[k]===undefined||(Number.isInteger(raw[k])&&raw[k]>=0&&raw[k]<1440);}));}
 function quiet(now,pref){
  if(!pref.quiet)return false;var date=new Date(now),minute=date.getHours()*60+date.getMinutes();
  return pref.start===pref.end|| (pref.start<pref.end?minute>=pref.start&&minute<pref.end:minute>=pref.start||minute<pref.end);
 }
 function valid(item){return item&&typeof item.key==='string'&&item.key.length>0&&item.key.length<=512&&
  Number.isSafeInteger(item.start)&&item.start>=0&&typeof item.title==='string'&&typeof item.channel==='string';}
 function publicItem(item,now){return {key:item.key,title:item.title.slice(0,300),channel:item.channel.slice(0,200),start:item.start,
  state:now>=item.start+GRACE?'expired':now>=item.start?'due':'pending'};}
 function create(options){
  options=options||{};if(typeof options.read!=='function'||typeof options.write!=='function')throw Error('storage port required');
  var clock=options.now||Date.now;
  function load(){try{var data=options.read(KEY);if(data==null)return {ok:true,raw:[]};
   if(!Array.isArray(data)||data.length>5000||JSON.stringify(data).length>2000000)return {ok:false,reason:'invalid-storage'};
   return {ok:true,raw:data.slice()};}catch(e){return {ok:false,reason:'storage-failed'};}}
  function write(key,value){try{options.write(key,value);return JSON.stringify(options.read(key))===JSON.stringify(value);}catch(e){return false;}}
  function prefs(){try{var raw=options.read(PREF);if(!validPreferences(raw))throw Error('invalid preferences');return preferences(raw);}
   catch(e){return Object.assign(preferences(),{enabled:false,storageError:true});}}
  function setPrefs(value){try{var old=options.read(PREF);if(!validPreferences(old))return {ok:false,reason:'invalid-preferences'};
   var next=Object.assign({},old||{},preferences(Object.assign({},old||{},value)));
   return {ok:write(PREF,next)};}catch(e){return {ok:false,reason:'storage-failed'};}}
  function list(){var data=load();if(!data.ok)return {ok:false,reason:data.reason,items:[]};var seen=Object.create(null);
   return {ok:true,items:data.raw.filter(function(x){if(!valid(x)||seen[x.key])return false;seen[x.key]=true;return true;})
    .map(function(x){return publicItem(x,clock());}).sort(function(a,b){return a.start-b.start||a.key.localeCompare(b.key);})};}
  function add(event){
   var start=event&&event.time&&event.time.start,id=event&&event.channelId;
   if(!event||typeof id!=='string'||!id||id.length>128||!Number.isSafeInteger(start)||start<=clock()||start-clock()>2592000000||typeof event.title!=='string')return {ok:false,reason:'invalid-event'};
   var data=load();if(!data.ok)return data;var key=id+':'+start;
   if(data.raw.some(function(x){return valid(x)&&x.key===key;}))return {ok:true,duplicate:true};
   if(data.raw.length>=100)return {ok:false,reason:'limit'};
   data.raw.push({key:key,title:event.title.slice(0,300),channel:typeof event.channelTitle==='string'?event.channelTitle.slice(0,200):'',start:start});
   return write(KEY,data.raw)?{ok:true,duplicate:false}:{ok:false,reason:'storage-failed'};
  }
  function cancel(key){if(typeof key!=='string'||!key||key.length>512)return {ok:false,reason:'invalid-key'};var data=load();if(!data.ok)return data;
   var next=data.raw.filter(function(x){return !x||x.key!==key;});if(next.length===data.raw.length)return {ok:true,changed:false};
   return {ok:write(KEY,next),changed:true};}
  function tick(options){
   if(!options||options.foreground!==true)return {delivered:[],expired:0,reason:'not-foreground'};
   var pref=prefs();if(!pref.enabled)return {delivered:[],expired:0,reason:pref.storageError?'invalid-preferences':'disabled'};
   var data=load();if(!data.ok)return {delivered:[],expired:0,reason:data.reason};
   var now=clock(),remove=Object.create(null),delivered=[],expired=0,isQuiet=quiet(now,pref);
   data.raw.forEach(function(x){if(!valid(x)||remove[x.key])return;
    if(now>=x.start+GRACE){remove[x.key]=true;expired++;}
    else if(now>=x.start&&!isQuiet){remove[x.key]=true;delivered.push(publicItem(x,now));}
   });
   if(!Object.keys(remove).length)return {delivered:[],expired:0,reason:isQuiet?'quiet':'idle'};
   var next=data.raw.filter(function(x){return !x||!remove[x.key];});
   if(!write(KEY,next))return {delivered:[],expired:0,reason:'storage-failed'};
   return {delivered:delivered,expired:expired,reason:'processed'};
  }
  return {add:add,cancel:cancel,list:list,prefs:prefs,setPrefs:setPrefs,tick:tick};
 }
 root.DC4IReminders={create:create,quiet:quiet};
})(window);
