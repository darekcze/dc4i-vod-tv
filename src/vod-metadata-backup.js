/* Preferences only. No histories, titles, playlists, account data or arbitrary keys. */
(function(root){'use strict';
 var keys={home:'homeRailsLayoutV1',reminders:'dc4iReminderPrefsV1',charts:'dc4iChartLinksV1'},ids=['now','today','week','missedToday','missedWeek','films','series','favourite','scifi','reality','family'];
 function object(v){return v&&typeof v==='object'&&!Array.isArray(v);}
 function fields(v,allowed){if(!object(v)||Object.keys(v).some(function(k){return allowed.indexOf(k)<0;}))throw Error('invalid fields');}
 function section(name,v){var out={};if(name==='home'){fields(v,['active','order','enabled']);if(typeof v.active!=='boolean')throw Error();out.active=v.active;
  ['order','enabled'].forEach(function(k){if(!Array.isArray(v[k])||v[k].length>11||new Set(v[k]).size!==v[k].length||v[k].some(function(x){return ids.indexOf(x)<0;}))throw Error();out[k]=v[k].slice();});}
 else if(name==='reminders'){fields(v,['enabled','quiet','start','end']);if(typeof v.enabled!=='boolean'||typeof v.quiet!=='boolean'||!Number.isInteger(v.start)||v.start<0||v.start>=1440||!Number.isInteger(v.end)||v.end<0||v.end>=1440)throw Error();out={enabled:v.enabled,quiet:v.quiet,start:v.start,end:v.end};}
 else if(name==='charts'){fields(v,['region','category']);if(['global','poland'].indexOf(v.region)<0||['film','tv'].indexOf(v.category)<0)throw Error();out={region:v.region,category:v.category};}else throw Error('unsupported section');return out;}
 function project(name,v){if(!object(v))throw Error();var names=name==='home'?['active','order','enabled']:name==='reminders'?['enabled','quiet','start','end']:['region','category'];var out={};names.forEach(function(k){out[k]=v[k];});return section(name,out);}
 function parse(text){if(typeof text!=='string'||text.length>16384)throw Error('size limit');var v=JSON.parse(text);fields(v,['format','schema','sections']);if(v.format!=='dc4i-preferences'||v.schema!==1)throw Error('schema');fields(v.sections,Object.keys(keys));var out={};Object.keys(v.sections).forEach(function(k){out[k]=section(k,v.sections[k]);});if(!Object.keys(out).length)throw Error('empty');return out;}
 function create(port){var preview=null,undo=null;
  function exportText(){var sections={};Object.keys(keys).forEach(function(name){var raw=port.read(keys[name]);if(raw!==null)sections[name]=project(name,JSON.parse(raw));});if(!Object.keys(sections).length)throw Error('nothing saved');return JSON.stringify({format:'dc4i-preferences',schema:1,sections:sections},null,2);}
  function prepare(text,name){preview=null;if(!Object.prototype.hasOwnProperty.call(keys,name))return {ok:false,reason:'section'};try{var sections=parse(text);if(!sections[name])throw Error();var key=keys[name],raw=port.read(key),old=raw===null?{}:JSON.parse(raw);if(!object(old))throw Error();
   var changes=Object.keys(sections[name]).map(function(field){var before={state:'missing'};
    if(Object.prototype.hasOwnProperty.call(old,field)){try{var candidate=Object.assign({},sections[name]);candidate[field]=old[field];before={state:'value',value:section(name,candidate)[field]};}catch(e){before={state:'invalid'};}}
    var after=sections[name][field];return {field:field,before:before,after:after,changed:before.state!=='value'||JSON.stringify(before.value)!==JSON.stringify(after)};
   });
   preview={profile:port.profile(),key:key,before:raw,after:JSON.stringify(Object.assign(Object.create(null),old,sections[name])),section:name};return {ok:true,section:name,fields:Object.keys(sections[name]),changes:changes};}catch(e){return {ok:false,reason:'invalid-or-unreadable'};}}
  function apply(){if(!preview)return {ok:false,reason:'preview-required'};var p=preview;preview=null;
   try{if(port.profile()!==p.profile||port.read(p.key)!==p.before)return {ok:false,reason:'conflict'};port.write(p.key,p.after);
    if(port.read(p.key)!==p.after)return {ok:false,reason:'write-unconfirmed'};undo=p;return {ok:true};}catch(e){return {ok:false,reason:'write-unconfirmed'};}}
  function rollback(){if(!undo)return {ok:false,reason:'nothing-to-undo'};var p=undo;
   try{if(port.profile()!==p.profile||port.read(p.key)!==p.after)return {ok:false,reason:'conflict'};port.write(p.key,p.before);if(port.read(p.key)!==p.before)return {ok:false,reason:'write-unconfirmed'};undo=null;return {ok:true};}catch(e){return {ok:false,reason:'write-unconfirmed'};}}
  return {exportText:exportText,prepare:prepare,apply:apply,rollback:rollback,invalidate:function(){preview=null;}};
 }
 root.DC4IMetadataBackup={create:create,parse:parse,section:section,keys:Object.assign({},keys)};
})(window);
