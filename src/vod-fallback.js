/* DC4I VOD TV: native LG player discovery and title handoff, v1.2.2.
 * LG Store listing 1231221 is a CATALOG ID, not a verified applicationManager ID.
 * Both getAppLoadStatus and launch outcomes are recorded (without credentials).
 */
(function () {
'use strict';
var TV=window.TV;if(!TV)return;
function say(pl,en){return TV.S.uiLang==='en'?en:pl;}
var players={
 stremio:{name:'Stremio',ids:['io.strem.tv','io.strem.webos','com.razagr.stremio'],match:/stremio/i},
 iptv:{name:'IPTV Smarters Player',storeId:'1231221',
  ids:['com.smarterstvplayers.net'],match:/^IPTVSmartersPlayer$/i}
};
var known=TV.store('vodInstalledPlayerIds')||{};
if(known.iptv && known.iptv!=='com.smarterstvplayers.net'){delete known.iptv;TV.store('vodInstalledPlayerIds',known);}
var diagnostics=TV.store('vodNativeDiagnostics122')||[];
function log(name,phase,id,result,error){
 var row={player:name,phase:phase,id:id||'',success:!!result,
  error:error?String(error).slice(0,140):'',when:Date.now()};
 diagnostics.push(row);
 if(diagnostics.length>24)diagnostics=diagnostics.slice(-24);
 TV.store('vodNativeDiagnostics122',diagnostics);
 try{console.log('DC4I_PLAYER',row.player,row.phase,row.id,row.success,row.error);}catch(e){}
}
function report(name,phase,id,result,error){log(name,phase,id,result,error);return result;}
function until(promise,ms){
 return Promise.race([promise,new Promise(function(resolve){setTimeout(function(){resolve(null);},ms);})]);
}
function installed(id,name){
 return until(TV.luna('com.webos.applicationManager/getAppLoadStatus',{appId:id})
  .then(function(res){return report(name,'installed',id,res.exist===true,res.exist===true?'':'absent');},
        function(err){log(name,'installed',id,false,(err&&err.errorText)||err);return false;}),1300);
}
function firstPositive(ids,name){
 return new Promise(function(resolve){
  var pending=ids.length,finished=false;
  if(!pending)return resolve(null);
  var stop=setTimeout(function(){finish(null);},2900);
  function finish(id){if(finished)return;finished=true;clearTimeout(stop);resolve(id);}
  ids.forEach(function(id){
   installed(id,name).then(function(ok){
    if(ok===true)return finish(id);
    if(--pending===0)finish(null);
   },function(){if(--pending===0)finish(null);});
  });
 });
}
function byName(regex,name){
 if(!TV.onTV)return Promise.resolve(null);
 return until(TV.luna('com.webos.applicationManager/listLaunchPoints',{subscribe:false})
  .then(function(res){
   var a=res.launchPoints||res.apps||[];
   for(var i=0;i<a.length;i++){
    var title=a[i].title||a[i].name||'';
    if(regex.test(title))return report(name,'list',a[i].id||a[i].appId,true,'')?
      (a[i].id||a[i].appId):null;
   }
   return null;
  },function(err){log(name,'list','',false,(err&&err.errorText)||err);return null;}),1300);
}
function remember(name,id){
 if(!id)return null;
 known[name]=id;TV.store('vodInstalledPlayerIds',known);
 return id;
}
function find(name){
 var cfg=players[name];
 if(!cfg||!TV.onTV)return Promise.resolve(null);
 var actual=TV.findInstalledApp&&TV.findInstalledApp(cfg.match);
 if(actual&&actual.id&&!actual.unverified && cfg.ids.indexOf(actual.id)>=0)return Promise.resolve(remember(name,actual.id));
 var ids=[];
 if(known[name])ids.push(known[name]);
 cfg.ids.forEach(function(id){if(ids.indexOf(id)<0)ids.push(id);});
 return firstPositive(ids,name).then(function(id){
  if(id)return remember(name,id);
  return byName(cfg.match,name).then(function(found){return remember(name,found);});
 });
}
function launchResult(name,id,params){
 return until(TV.luna('com.webos.applicationManager/launch',{id:id,params:params||{}})
  .then(function(res){
   var ok=res&&res.returnValue!==false;
   log(name,'launch',id,ok,ok?'':res.errorText||'error');
   return ok;
  },function(err){
   log(name,'launch',id,false,(err&&err.errorText)||(err&&err.errorCode)||err);
   return false;
  }),1800).then(function(ok){
   if(ok===null){log(name,'launch-timeout',id,false,'no confirmation');return false;}
   return ok;
  });
}
function tryLaunch(name,params,preferred){
 var cfg=players[name];
 var ids=[];
 function add(id){if(id&&ids.indexOf(id)<0)ids.push(id);}
 add(preferred);add(known[name]);
 cfg.ids.forEach(add);
 var counter=0;
 function next(){
  if(counter>=ids.length)return Promise.resolve(null);
  var id=ids[counter++];
  return launchResult(name,id,params).then(function(ok){
   if(ok){remember(name,id);return id;}
   return next();
  });
 }
 return next();
}
function stremioLink(title,tmdb,details){
 var ids=details&&details.external_ids,imdb=ids&&ids.imdb_id;
 var type=tmdb&&tmdb.type==='tv'?'series':'movie';
 if(/^tt[0-9]{5,10}$/.test(imdb||'')){
  return type==='movie' ? 'stremio:///detail/movie/'+imdb+'/'+imdb :
   'stremio:///detail/series/'+imdb;
 }
 return 'stremio:///search?search='+encodeURIComponent(title||'');
}
function resolveLink(title,tmdb,details){
 if(details&&details.external_ids&&/^tt[0-9]{5,10}$/.test(details.external_ids.imdb_id||''))
  return Promise.resolve(stremioLink(title,tmdb,details));
 if(!tmdb||!tmdb.id||!tmdb.type)return Promise.resolve(stremioLink(title,tmdb,details));
 return until(TV.tmdb(tmdb.type+'/'+tmdb.id+'/external_ids')
  .then(function(ids){return stremioLink(title,tmdb,{external_ids:ids});},
        function(){return stremioLink(title,tmdb,details);}),2200)
  .then(function(result){return result||stremioLink(title,tmdb,details);});
}
function stremioWebUrl(title,tmdb,details){
 return resolveLink(title,tmdb,details).then(function(url){
  // The hash route belongs to Stremio Web, not LG's proprietary native application.
  return 'https://web.stremio.com/#'+url.replace('stremio://','');
 });
}
function openWeb(title,tmdb,details){
 return stremioWebUrl(title,tmdb,details).then(function(url){
  if(!TV.onTV){TV.toast(url);return false;}
  return launchResult('stremio-web','com.webos.app.browser',{target:url,fullMode:true})
   .then(function(ok){
    if(!ok)TV.toast(say('Nie udało się otworzyć Stremio Web','Could not open Stremio Web'));
    return ok;
   });
 });
}
function open(name,title,tmdb,details){
 var cfg=players[name];
 if(!cfg)return Promise.resolve(false);
 if(!TV.onTV){TV.toast(say('Otworzyłoby ','Would open ')+cfg.name);return Promise.resolve(false);}
 if(name==='stremio'){
  return resolveLink(title,tmdb,details).then(function(url){
   var params={contentTarget:url,search:title||''};
   // A successful webOS launch does not guarantee native Stremio honored contentTarget.
   return find('stremio').then(function(id){
    if(id)return launchResult('stremio',id,params).then(function(ok){
     if(!ok)TV.toast(say('Stremio nie uruchomiło się. Użyj Stremio Web.','Stremio could not launch; try Stremio Web.'));
     return ok;
    });
    return tryLaunch('stremio',params,null).then(function(found){
     if(!found)TV.toast(say('Nie wykryto Stremio','Stremio not found'));
     return !!found;
    });
   });
  });
 }
 var params=title?{search:title,searchQuery:title,title:title}:{};
 return find('iptv').then(function(id){
  if(id)return launchResult('iptv',id,params).then(function(ok){
   if(ok)return true;
   return tryLaunch('iptv',params,id).then(function(found){
    if(!found)TV.toast(say('Nie udało się uruchomić Smarters. Zobacz diagnostykę.','Unable to launch Smarters; check diagnostics.'));
    return !!found;
   });
  });
  return tryLaunch('iptv',params,null).then(function(found){
   if(!found)TV.toast(say('Nie udało się uruchomić IPTVSmartersPlayer (com.smarterstvplayers.net).','Cannot launch IPTVSmartersPlayer (com.smarterstvplayers.net).'));
   return !!found;
  });
 });
}
TV.vodPlayers={find:find,open:open,openWeb:openWeb,players:players,
 stremioLink:stremioLink,stremioWebUrl:stremioWebUrl,
 positiveFirst:firstPositive,byVisibleName:byName,
 diagnostics:function(){return diagnostics.slice();}};
})();
