import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const app=readFileSync('build/dc4i-vodtv/app.js','utf8'),xt=readFileSync('build/dc4i-vodtv/vod-xtream.js','utf8');
assert.ok(!xt.includes("var reminders=TV.store('dc4iEpgRemindersV1')"),'old cached profile list removed');
assert.ok(!xt.includes("TV.toast('Teraz w TV: '"),'legacy delivery timer removed');
let forwarded,opened=0;const TV={reminders:{add:e=>{forwarded=e;return true;},openSettings(){opened++;}}};
const context={TV,SROWS:[{key:'reminderSettings',opts:[['edit','Configure']]}],draft:{}};
const helper=xt.slice(xt.indexOf('function remindEpg(event){'),xt.indexOf('function chosenEpgChannels(){'));
vm.runInNewContext(helper,context);const event={channelId:'1',time:{start:1}};assert.equal(context.remindEpg(event),true);assert.equal(forwarded,event);
const choose=app.slice(app.indexOf('  function choose(e)'),app.indexOf('  // ---------- quick settings'));vm.runInNewContext(choose,context);
context.choose({dataset:{r:'0',i:'0'}});assert.equal(opened,1);
assert.ok(xt.includes("if(entry.state==='future')return remindEpg(entry);"),'future archive dispatcher preserves reminder entrypoint');
assert.ok(readFileSync('build/dc4i-vodtv/features/details.js','utf8').includes('TV.xtream.remindEpg(e)'));
assert.equal(JSON.parse(readFileSync('build/dc4i-vodtv/appinfo.json')).version,'1.2.19');
console.log('REMINDER_INTEGRATION_PASS single delivery system, existing future entrypoints, actual settings routing, version preserved');
// Exercise generated adapters: upstream store swallows corrupt JSON, strict reader must not.
const storage={},P={prefix:'profile-a:'};let deny=false;
const localStorage=new Proxy(storage,{get(target,k){if(k==='getItem')return key=>{if(deny)throw Error('denied');return Object.hasOwn(target,key)?target[key]:null;};return target[k];}});
const adapter={localStorage,P,window:{},Date};
vm.runInNewContext(app.slice(app.indexOf('  function store('),app.indexOf('  // ---------- settings')),adapter);
assert.equal(typeof adapter.readReminderStorage,'function','strict generated reminder reader exists');
vm.runInNewContext(readFileSync('src/vod-reminders.js','utf8'),adapter);
const model=adapter.window.DC4IReminders.create({read:adapter.readReminderStorage,write:adapter.store,now:()=>100000});
const reminder=[{key:'1:100000',title:'Synthetic',channel:'One',start:100000}];
storage['profile-a:dc4iEpgRemindersV1']=JSON.stringify(reminder);storage['profile-a:dc4iReminderPrefsV1']='{bad-json';
assert.equal(adapter.store('dc4iReminderPrefsV1'),null,'actual upstream helper masks parse errors');
assert.equal(model.tick({foreground:true}).reason,'invalid-preferences');assert.equal(JSON.parse(storage['profile-a:dc4iEpgRemindersV1']).length,1);
assert.equal(model.setPrefs({enabled:true}).ok,false);assert.equal(storage['profile-a:dc4iReminderPrefsV1'],'{bad-json');
for(const raw of ['', 'null']){storage['profile-a:dc4iReminderPrefsV1']=raw;assert.equal(model.tick({foreground:true}).reason,'invalid-preferences');}
delete storage['profile-a:dc4iReminderPrefsV1'];deny=true;assert.equal(model.tick({foreground:true}).reason,'invalid-preferences');deny=false;
P.prefix='profile-b:';assert.equal(model.list().items.length,0);P.prefix='profile-a:';assert.equal(model.tick({foreground:true}).delivered.length,1,'truly missing preferences use defaults');
console.log('REMINDER_GENERATED_STORAGE_PASS corrupt/read-failed preferences pause without removal; missing/profile semantics preserved');

const css=readFileSync('build/dc4i-vodtv/dc4i.css','utf8');
assert.ok(css.includes('#toast{z-index:100;}'),'toast above opaque settings panel z-index30');
