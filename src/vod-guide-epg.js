/* Guide EPG request adapter. Limits private Xtream EPG to one in-flight request. */
(function(root){
 'use strict';
 function create(load,parse,opts){
   var options=opts||{},ttl=Number(options.ttlMs)||300000;
   var now=options.now||Date.now,cache=Object.create(null),pending=Object.create(null);
   var tail=Promise.resolve();
   function key(channel){return String(channel.accountId||'')+':'+String(channel.id);}
   function get(channel){
     if(!channel || !channel.id)return Promise.resolve([]);
     var k=key(channel),snapshot=cache[k],current=now();
     if(snapshot && current-snapshot.at<ttl)return Promise.resolve(snapshot.events);
     if(pending[k])return pending[k];
     var job=tail.then(function(){return load(channel);}).then(function(payload){
       var rows=Array.isArray(payload)?payload:(payload && payload.epg_listings)||[];
       if(!Array.isArray(rows))rows=[];
       var list=rows.map(function(r){return parse(r,channel,now());}).filter(Boolean);
       cache[k]={at:now(),events:list};
       return list;
     });
     tail=job.catch(function(){return null;});
     pending[k]=job.then(function(list){delete pending[k];return list;},function(err){delete pending[k];throw err;});
     return pending[k];
   }
   function invalidate(accountId){
     var prefix=String(accountId||'')+':';
     Object.keys(cache).forEach(function(k){if(k.indexOf(prefix)===0)delete cache[k];});
   }
   return {get:get,invalidate:invalidate};
 }
 root.DC4IGuideEpg={create:create};
})(window);
