import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
class El {
 constructor(cls=''){this.className=cls;this.children=[];this.dataset={};this.style={};this.hidden=false;this.textContent='';this.classList={add(){},toggle(){}};this.ids={};}
 setAttribute(){} scrollIntoView(){}
 appendChild(el){this.children.push(el);return el;}
 set innerHTML(value){this.children=[];this.ids={};for(const m of value.matchAll(/id="([^"]+)"/g))this.ids[m[1]]=new El();}
 querySelector(selector){return this.ids[selector.slice(1)]||null;}
 querySelectorAll(selector){const names=selector.split('.').filter(Boolean);return this.children.filter(e=>names.every(n=>e.className.split(' ').includes(n)));}
}
for(const providerState of ['success','empty','error']){
 let guide,root,clock=1792929600000,watched=0;
 const timers=[];const TV={S:{uiLang:'en'},store:()=>null,el(tag,cls,html=''){const el=new El(cls);el.innerHTML=html;if(tag==='main')root=el;return el;},
  xtream:{open(){},getLiveCategories:()=>[],getAccounts:()=>[{label:'fixture'}],ensureCatalog:async()=>[{id:'1',type:'live',title:'Channel',epgId:'a'}],
   guideEpg:async()=>{if(providerState==='error')throw Error('fixture');return providerState==='success'?[{title:'Provider',time:{start:clock,end:clock+10000}}]:[];},guideWatch(){watched++;return true;}},
  addView(name,view){guide=view;},view:()=>'guide',rebuild(){},closeView(){},toast(){}};
 const context={window:{TV},document:{body:new El(),createElement:()=>new El()},Date:class extends Date{static now(){return clock;}},setTimeout(fn){timers.push(fn);return timers.length;},clearTimeout(){},setInterval(){},Number,JSON};
 for(const name of ['vod-guide-model.js','vod-rich-epg.js','vod-epg-metadata-ui.js','vod-channel-guide.js'])vm.runInNewContext(readFileSync('src/'+name,'utf8'),context);
 TV.epgMetadata.acceptLocal({schemaVersion:1,source:'synthetic',fetchedAt:clock,channels:[{id:'a',names:['Channel']}],events:[{channelId:'a',title:'Local programme',start:clock-100,end:clock+3600000}]});
 guide.show();await Promise.resolve();timers.forEach(fn=>fn());await Promise.resolve();await Promise.resolve();
 const el=id=>root.querySelector('#gd-'+id);
 assert.equal(el('status').textContent,'Local XMLTV metadata',providerState);
 assert.equal(el('now-title').textContent,'Local programme');
 el('timeline-toggle').onok();assert.equal(el('timeline').hidden,false);
 assert.equal(el('now').hidden,true);
 const rows=el('airings').children;assert.equal(rows.length,1);assert.match(rows[0].textContent,/Local programme/);
 assert.equal(rows[0].onok,undefined);assert.equal(watched,0);
 el('day-prev').onok();assert.match(el('range').textContent,/5\/10/);
 el('timeline-toggle').onok();assert.equal(el('timeline').hidden,true);
 assert.equal(el('now').hidden,false);
 assert.ok(guide.nav()[4].every(x=>!x.hidden),'hidden day controls excluded from focus');
 el('watch').onok();assert.equal(watched,1,'existing channel playback retained');
}
console.log('GUIDE_RUNTIME_PASS local+provider success/empty/error, timeline toggle/day/focus, channel playback');
