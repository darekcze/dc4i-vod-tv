/* Observed foreground progression only; never URLs, credentials or inferred tracks. */
(function(root){'use strict';
 function languages(list,subtitles){var out=[];try{for(var i=0;list&&i<Math.min(list.length,64);i++){var x=list[i];if(subtitles&&['subtitles','captions'].indexOf(x.kind)<0)continue;var lang=String(x.language||'').toLowerCase();if(/^[a-z]{2,3}(?:-[a-z0-9]{2,8})?$/.test(lang)&&out.indexOf(lang)<0)out.push(lang);}}catch(e){return [];}return out;}
 function tracks(media){return {source:'media-track-list',audio:languages(media&&media.audioTracks),subtitles:languages(media&&media.textTracks,true),dubbing:'unknown'};}
 function languageMatch(evidence,preference){if(!preference||preference==='any')return 'match';if(!evidence||evidence.source!=='media-track-list')return 'unknown';
  if(preference==='pl-dubbed')return 'unknown';
  if(preference!=='en-pl-subs'||!Array.isArray(evidence.audio)||!Array.isArray(evidence.subtitles))return 'unknown';
  return evidence.audio.some(function(x){return /^(en|eng)(-|$)/.test(x);})&&evidence.subtitles.some(function(x){return /^(pl|pol)(-|$)/.test(x);})?'match':'unknown';}
 function create(options){var session=null,last=null,active=false,blocked=false,seen=new Set();
  function boundary(){last=null;active=false;}
  function start(meta){boundary();session=null;blocked=false;if(!meta||typeof meta.session!=='string'||seen.has(meta.session)||typeof meta.profile!=='string')return false;
   seen.add(meta.session);if(seen.size>500)seen.delete(seen.values().next().value);
   session={session:meta.session,profile:meta.profile,genres:Array.isArray(meta.genres)?meta.genres.filter(function(x){return Number.isInteger(x)&&x>0;}).slice(0,32):[],ranges:[],seconds:0,action:'partial',at:options.now(),duration:null};return true;}
  function snapshot(){if(!session)return null;return {session:session.session,profile:session.profile,genres:session.genres.slice(),seconds:session.seconds,action:session.action,at:session.at,duration:session.duration};}
  function save(){if(!session||session.seconds<30)return false;try{return options.save(snapshot())===true;}catch(e){return false;}}
  function event(type,data){data=data||{};if(!session||blocked)return null;
   if(data.profile!==session.profile){blocked=true;boundary();return null;}
   if(data.foreground!==true){save();boundary();return snapshot();}
   var t=data.time,now=options.now(),duration=data.duration;
   if(Number.isFinite(duration)&&duration>0&&duration<=604800)session.duration=duration;
   if(type==='playing'){active=true;last=null;return snapshot();}
   if(type==='timeupdate'&&active&&Number.isFinite(t)&&t>=0){
    if(last){var dt=t-last.t,wall=(now-last.now)/1000;
     if(dt>0&&wall>0&&wall<=15&&dt<=wall*1.25+0.25&&dt<=15){
      session.ranges.push([last.t,t]);session.ranges.sort(function(a,b){return a[0]-b[0];});var merged=[];
      session.ranges.forEach(function(r){var p=merged[merged.length-1];if(p&&r[0]<=p[1])p[1]=Math.max(p[1],r[1]);else merged.push(r.slice());});
      if(merged.length>1000){blocked=true;boundary();return snapshot();}session.ranges=merged;
      session.seconds=merged.reduce(function(n,r){return n+r[1]-r[0];},0);session.at=now;
     }}last={t:t,now:now};
   }
   if(type==='ended'&&session.duration&&session.seconds>=session.duration*0.9&&Number.isFinite(t)&&t>=session.duration*0.9)session.action='completed';
   if(['pause','seeking','waiting','stalled','ended','error','stop'].indexOf(type)>=0){save();boundary();if(['ended','error','stop'].indexOf(type)>=0)blocked=true;}
   return snapshot();
  }
  return {start:start,event:event,snapshot:snapshot,save:save};
 }
 root.DC4IPlaybackLearning={create:create,tracks:tracks,languageMatch:languageMatch};
})(window);
