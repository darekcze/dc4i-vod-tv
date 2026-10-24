/* DC4I VOD TV: expose root-only controls only after verified local service response. */
(function(){
'use strict';
function showRootControls(){
  document.body.classList.add('dc4i-rooted');
}
function detect(){
  if(typeof window.PalmServiceBridge!=='function')return;
  var timer=setTimeout(function(){},3000);
  fetch('http://127.0.0.1:45620/getApps',{
    method:'POST',headers:{'Content-Type':'application/json'},body:'{}'
  }).then(function(r){if(!r.ok)throw Error('root service not available');return r.json();})
  .then(function(data){if(data&&Array.isArray(data.apps))showRootControls();})
  .catch(function(){ /* Developer Mode / non-root is supported, silently hide root-only controls */ })
  .then(function(){clearTimeout(timer);});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',detect);
else detect();
})();
