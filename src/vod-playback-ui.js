/* Native-media session adapter. No stream URLs, credentials or inferred languages. */
(function(){'use strict';var TV=window.TV,api=window.DC4IPlaybackLearning;if(!TV||!api)return;
 var key='playbackLearningV1',bound=new WeakMap(),counter=0,evidence=null,evidenceProfile=null,epoch=0;
 function tr(pl,en){return TV.S.uiLang==='en'?en:pl;}
 function profile(){return String(TV.P&&TV.P.prefix||'');}
 function read(){if(typeof TV.readPlaybackStorage!=='function')throw Error();var v=TV.readPlaybackStorage();if(v===null)return [];
  if(!v||v.schema!==1||!Array.isArray(v.records)||v.records.length>150)throw Error();return v.records;}
 function write(records){TV.store(key,{schema:1,records:records});return JSON.stringify(read())===JSON.stringify(records);}
 function valid(r){return r&&typeof r.session==='string'&&r.session.length<=100&&['partial','completed'].indexOf(r.action)>=0&&Number.isFinite(r.seconds)&&r.seconds>=30&&r.seconds<=604800&&Number.isFinite(r.at)&&Array.isArray(r.genres);}
 function history(){try{return read().filter(function(r){return valid(r)&&r.imported!==true;}).map(function(r){return {action:'observed-'+r.action,at:r.at,genres:r.genres.filter(function(g){return Number.isInteger(g)&&g>0;}).slice(0,32),seconds:r.seconds,provenance:'native-media-progression'};});}catch(e){return [];}}
 function clear(){epoch++;try{if(!write([]))throw Error();TV.toast(tr('Wyczyszczono obserwacje odtwarzania profilu','Profile playback observations cleared'));}catch(e){TV.toast(tr('Nie usunięto obserwacji','Observations were not cleared'));}}
 function begin(media,item){if(!media||typeof media.addEventListener!=='function')return false;if(bound.has(media))bound.get(media)();
  evidence=null;evidenceProfile=null;var token=profile(),startedEpoch=epoch,ready=false,id=Date.now().toString(36)+'-'+(++counter)+'-'+Math.random().toString(36).slice(2,10),model=api.create({now:Date.now,save:function(record){
   if(profile()!==token||startedEpoch!==epoch||(typeof TV.profileFlagEnabled!=='function'||!TV.profileFlagEnabled('recoLearnPlayback')))return false;
   try{var records=read();if(records.some(function(r){return !valid(r);}))return false;
    var value={session:record.session,action:record.action,seconds:record.seconds,at:record.at,genres:record.genres,duration:record.duration};
    records=records.filter(function(r){return r.session!==id;});records.push(value);return write(records.slice(-150));
   }catch(e){return false;}}});
  model.start({session:id,profile:token,genres:item&&item.learning&&item.learning.genre_ids});
  function event(type){if(type==='loadedmetadata'){ready=true;return;}if(!ready||startedEpoch!==epoch)return;var foreground=document.visibilityState==='visible'&&typeof document.hasFocus==='function'&&document.hasFocus();
   if((typeof TV.profileFlagEnabled!=='function'||!TV.profileFlagEnabled('recoLearnPlayback')))foreground=false;
   if(profile()!==token){evidence=null;evidenceProfile=null;}
   if(foreground&&profile()===token){evidence=api.tracks(media);evidenceProfile=token;}
   model.event(type,{profile:profile(),foreground:foreground,time:media.currentTime,duration:media.duration});}
  var handlers={},names=['loadedmetadata','playing','timeupdate','pause','seeking','waiting','stalled','ended','error'];
  names.forEach(function(name){handlers[name]=function(){event(name);};media.addEventListener(name,handlers[name]);});
  function background(){event('pause');}
  function resume(){if(document.visibilityState==='visible'&&typeof document.hasFocus==='function'&&document.hasFocus()&&media.paused===false&&media.ended!==true)event('playing');else background();}
  document.addEventListener('visibilitychange',resume);window.addEventListener('blur',background);window.addEventListener('focus',resume);
  function detach(){event('stop');names.forEach(function(name){media.removeEventListener(name,handlers[name]);});document.removeEventListener('visibilitychange',resume);window.removeEventListener('blur',background);window.removeEventListener('focus',resume);bound.delete(media);evidence=null;}
  bound.set(media,detach);return true;
 }
 TV.addSetting({key:'recoLearnPlayback',title:tr('Polecane: ucz się z odtwarzania lokalnego','Recommendations: learn from local playback'),hint:tr('Tylko zaobserwowany postęp; bez historii zewnętrznych aplikacji','Observed progression only; no external app history'),opts:[[true,tr('Tak','Yes')],[false,tr('Nie','No')]]},true);
 TV.addSetting({key:'playbackClear',title:tr('Obserwacje odtwarzania profilu','Profile playback observations'),hint:tr('Nie usuwa historii otwarć ani kont','Does not remove opened history or accounts'),opts:[['clear',tr('Wyczyść','Clear')]]},'');
 var old=TV.personalized&&TV.personalized.history;if(old)TV.personalized.history=function(){return old().concat((typeof TV.profileFlagEnabled!=='function'||!TV.profileFlagEnabled('recoLearnPlayback'))?[]:history());};
 TV.playbackLearning={begin:begin,stop:function(media){if(bound.has(media))bound.get(media)();},history:history,clear:clear,trackEvidence:function(){return evidenceProfile===profile()?evidence:null;},languageMatch:api.languageMatch};
})();
