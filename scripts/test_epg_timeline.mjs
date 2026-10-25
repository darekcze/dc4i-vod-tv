import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const TV={S:{uiLang:'en'}},context={window:{TV},Date,Number,JSON,document:{}};
for(const name of ['vod-rich-epg.js','vod-epg-metadata-ui.js'])vm.runInNewContext(readFileSync('src/'+name,'utf8'),context);
let now=Date.UTC(2026,9,25,12),DAY=86400000;
const ui=TV.epgMetadata.create({now:()=>now});
assert.equal(typeof ui.timeline,'function','ten-day UI boundary');
const snap={schemaVersion:1,source:'synthetic',fetchedAt:now,channels:[{id:'a',names:['A']}],events:[]};
for(let d=-5;d<5;d++)snap.events.push({channelId:'a',title:'Day '+d,start:now+d*DAY,end:now+d*DAY+3600000,originalLanguage:'en',rating:{value:'4/5',system:'editorial'},year:'2026',categories:['Drama']});
ui.acceptLocal(snap);
for(let d=-5;d<5;d++){
 const view=ui.timeline({epgId:'a'},d);
 assert.equal(view.events.length,1);assert.equal(view.events[0].title,'Day '+d);
 assert.equal(view.from,now+d*DAY);assert.equal(view.to,view.from+DAY);
 assert.match(view.label,/synthetic/);
 assert.match(ui.describe(view.events[0]),/Original language: en/);
 assert.match(ui.describe(view.events[0]),/XMLTV rating.*unverified/);
 assert.equal(view.events[0].playable,false);
}
assert.throws(()=>ui.timeline({epgId:'a'},-6),/day/);
assert.throws(()=>ui.timeline({epgId:'a'},5),/day/);
assert.equal(ui.timeline({title:'A'},0).events.length,0);
TV.S.uiLang='pl';assert.match(ui.describe(ui.timeline({epgId:'a'},0).events[0]),/Język oryginalny/);
now+=3900000;assert.equal(ui.timeline({epgId:'a'},0).events.length,0);
console.log('EPG_TIMELINE_PASS ten rolling days, bounds, expiry, exact IDs, honest source fields');
