import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import vm from 'node:vm';
class Element {
 constructor(){this.children=[];this.attrs={};this.textContent='';}
 setAttribute(k,v){this.attrs[k]=v;}
 appendChild(el){this.children.push(el);return el;}
}
const TV={S:{uiLang:'en'}};
const context={window:{TV},document:{createElement:()=>new Element()},Date,Number,JSON};
vm.runInNewContext(readFileSync('src/vod-rich-epg.js','utf8'),context);
if(existsSync('src/vod-epg-metadata-ui.js'))vm.runInNewContext(readFileSync('src/vod-epg-metadata-ui.js','utf8'),context);
assert.ok(TV.epgMetadata,'UI adapter installed');
let now=1000000;
const ui=TV.epgMetadata.create({now:()=>now,ttlMs:1000,staleMs:2000});
const snapshot={schemaVersion:1,source:'local-test',fetchedAt:now,channels:[{id:'a',names:['Channel']}],events:[{channelId:'a',title:'<b>Example</b>',description:'test',start:now-100,end:now+10000}],partial:true};
const provider=[{title:'Provider',time:{start:now,end:now+10}}];
assert.match(ui.guide({epgId:'a'},provider).label,/freshness unknown/);
assert.equal(ui.acceptLocal(snapshot).accepted,true);
assert.equal(ui.guide({title:'Channel'},provider).events,provider,'name suggestion cannot override provider');
const view=ui.guide({epgId:'a'},provider);
assert.equal(view.events[0].title,'<b>Example</b>');assert.equal(view.events[0].playable,false);
assert.match(view.label,/local-test.*Fresh.*Partial/);
assert.match(view.label,/tracks unverified/);
let host=new Element();ui.renderDetails(host,'<b>Example</b>',provider);
assert.equal(host.children[0].attrs.translate,'no');
assert.match(host.children[0].textContent,/Provider EPG.*freshness unknown/);
assert.match(host.children[1].textContent,/title match unverified/);
assert.match(host.children[1].textContent,/<b>Example<\/b>/);
assert.ok(host.children.every(e=>!e.onok&&!e.onclick),'metadata grants no playback actions');
now+=1000;assert.match(ui.guide({epgId:'a'},[]).label,/Stale/);
TV.S.uiLang='pl';assert.match(ui.guide({epgId:'a'},[]).label,/Nieaktualne.*Niepełne/);
host=new Element();ui.renderDetails(host,'<b>Example</b>',[]);assert.match(host.children[0].textContent,/tytułu niezweryfikowane/);
now+=2000;assert.equal(ui.guide({epgId:'a'},provider).events,provider);
host=new Element();ui.renderDetails(host,'<b>Example</b>',[]);assert.equal(host.children.length,0);
assert.equal(ui.acceptLocal({...snapshot,source:'https://user:password@example.invalid'}).accepted,false);
ui.clear();assert.equal(ui.guide({epgId:'a'},[]).label,'');
console.log('EPG_METADATA_UI_PASS PL/EN, exact mapping, freshness, expiry, partial, text-only details, no playback grants');
