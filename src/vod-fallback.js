/* DC4I VOD TV: native Stremio and Smarters Player launch helpers.
   LG Smarters package ID com.iptvsmarters.app appears in IP-control documentation.
   Actual search/deep-link support on webOS is not yet confirmed.
*/
(function(){
'use strict';
var TV=window.TV;if(!TV)return;
var say=function(pl,en){return TV.S.uiLang==='en'?en:pl;};
var players={
 stremio:{name:'Stremio',ids:['io.strem.tv','io.strem.webos','com.razagr.stremio'],match:/stremio/i},
 iptv:{name:'IPTV Smarters Player',ids:['com.iptvsmarters.app','com.iptvsmarters.player',
  'com.iptv.smarters','com.smartersplayer.app','smartersplayer','com.iptvsmarterspro',
  'com.whmcs.iptvsmarters','com.iptv.smarterspro','iptvsmarters'],match:/smarters|smarter\s*player|iptv\s*smarter/i}
};
var resolved=TV.store('vodInstalledPlayerIds')||{};
function firstInstalled(ids,timeoutMs){
 return new Promise(function(resolve){
  ids=ids.filter(Boolean);if(!ids.length)return resolve(null);
  var done=false,left=ids.length,timeout=setTimeout(function(){finish(null);},timeoutMs||3400);
  function finish(id){if(done)return;done=true;clearTimeout(timeout);resolve(id||null);}
  ids.forEach(function(id){
   TV.luna('com.webos.applicationManager/getAppLoadStatus',{appId:id})
    .then(function(r){if(r.exist===true)return finish(id);if(--left===0)finish(null);},
          function(){if(--left===0)finish(null);});
  });
 });
}
function byName(re){
 return Promise.race([
  TV.luna('com.webos.applicationManager/listLaunchPoints',{subscribe:false})
   .then(function(r){var a=r.launchPoints||r.apps||[];
    for(var i=0;i<a.length;i++)if(re.test((a[i].title||a[i].name||'')+' '+(a[i].id||a[i].appId||'')))
      return a[i].id||a[i].appId||null;
    return null;
   },function(){return null;}),
  new Promise(function(res){setTimeout(function(){res(null);},1200);})
 ]);
}
function remember(name,id){if(!id)return null;resolved[name]=id;TV.store('vodInstalledPlayerIds',resolved);return id;}
function find(name){
 var p=players[name];if(!p||!TV.onTV)return Promise.resolve(null);
 var seen=TV.findInstalledApp&&TV.findInstalledApp(p.match);
 if(seen&&seen.id)return Promise.resolve(remember(name,seen.id));
 var ids=[];if(resolved[name])ids.push(resolved[name]);
 p.ids.forEach(function(id){if(ids.indexOf(id)<0)ids.push(id);});
 return firstInstalled(ids,3400).then(function(id){
  if(id)return remember(name,id);
  return byName(p.match).then(function(v){return remember(name,v);});
 });
}
function stremioLink(title,tmdb,details){
 var ids=details&&details.external_ids,imdb=ids&&ids.imdb_id;
 var type=tmdb&&tmdb.type==='tv'?'series':'movie';
 if(/^tt[0-9]{5,10}$/.test(imdb||''))
  return type==='movie'?'stremio:///detail/movie/'+imdb+'/'+imdb:
    'stremio:///detail/series/'+imdb;
 return 'stremio:///search?search='+encodeURIComponent(title||'');
}
function stremioTarget(title,tmdb,details){
 if(details&&details.external_ids&&/^tt[0-9]{5,10}$/.test(details.external_ids.imdb_id||''))
  return Promise.resolve(stremioLink(title,tmdb,details));
 if(!tmdb||!tmdb.id||!tmdb.type)return Promise.resolve(stremioLink(title,tmdb,details));
 return Promise.race([
  TV.tmdb(tmdb.type+'/'+tmdb.id+'/external_ids')
   .then(function(r){return stremioLink(title,tmdb,{external_ids:r});},
         function(){return stremioLink(title,tmdb,details);}),
  new Promise(function(res){setTimeout(function(){res(stremioLink(title,tmdb,details));},2000);})
 ]);
}
function open(name,title,tmdb,details){
 var p=players[name];if(!p)return Promise.resolve(false);
 if(!TV.onTV){TV.toast(say('Na LG otworzy się ','Would launch on LG: ')+p.name);return Promise.resolve(false);}
 return find(name).then(function(id){
  if(!id){TV.toast(say('Nie wykryto aplikacji ','App not found: ')+p.name);return false;}
  if(name==='stremio')return stremioTarget(title,tmdb,details).then(function(url){
   // Stremio protocol is documented, but acceptance by LG webOS is unverified.
   TV.launch(id,{contentTarget:url,search:title||''});return true;
  });
  // Smarters Player has no published webOS deep-link contract. The app may ignore these hints.
  TV.launch(id,title?{search:title,searchQuery:title,title:title}:{});
  return true;
 });
}
TV.vodPlayers={find:find,open:open,players:players,stremioLink:stremioLink,
 positiveFirst:firstInstalled,byVisibleName:byName};
})();
