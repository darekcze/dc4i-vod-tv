/* Offline DVR contracts. No storage implementation, recorder, network or playback. */
(function(root){
 'use strict';
 var STATES=['scheduled','starting','recording','finishing','cancelling','cancelled','missed','failed','interrupted','finished-unverified'];
 function create(options){
  options=options||{};var clock=options.now||Date.now,backend=options.backend;
  var quota=options.quotaBytes===undefined?1073741824:options.quotaBytes;
  var concurrent=options.maxConcurrent===undefined?1:options.maxConcurrent;
  var maxJobs=options.maxJobs===undefined?100:options.maxJobs;
  var retention=options.retentionMs===undefined?86400000:options.retentionMs;
  var timeout=options.timeoutMs===undefined?10000:options.timeoutMs;
  if(!Number.isSafeInteger(quota)||quota<=0||quota>1099511627776||!Number.isSafeInteger(concurrent)||concurrent<1||concurrent>4||
    !Number.isSafeInteger(maxJobs)||maxJobs<1||maxJobs>100||!Number.isSafeInteger(retention)||retention<1||retention>2592000000||
    !Number.isSafeInteger(timeout)||timeout<1||timeout>30000)throw Error('invalid limits');
  var available=!!backend&&['start','finish','cancel','stat'].every(function(k){return typeof backend[k]==='function';});
  var jobs=[],versions=Object.create(null),inflight=Object.create(null),ticking=null;
  function id(value){return typeof value==='string'&&/^[a-zA-Z0-9_.-]{1,64}$/.test(value);}
  function clean(value){
   if(!value||!id(value.id)||!id(value.channelId)||!Number.isSafeInteger(value.start)||value.start<0||!Number.isSafeInteger(value.end)||
     value.end<=value.start||value.end-value.start>43200000||!Number.isSafeInteger(value.estimatedBytes)||value.estimatedBytes<=0||value.estimatedBytes>quota)return null;
   return {id:value.id,channelId:value.channelId,title:typeof value.title==='string'?value.title.slice(0,200):'',start:value.start,end:value.end,estimatedBytes:value.estimatedBytes};
  }
  function publicJob(j){return {id:j.id,channelId:j.channelId,title:j.title,start:j.start,end:j.end,estimatedBytes:j.estimatedBytes,
    state:j.state,reason:j.reason||'',bytes:j.bytes||0,artifactId:j.artifactId||'',completedAt:j.completedAt||0,playable:false};}
  function reserved(j){return ['cancelled','missed','failed'].indexOf(j.state)>=0?0:j.state==='finished-unverified'?j.bytes:Math.max(j.estimatedBytes,j.bytes||0);}
  function used(){return jobs.reduce(function(n,j){return n+reserved(j);},0);}
  function active(j){return ['starting','recording','finishing','cancelling','interrupted'].indexOf(j.state)>=0;}
  function find(key){return jobs.find(function(j){return j.id===key;});}
  function call(method,arg){return new Promise(function(resolve,reject){
   var done=false;function finish(ok,value){if(done)return;done=true;clearTimeout(timer);ok?resolve(value):reject(Error('backend-failed'));}
   var timer=setTimeout(function(){finish(false);},timeout);
   try{Promise.resolve(backend[method](arg)).then(function(v){finish(true,v);},function(){finish(false);});}catch(e){finish(false);}
  });}
  function schedule(input){
   if(!available)return {accepted:false,reason:'backend-unavailable'};
   var job=clean(input);if(!job)return {accepted:false,reason:'invalid-schedule'};
   var old=find(job.id);if(old)return JSON.stringify(clean(old))===JSON.stringify(job)?{accepted:true,idempotent:true,job:publicJob(old)}:{accepted:false,reason:'id-collision'};
   if(job.start<clock()||job.start-clock()>604800000)return {accepted:false,reason:'invalid-schedule'};
   if(jobs.some(function(j){return j.state==='interrupted';}))return {accepted:false,reason:'recovery-required'};
   if(jobs.length>=maxJobs)return {accepted:false,reason:'job-limit'};
   if(used()+job.estimatedBytes>quota)return {accepted:false,reason:'quota'};
   var points=[];jobs.concat([job]).filter(function(j){return j===job||['scheduled','starting','recording','finishing','cancelling'].indexOf(j.state)>=0;})
    .forEach(function(j){points.push([j.start,1],[j.end,-1]);});
   points.sort(function(a,b){return a[0]-b[0]||a[1]-b[1];});var count=0;
   for(var i=0;i<points.length;i++){count+=points[i][1];if(count>concurrent)return {accepted:false,reason:'conflict'};}
   job.state='scheduled';job.reason='simulation-only';jobs.push(job);versions[job.id]=0;
   return {accepted:true,idempotent:false,job:publicJob(job)};
  }
  function artifact(job,value){
   if(!value||value.exists!==true||value.active!==false||!id(value.artifactId)||!Number.isSafeInteger(value.bytes)||value.bytes<=0)return false;
   job.bytes=value.bytes;job.artifactId=value.artifactId;
   if(used()-reserved(job)+job.bytes>quota)return false;
   job.state='finished-unverified';job.reason='artifact-metadata-only';job.completedAt=job.completedAt||clock();return true;
  }
  function operate(job,method){
   var token=++versions[job.id];job.state=method==='start'?'starting':'finishing';
   var pending=call(method,method==='start'?clean(job):job.id).then(function(result){
    if(versions[job.id]!==token)return;
    if(method==='start'&&result===true){job.state='recording';job.reason='simulation-only';}
    else if(method==='finish'&&artifact(job,result))return;
    else{job.state='interrupted';job.reason='backend-result-unverified';}
   },function(){if(versions[job.id]===token){job.state='interrupted';job.reason='backend-operation-failed';}});
   inflight[job.id]=pending;return pending.finally(function(){if(inflight[job.id]===pending)delete inflight[job.id];});
  }
  function tick(){
   if(ticking)return ticking;if(!available)return Promise.resolve();
   ticking=(async function(){
    var ordered=jobs.slice().sort(function(a,b){return a.start-b.start||a.id.localeCompare(b.id);});
    for(var i=0;i<ordered.length;i++){
     var job=ordered[i],now=clock();
     if(job.state==='recording'&&now>=job.end)await operate(job,'finish');
     if(job.state!=='scheduled')continue;
     if(now>=job.end||now-job.start>30000){job.state='missed';job.reason='start-window-missed';continue;}
     if(now>=job.start&&jobs.filter(active).length<concurrent&&!jobs.some(function(j){return j.state==='interrupted';}))await operate(job,'start');
    }
   })().finally(function(){ticking=null;});return ticking;
  }
  async function cancel(key){
   var job=find(key);if(!job||!available||['cancelled','missed','failed','finished-unverified'].indexOf(job.state)>=0)return false;
   if(job.state==='scheduled'){job.state='cancelled';job.reason='cancelled';return true;}
   if(job.state==='cancelling')return false;
   ++versions[key];job.state='cancelling';job.reason='cancelling';
   if(inflight[key])await inflight[key];
   try{if(await call('cancel',key)!==true)throw Error('cancel-unconfirmed');job.state='cancelled';job.reason='cancelled';return true;}
   catch(e){job.state='interrupted';job.reason='cancel-unconfirmed';return false;}
  }
  function snapshot(){return {schema:1,jobs:jobs.map(publicJob)};}
  function restore(value){
   if(jobs.length||!value||value.schema!==1||!Array.isArray(value.jobs)||value.jobs.length>maxJobs)return false;
   var seen=Object.create(null),restored=[];
   for(var i=0;i<value.jobs.length;i++){
    var raw=value.jobs[i],job=clean(raw);if(!job||seen[job.id]||STATES.indexOf(raw.state)<0)return false;seen[job.id]=true;
    job.state=active(raw)?'interrupted':raw.state;job.reason=job.state==='interrupted'?'restart-interrupted':'restored-metadata';
    if(raw.bytes){if(!Number.isSafeInteger(raw.bytes)||raw.bytes<0||raw.bytes>quota)return false;job.bytes=raw.bytes;}
    if(raw.artifactId){if(!id(raw.artifactId))return false;job.artifactId=raw.artifactId;}
    if(raw.completedAt){if(!Number.isSafeInteger(raw.completedAt)||raw.completedAt<0||raw.completedAt>clock())return false;job.completedAt=raw.completedAt;}
    if(job.state==='finished-unverified'&&(!job.bytes||!job.artifactId||!job.completedAt))return false;
    restored.push(job);
   }
   if(restored.reduce(function(n,j){return n+reserved(j);},0)>quota)return false;
   jobs=restored;jobs.forEach(function(j){versions[j.id]=0;});return true;
  }
  async function reconcile(key){
   var job=find(key);if(!available||!job||['interrupted','finished-unverified'].indexOf(job.state)<0)return false;
   var token=++versions[key];
   try{var value=await call('stat',key);if(versions[key]!==token)return false;
    if(artifact(job,value))return true;
    if(value&&value.exists===false&&value.active===false){job.state='failed';job.reason='no-artifact';job.bytes=0;job.artifactId='';return true;}
   }catch(e){}
   if(versions[key]!==token)return false;
   job.state='interrupted';job.reason='recovery-unverified';return false;
  }
  return {schedule:schedule,tick:tick,cancel:cancel,snapshot:snapshot,restore:restore,reconcile:reconcile,jobs:function(){return jobs.map(publicJob);},
   quota:function(){return {limit:quota,reserved:used(),remaining:Math.max(0,quota-used())};},
   capability:function(){return {usable:false,simulation:available,reason:available?'in-memory-contract-only':'backend-unavailable'};},
   retentionPlan:function(){return jobs.filter(function(j){return j.state==='finished-unverified'&&clock()-j.completedAt>=retention;}).map(function(j){return {id:j.id,artifactId:j.artifactId,bytes:j.bytes};});}};
 }
 root.DC4IDvr={create:create};
})(window);
