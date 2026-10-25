import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
// Synthetic guide integration, no network, Chrome, actual provider or LG.
class El {
 constructor(cls=''){this.className=cls;this.children=[];this.dataset={};this.style={};this.hidden=false;this.textContent='';this.classList={add(){},toggle(){}};this.ids={};}
 setAttribute(){} scrollIntoView(){}
 appendChild(el){this.children.push(el);return el;}
 set innerHTML(value){this.children=[];this.ids={};for(const m of value.matchAll(/id="([^"]+)"/g))this.ids[m[1]]=new El();}
 querySelector(selector){return this.ids[selector.slice(1)]||null;}
 querySelectorAll(selector){const names=selector.split('.').filter(Boolean);return this.children.filter(e=>names.every(n=>e.className.split(' ').includes(n)));}
}
let guide,root,focused,watched=0,requests=0;
const now=Date.UTC(2026,9,25,12),DAY=86400000,timers=[];
const TV={S:{uiLang:'en'},store:()=>null,readMetadataStorage:()=>null,
 el(tag,cls,html=''){const el=new El(cls);el.innerHTML=html;if(tag==='main')root=el;return el;},
 xtream:{open(){},getLiveCategories:()=>[],getAccounts:()=>[{label:'synthetic'}],
 ensureCatalog:async()=>[{id:'1',type:'live',title:'Provider Channel',epgId:'test.a'}],
 guideEpg:async()=>{requests++;return [
  {title:'Provider now',description:'Synthetic description',time:{start:now-10000,end:now+60000},stream_url:'https://private.invalid'},
  {title:'Tomorrow',time:{start:now+DAY,end:now+DAY+60000}},
  {title:'Bad timestamp',time:{start:now+DAY,end:now+DAY}}
 ];},guideWatch(){watched++;return true;}},
 addView(name,view){if(name==='guide')guide=view;},
 view:()=>'guide',rebuild(r,c){if(guide&&r!==undefined)focused=guide.nav()[r]?.[c||0];},
 closeView(){},toast(){}};
const context={window:{TV},document:{body:new El(),createElement:()=>new El()},
 Date:class extends Date{static now(){return now;}},setTimeout(fn){timers.push(fn);return timers.length;},
 clearTimeout(){},setInterval(){},Number,JSON};
for(const name of ['vod-guide-model.js','vod-rich-epg.js','vod-epg-metadata-ui.js','vod-channel-guide.js'])
 vm.runInNewContext(readFileSync('src/'+name,'utf8'),context);
guide.show();await Promise.resolve();timers.forEach(fn=>fn());
for(let i=0;i<6;i++)await Promise.resolve();
const el=id=>root.querySelector('#gd-'+id);
assert.equal(requests,1,'single already existing provider request');
assert.equal(el('now-title').textContent,'Provider now');
el('timeline-toggle').onok();
assert.equal(el('timeline').hidden,false);
assert.equal(el('airings').children.length,1,'only bounded current window');
assert.match(el('airings').children[0].textContent,/Provider now/);
assert.match(el('metadata').textContent,/freshness unknown/);
assert.equal(el('status').textContent,'Provider EPG');
assert.doesNotMatch(el('airings').children[0].textContent,/private.invalid/);
assert.equal(el('airings').children[0].onok,undefined);
el('day-next').onok();
assert.equal(el('airings').children.length,1);
assert.match(el('airings').children[0].textContent,/Tomorrow/);
assert.equal(el('status').textContent,'Provider EPG');
el('day-next').onok();
assert.equal(el('status').textContent,'No EPG in this period');
assert.match(el('airings').children[0].textContent,/No EPG in this period/);
el('day-prev').onok();
guide.keydown({keyCode:39});guide.keydown({keyCode:39});
assert.equal(focused,el('airings').children[0],'D-pad focus on provider metadata row');
assert.equal(requests,1,'day navigation must not fetch another provider guide');
TV.S.uiLang='pl';el('day-prev').onok();
assert.equal(el('status').textContent,'Dane EPG dostawcy');
assert.match(el('metadata').textContent,/aktualność nieznana/);
assert.equal(watched,0,'metadata never dispatches playback');
el('watch').onok();assert.equal(watched,1,'original live channel action remains');
console.log('EPG_PROVIDER_GUIDE_RUNTIME_PASS real guide VM, remote focus, PL/EN, source truth, no extra calls or secret');
