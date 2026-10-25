import assert from 'node:assert/strict';
import {existsSync,readFileSync} from 'node:fs';
import vm from 'node:vm';
const context={window:{}};
if(existsSync('src/vod-reminders.js'))vm.runInNewContext(readFileSync('src/vod-reminders.js','utf8'),context);
const api=context.window.DC4IReminders;assert.ok(api);
let now=Date.UTC(2026,9,25,0,0),profile='a',fail=false;const storage={};
const options={now:()=>now,read:k=>storage[profile+':'+k]??null,write(k,v){if(!fail)storage[profile+':'+k]=JSON.parse(JSON.stringify(v));}};
let model=api.create(options);
const event={channelId:'1',channelTitle:'Synthetic',title:'Original reminder',time:{start:now+60000}};
const old={key:'legacy:'+now,title:'Legacy',channel:'Old',start:now+120000,extra:'preserve'};
storage['a:dc4iEpgRemindersV1']=[old,{unknown:'preserve'}];
assert.equal(model.add(event).ok,true);assert.equal(model.add(event).duplicate,true);
assert.equal(storage['a:dc4iEpgRemindersV1'][0].extra,'preserve');
profile='b';assert.equal(model.list().items.length,0);model.add({...event,title:'Other profile'});profile='a';
fail=true;assert.equal(model.add({...event,channelId:'2'}).ok,false);now=event.time.start;
assert.equal(model.tick({foreground:true}).delivered.length,0,'failed removal must not announce delivery');
fail=false;assert.equal(model.tick({foreground:false}).delivered.length,0);
assert.equal(model.tick({foreground:true}).delivered.length,1);model=api.create(options);assert.equal(model.tick({foreground:true}).delivered.length,0,'reload cannot redeliver consumed reminder');
assert.equal(model.cancel(old.key).ok,true);assert.equal(storage['a:dc4iEpgRemindersV1'].length,1,'unknown legacy record preserved');
profile='b';assert.equal(model.list().items.length,1,'other profile unchanged');
model.setPrefs({enabled:false});assert.equal(model.tick({foreground:true}).delivered.length,0);
model.setPrefs({enabled:true,quiet:true,start:0,end:0});assert.equal(model.tick({foreground:true}).delivered.length,0,'equal quiet endpoints mean all day');
now+=300000;assert.equal(model.tick({foreground:true}).expired,1);assert.equal(model.list().items.length,0);
assert.equal(model.add({...event,time:{start:now}}).ok,false);
assert.equal(model.add({...event,time:{start:now+31*86400000}}).ok,false);
const pending=Array.from({length:101},(_,i)=>({key:'old'+i,title:'Legacy',channel:'TV',start:now+100000+i}));
storage['b:dc4iEpgRemindersV1']=pending;assert.equal(model.add({...event,time:{start:now+60000}}).reason,'limit');assert.equal(storage['b:dc4iEpgRemindersV1'].length,101);
storage['b:dc4iEpgRemindersV1']={corrupt:true};assert.equal(model.add({...event,time:{start:now+60000}}).reason,'invalid-storage');
assert.equal(api.quiet(new Date(2026,0,1,23,0).getTime(),{quiet:true,start:1320,end:480}),true);
assert.equal(api.quiet(new Date(2026,0,1,8,0).getTime(),{quiet:true,start:1320,end:480}),false);
if(process.env.TZ==='Europe/Warsaw'){
 const a=Date.UTC(2026,9,25,0,30),b=Date.UTC(2026,9,25,1,30);
 assert.equal(new Date(a).getHours(),2);assert.equal(new Date(b).getHours(),2);
 for(const t of [a,b])assert.equal(api.quiet(t,{quiet:true,start:120,end:180}),true);
 assert.equal(api.quiet(Date.UTC(2026,2,29,1,30),{quiet:true,start:120,end:180}),false,'spring gap cannot invent local02:30');
 profile='dst';now=a-1000;model.setPrefs({enabled:true,quiet:false});
 model.add({...event,time:{start:a}});model.add({...event,time:{start:b}});
 now=a;assert.equal(model.tick({foreground:true}).delivered.length,1);
 now=b;assert.equal(model.tick({foreground:true}).delivered.length,1,'repeated local hour keeps UTC identities');
}
console.log('REMINDERS_PASS legacy/profile isolation, confirmed writes, dedupe/reload/expiry, quiet hours and UTC/DST');

profile='invalid-prefs';now=100000;storage[profile+':dc4iEpgRemindersV1']=[{key:'due',title:'Due',channel:'TV',start:now}];
storage[profile+':dc4iReminderPrefsV1']='invalid';assert.equal(model.tick({foreground:true}).reason,'invalid-preferences');
assert.equal(storage[profile+':dc4iEpgRemindersV1'].length,1,'invalid preferences do not consume reminders');
assert.equal(model.cancel(undefined).ok,false);
profile='failed-prefs';fail=true;assert.equal(model.setPrefs({enabled:false}).ok,false);assert.equal(model.prefs().enabled,true);fail=false;

for(const invalid of [{enabled:'false'},{quiet:'false'},{start:-1},{end:1440}]){let untouched=0;const strict=api.create({read:k=>k==='dc4iReminderPrefsV1'?invalid:[],write(){untouched++;}});assert.equal(strict.prefs().storageError,true);assert.equal(strict.setPrefs({enabled:true}).ok,false);assert.equal(untouched,0);}
