/* Injected archive contract only. No URLs, credentials, network or buffer allocation. */
(function(root){
 'use strict';
 function create(options){
  options=options||{};var transport=options.transport,clock=options.now||Date.now;
  var timeout=options.timeoutMs===undefined?10000:options.timeoutMs;
  var seconds=options.maxBufferSeconds===undefined?120:options.maxBufferSeconds;
  var bytes=options.maxBufferBytes===undefined?33554432:options.maxBufferBytes;
  if(!Number.isSafeInteger(timeout)||timeout<=0||timeout>30000||!Number.isSafeInteger(seconds)||seconds<=0||seconds>300||!Number.isSafeInteger(bytes)||bytes<=0||bytes>67108864)throw Error('invalid limits');
  var status='unavailable',reason='no-offer',request=null,proof=null,epoch=0,pending=null,cancelCall=null;
  function validProof(){return proof&&clock()>=proof.at&&clock()-proof.at<120000;}
  function state(){
   if(status==='ready'&&!validProof()){release();status='unverified';reason='verification-expired';proof=null;}
   return {status:status,reason:reason,canPause:status==='playing'&&!!validProof()&&proof.canPause,
    canSeek:status==='playing'&&!!validProof()&&proof.canSeek};
  }
  function stop(){++epoch;if(cancelCall)cancelCall();pending=null;proof=null;
   if(transport&&typeof transport.stop==='function'&&['verifying','ready','starting','playing'].indexOf(status)>=0){try{Promise.resolve(transport.stop()).catch(function(){});}catch(e){}}
   status='stopped';reason='stopped';return state();
  }
  function release(){if(transport&&typeof transport.stop==='function'){try{Promise.resolve(transport.stop()).catch(function(){});}catch(e){}}}
  function offer(input){
   stop();request=null;
   if(!input||input.providerEnabled!==true||input.archiveHint!==true){status='unavailable';reason='provider-unavailable';return state();}
   if(!/^[a-zA-Z0-9_.-]{1,100}$/.test(input.providerId||'')||!/^\d{1,20}$/.test(input.streamId||'')||
      !Number.isSafeInteger(input.start)||input.start<0||!Number.isSafeInteger(input.end)||input.end<=input.start||input.end>clock()||input.end-input.start>86400000){
    status='unavailable';reason='invalid-or-future-event';return state();}
   request={providerId:input.providerId,streamId:input.streamId,start:input.start,end:input.end};
   status='unverified';reason='runtime-verification-required';return state();
  }
  function call(method){
   return new Promise(function(resolve,reject){
    var value,finished=false;
    function finish(ok,result){if(finished)return;finished=true;clearTimeout(timer);if(cancelCall===cancel)cancelCall=null;ok?resolve(result):reject(Error('transport-failed'));}
    function cancel(){finish(false);}
    var timer=setTimeout(cancel,timeout);cancelCall=cancel;
    try{value=transport[method](Object.assign({},request));}catch(e){finish(false);return;}
    Promise.resolve(value).then(function(result){finish(true,result);},function(){finish(false);});
   });
  }
  function bounded(value){
   if(!value||!Number.isSafeInteger(value.bufferedBytes)||value.bufferedBytes<=0||value.bufferedBytes>bytes||!Array.isArray(value.seekable)||!value.seekable.length||value.seekable.length>16)return null;
   var ranges=[],total=0,last=-Infinity;
   for(var i=0;i<value.seekable.length;i++){
    var r=value.seekable[i];if(!r||!Number.isFinite(r.start)||!Number.isFinite(r.end)||r.start<0||r.end<=r.start||r.start<last)return null;
    total+=r.end-r.start;last=r.end;ranges.push({start:r.start,end:r.end});
   }
   return total<=seconds&&ranges[ranges.length-1].end-ranges[0].start<=seconds?ranges:null;
  }
  function verify(){
   if(pending)return pending;
   if(status==='playing'||status==='starting')return Promise.resolve(state());
   if(!request||!transport||typeof transport.verify!=='function')return Promise.resolve(state());
   var token=++epoch;status='verifying';reason='checking-runtime';proof=null;
   pending=call('verify').then(function(result){
    if(token!==epoch)return state();
    if(result&&result.providerEnabled===false){release();status='unavailable';reason='provider-disabled';}
    else if(!result||result.providerEnabled!==true||result.mediaTypeVerified!==true||result.playbackStarted!==true){release();status='unverified';reason='insufficient-runtime-evidence';}
    else{proof={at:clock(),canPause:result.canPause===true&&!!bounded(result),canSeek:!!bounded(result)};status='ready';reason='session-verified';}
    return state();
   },function(){if(token===epoch){release();status='failed';reason='verification-failed';proof=null;}return state();}).then(function(result){if(token===epoch)pending=null;return result;});
   return pending;
  }
  function start(){
   if(state().status!=='ready'||!transport||typeof transport.play!=='function')return Promise.resolve(false);
   var token=++epoch;status='starting';reason='starting';
   return call('play').then(function(result){if(token!==epoch)return false;
    if(result&&result.started===true){status='playing';reason='session-playing';return true;}
    release();status='failed';reason='playback-failed';proof=null;return false;
   },function(){if(token===epoch){release();status='failed';reason='playback-failed';proof=null;}return false;});
  }
  function control(method,target){
   if(status!=='playing'||!validProof()||!transport||typeof transport[method]!=='function'||typeof transport.bounds!=='function')return false;
   var ranges;try{ranges=bounded(transport.bounds());}catch(e){return false;}
   if(!ranges||(method==='pause'&&!proof.canPause)||(method==='seek'&&(!proof.canSeek||!Number.isFinite(target)||!ranges.some(function(r){return target>=r.start&&target<=r.end;}))))return false;
   var token=epoch;
   try{var result=transport[method](target);if(result===false)throw Error('control-failed');Promise.resolve(result).then(function(value){if(value===false)throw Error('control-failed');}).catch(function(){if(token===epoch&&status==='playing'){release();status='failed';reason='control-failed';proof=null;}});return true;}catch(e){release();status='failed';reason='control-failed';proof=null;return false;}
  }
  return {offer:offer,state:state,verify:verify,start:start,stop:stop,pause:function(){return control('pause');},seek:function(t){return control('seek',t);},
   failure:function(){release();++epoch;if(cancelCall)cancelCall();pending=null;status='failed';reason='media-failed';proof=null;return state();}};
 }
 root.DC4IArchive={create:create};
})(window);
