import assert from 'node:assert/strict';
import {existsSync,readFileSync} from 'node:fs';
import vm from 'node:vm';
class El{constructor(){this.children=[];this.dataset={};}setAttribute(){}appendChild(x){this.children.push(x);return x;}set innerHTML(v){this.children=[];}scrollIntoView(){}}
let now=100000,profile='a',visible='visible',focused=true,fail=false,view='home';const data={},views={},messages=[],intervals=[],listeners={};
const TV={S:{uiLang:'en'},store(k,v){const key=profile+':'+k;if(arguments.length===2&&!fail)data[key]=JSON.stringify(v);return JSON.parse(data[key]||'null');},
 el:()=>new El(),addSetting(){},addView(k,v){views[k]=v;},openView(k){view=k;views[k].show();},closeView(){views[view].hide();view='home';},rebuild(){},view:()=>view,toast:s=>messages.push(s)};
const context={window:{TV,addEventListener(k,fn){listeners[k]=fn;}},document:{body:new El(),get visibilityState(){return visible;},hasFocus:()=>focused,addEventListener(k,fn){listeners[k]=fn;}},
 Date:class extends Date{static now(){return now;}},setInterval(fn){intervals.push(fn);}};
for(const name of ['vod-reminders.js','vod-reminder-ui.js'])if(existsSync('src/'+name))vm.runInNewContext(readFileSync('src/'+name,'utf8'),context);
assert.ok(TV.reminders);
const event={channelId:'1',channelTitle:'Channel',title:'Synthetic show',time:{start:now+60000}};
assert.equal(TV.reminders.add(event),true);assert.match(messages.pop(),/foreground/);
profile='b';TV.reminders.openSettings();assert.equal(views.reminders.nav().length,5,'new profile has no inherited reminders');
profile='a';TV.reminders.openSettings();let nav=views.reminders.nav();assert.equal(nav.length,6);
views.reminders.onFocus(nav[3][0]);views.reminders.keydown({keyCode:39});
assert.equal(JSON.parse(data['a:dc4iReminderPrefsV1']).start,1380,'remote changes quiet start');
now=event.time.start;visible='hidden';intervals.forEach(fn=>fn());assert.equal(messages.length,0);
visible='visible';focused=false;listeners.visibilitychange();assert.equal(messages.length,0);
focused=true;listeners.focus();assert.match(messages.pop(),/Synthetic show/);
intervals.forEach(fn=>fn());assert.equal(messages.length,0,'single delivery across timer/focus');
now+=1000;fail=true;assert.equal(TV.reminders.add({...event,time:{start:now+60000}}),false);assert.match(messages.pop(),/not saved/);fail=false;
TV.S.uiLang='pl';TV.reminders.add({...event,time:{start:now+60000}});assert.match(messages.pop(),/pierwszym planie/);
TV.reminders.openSettings();nav=views.reminders.nav();nav[5][0].onok();assert.equal(JSON.parse(data['a:dc4iEpgRemindersV1']).length,0,'remote cancel persisted');
assert.equal(TV.reminders.backgroundSupported,false);
console.log('REMINDER_UI_PASS profile reload/read, visible+focused only, remote quiet/cancel, write failures and PL/EN');
