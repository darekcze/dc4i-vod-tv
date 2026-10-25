/* Metadata-only journaled restore. Each localStorage write is atomic; the batch is recoverable, not globally atomic. */
(function(root){'use strict';var base=root.DC4IMetadataBackup,JOURNAL='metadataRestoreJournalV1';
 var keys={home:'homeRailsLayoutV1',reminders:'dc4iReminderPrefsV1',charts:'dc4iChartLinksV1',profile:'settings',opened:'recommendationOpensV1',playback:'playbackLearningV1'};
 var prefFields={home:['active','order','enabled'],reminders:['enabled','quiet','start','end'],charts:['region','category'],profile:['uiLang','recoEnabled','recoLearnHistory','recoLearnPlayback','recoFavouriteGenre','recoSciFiMin','recoHorrorMin','recoOtherMin','recoHorrorMode','recoEveningBoost','recoHideOpened']};
 function own(x,k){return Object.prototype.hasOwnProperty.call(x,k);}function object(x){return x&&typeof x==='object'&&!Array.isArray(x);}function equal(a,b){return JSON.stringify(a)===JSON.stringify(b);}function copy(x){return JSON.parse(JSON.stringify(x));}
 function only(x,names){if(!object(x)||Object.keys(x).some(function(k){return names.indexOf(k)<0;}))throw Error('fields');}
 function genres(x){if(!Array.isArray(x)||x.length>32||x.some(function(g){return !Number.isInteger(g)||g<=0||g>100000;}))throw Error('genres');return x.slice();}
 function record(name,r){if(!object(r))throw Error('record');var at=r.at;if(!Number.isSafeInteger(at)||at<0||at>8640000000000000)throw Error('time');
  if(name==='opened'){if(typeof r.key!=='string'||!/^(movie|tv):[1-9][0-9]{0,14}$/.test(r.key)||['opened','completed'].indexOf(r.action)<0)throw Error('identity');return {key:r.key,action:r.action,at:at,genres:genres(r.genres)};}
  if(typeof r.session!=='string'||!/^[a-zA-Z0-9_-]{1,100}$/.test(r.session)||['partial','completed'].indexOf(r.action)<0||!Number.isFinite(r.seconds)||r.seconds<30||r.seconds>604800||(r.duration!==null&&(!Number.isFinite(r.duration)||r.duration<=0||r.duration>604800)))throw Error('observation');
  return {session:r.session,action:r.action,seconds:r.seconds,at:at,genres:genres(r.genres),duration:r.duration};}
 function id(name,r){return name==='opened'?r.key+':'+r.action+':'+r.at:r.session;}
 function normalize(name,value,strict){if(!own(keys,name))throw Error('section');
  if(name==='opened'||name==='playback'){if(!Array.isArray(value)||value.length>150)throw Error('records');var seen={};return value.map(function(r){var clean=record(name,r);if(strict)only(r,Object.keys(clean));var k=id(name,clean);if(seen[k]){if(strict)throw Error('duplicate');return null;}seen[k]=true;return clean;}).filter(Boolean);}
  if(strict)only(value,prefFields[name]);if(!object(value))throw Error('preferences');var out={};prefFields[name].forEach(function(k){if(!own(value,k))return;var v=value[k];
   if(name==='profile'){if(k==='uiLang'){if(['pl','en'].indexOf(v)<0)throw Error();}
    else if(k==='recoFavouriteGenre'){if(['auto','scifi','family','romance','reality','comedy','drama','action','documentary','horror'].indexOf(v)<0)throw Error();}
    else if(k==='recoHorrorMode'){if(['hide','high'].indexOf(v)<0)throw Error();}
    else if(/Min$/.test(k)){if(!Number.isFinite(v)||v<0||v>10)throw Error();}
    else if(typeof v!=='boolean')throw Error();out[k]=v;
   }else {var defaults=name==='home'?{active:true,order:[],enabled:[]}:name==='reminders'?{enabled:true,quiet:false,start:1320,end:480}:{region:'poland',category:'film'};defaults[k]=v;out[k]=base.section(name,defaults)[k];}
  });return out;}
 function complete(name,value){var defaults=name==='home'?{active:true,order:['now','today','week','missedToday','missedWeek','films','series','favourite','scifi','reality','family'],enabled:['now','today','week','missedToday','missedWeek','films','series','favourite','scifi','reality','family']}:name==='reminders'?{enabled:true,quiet:false,start:1320,end:480}:{region:'poland',category:'film'};return base.section(name,Object.assign(defaults,value));}
 function readSection(port,name){var raw=port.read(keys[name]);if(raw===null)return {present:false,raw:null,value:name==='opened'||name==='playback'?[]:{}};
  if(typeof raw!=='string'||raw.length>262144)throw Error('stored size');var parsed=JSON.parse(raw);var value=name==='playback'?(object(parsed)&&parsed.schema===1?parsed.records:null):parsed;
  var clean=normalize(name,value,false);if(name==='charts')base.section(name,clean);return {present:true,raw:parsed,value:clean};}
 function encode(name,current,target,present){var raw=current.raw,out;
  if(name==='opened'||name==='playback'){var old=name==='opened'?(Array.isArray(raw)?raw:[]):raw&&raw.records||[],index={};old.forEach(function(r){index[id(name,r)]=r;});
   var wanted={};target.forEach(function(r){wanted[id(name,r)]=true;});var list=old.filter(function(r){return wanted[id(name,r)];});target.forEach(function(r){if(!index[id(name,r)])list.push(Object.assign(Object.create(null),r,name==='playback'?{imported:true}:{}));});
   if(name==='opened')return !present&&!list.length?null:JSON.stringify(list);
   out=Object.assign(Object.create(null),raw||{});out.schema=1;out.records=list;
   if(!present&&!list.length){delete out.schema;delete out.records;if(!Object.keys(out).length)return null;}return JSON.stringify(out);
  }
  out=Object.assign(Object.create(null),raw||{});prefFields[name].forEach(function(k){delete out[k];});Object.keys(target).forEach(function(k){out[k]=target[k];});return !present&&!Object.keys(out).length?null:JSON.stringify(out);}
 function parse(text){if(typeof text!=='string'||text.length>262144)throw Error('size');var v=JSON.parse(text);only(v,['format','schema','sections']);
  if(v.format!=='dc4i-preferences'||[1,2].indexOf(v.schema)<0)throw Error('schema');only(v.sections,Object.keys(keys));if(!Object.keys(v.sections).length)throw Error('empty');var sections={};Object.keys(v.sections).forEach(function(name){if(v.schema===1&&!own(base.keys,name))throw Error('migration scope');sections[name]=normalize(name,v.sections[name],true);});return {schema:2,migratedFrom:v.schema,sections:sections};}
 function create(port){var pending=null,lockedProfile=null,revision=0;
  function loadJournal(){var raw=port.read(JOURNAL);if(raw===null)return null;if(raw.length>524288)throw Error('journal limit');var j=JSON.parse(raw);only(j,['schema','state','steps']);if(j.schema!==1||['applying','committed','rolling-back'].indexOf(j.state)<0||!Array.isArray(j.steps)||!j.steps.length||j.steps.length>6)throw Error('journal');var seen={};j.steps.forEach(function(s){only(s,['name','present','before','after']);if(!own(keys,s.name)||seen[s.name]||typeof s.present!=='boolean')throw Error('journal step');seen[s.name]=true;normalize(s.name,s.before,true);normalize(s.name,s.after,true);});return j;}
  function writeRaw(key,raw){if(port.profile()!==lockedProfile)throw Error('profile changed');port.write(key,raw);if(port.profile()!==lockedProfile||port.read(key)!==raw)throw Error('unconfirmed');}
  function journal(j){var raw=j===null?null:JSON.stringify(j);if(raw!==null&&raw.length>524288)throw Error('journal limit');writeRaw(JOURNAL,raw);}
  function exportText(){if(loadJournal())throw Error('recovery required');var token=port.profile(),sections={};Object.keys(keys).forEach(function(n){var value=readSection(port,n);if(value.present)sections[n]=own(base.keys,n)?complete(n,value.value):value.value;});if(port.profile()!==token||!Object.keys(sections).length)throw Error('empty or profile changed');return JSON.stringify({format:'dc4i-preferences',schema:2,sections:sections},null,2);}
  function preview(text){pending=null;var token=port.profile();try{if(loadJournal())return {ok:false,reason:'recovery-required'};var parsed=parse(text),steps=[];Object.keys(parsed.sections).forEach(function(n){var current=readSection(port,n),target=parsed.sections[n];
    if(Array.isArray(target)){var existing={};current.value.forEach(function(r){existing[id(n,r)]=true;});target=current.value.concat(target.filter(function(r){return !existing[id(n,r)];}));if(target.length>150)throw Error('merge capacity');}
    else {target=Object.assign({},current.value,target);if(own(base.keys,n))target=complete(n,target);normalize(n,target,true);}
    steps.push({name:n,present:current.present,before:current.value,after:target});});
   if(port.profile()!==token)throw Error('profile changed');pending={profile:token,steps:copy(steps),token:++revision};return {ok:true,token:pending.token,migratedFrom:parsed.migratedFrom,changes:steps.map(function(s){return {section:s.name,before:s.before,after:s.after};})};
  }catch(e){return {ok:false,reason:'invalid-or-unreadable'};}}
  function recover(){pending=null;var token=port.profile();lockedProfile=token;try{var j=loadJournal();if(!j)return {ok:true,state:'idle'};
   if(j.state==='committed'){journal(null);return {ok:true,state:'committed'};}
   j.state='rolling-back';journal(j);
   for(var i=j.steps.length-1;i>=0;i--){if(port.profile()!==token)return {ok:false,reason:'profile-changed'};var s=j.steps[i],current=readSection(port,s.name);
    if(equal(current.value,s.before)&&current.present===s.present)continue;if(!equal(current.value,s.after))return {ok:false,reason:'conflict'};
    writeRaw(keys[s.name],encode(s.name,current,s.before,s.present));}
   if(port.profile()!==token)return {ok:false,reason:'profile-changed'};journal(null);return {ok:true,state:'rolled-back'};
  }catch(e){return {ok:false,reason:'recovery-required'};}}
  function apply(expectedToken){var p=pending;if(!p||(expectedToken!==undefined&&p.token!==expectedToken))return {ok:false,reason:'preview-required'};pending=null;lockedProfile=p.profile;try{if(port.profile()!==p.profile||loadJournal())return {ok:false,reason:'conflict'};
   for(var i=0;i<p.steps.length;i++){var current=readSection(port,p.steps[i].name);if(current.present!==p.steps[i].present||!equal(current.value,p.steps[i].before))return {ok:false,reason:'conflict'};}
   var j={schema:1,state:'applying',steps:p.steps};journal(j);
   for(var x=0;x<j.steps.length;x++){if(port.profile()!==p.profile)return {ok:false,reason:'profile-changed'};var step=j.steps[x],now=readSection(port,step.name);if(!equal(now.value,step.before))return {ok:false,reason:'recovery-required'};writeRaw(keys[step.name],encode(step.name,now,step.after,true));}
   if(port.profile()!==p.profile)return {ok:false,reason:'profile-changed'};j.state='committed';journal(j);journal(null);return {ok:true,state:'committed'};
  }catch(e){return {ok:false,reason:'recovery-required'};}}
  return {preview:preview,apply:apply,recover:recover,exportText:exportText,status:function(){try{return loadJournal()?{pending:true}:{pending:false};}catch(e){return {pending:true,invalid:true};}},invalidate:function(){pending=null;}};
 }
 root.DC4IBackupTransaction={create:create,parse:parse,journalKey:JOURNAL,keys:Object.assign({},keys)};
})(window);
