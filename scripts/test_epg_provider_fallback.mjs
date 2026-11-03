import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

// Source-only runtime contract. This is not a browser, webOS or real-feed test.
const TV={S:{uiLang:'en'}};
const context={window:{TV},Date,Number,JSON};
for(const name of ['vod-rich-epg.js','vod-epg-metadata-ui.js'])
  vm.runInNewContext(readFileSync('src/'+name,'utf8'),context);
const now=Date.UTC(2026,9,25,12),DAY=86400000;
const adapter=TV.epgMetadata.create({now:()=>now});
const provider=[
 {title:'Provider today',description:'Today',time:{start:now-1000,end:now+60000},
  account:'secret-account',stream_url:'https://private.invalid/?password=secret'},
 {title:'Provider tomorrow',time:{start:now+DAY,end:now+DAY+60000}},
 {title:'Invalid duration',time:{start:now+DAY,end:now+DAY}},
 {title:'Outside range',time:{start:now+12*DAY,end:now+13*DAY}}
];
const today=adapter.timeline({epgId:'a'},0,provider,'success');
assert.equal(today.status,'Provider EPG');
assert.equal(today.events.length,1);
assert.equal(today.events[0].title,'Provider today');
assert.equal(today.events[0].playable,false);
assert.equal(today.events[0].tracks.audio,'unknown');
assert.equal(today.events[0].provenance.kind,'provider');
assert.match(today.label,/freshness unknown/);
assert.doesNotMatch(JSON.stringify(today),/secret-account|private\.invalid|password/);
assert.equal(adapter.timeline({epgId:'a'},1,provider,'success').events[0].title,'Provider tomorrow');
assert.equal(adapter.timeline({epgId:'a'},2,provider,'loading').status,'Loading programme...');
assert.equal(adapter.timeline({epgId:'a'},2,provider,'error').status,'Could not load EPG');
assert.equal(adapter.timeline({epgId:'a'},2,provider,'success').status,'No EPG in this period');
const local={schemaVersion:1,source:'synthetic',fetchedAt:now,
 channels:[{id:'a',names:['A']}],events:[{channelId:'a',title:'Local',start:now,end:now+60000}]};
assert.equal(adapter.acceptLocal(local).accepted,true);
assert.equal(adapter.timeline({epgId:'a'},0,provider,'error').events[0].title,'Local');
assert.equal(adapter.timeline({epgId:'a'},1,provider,'success').events[0].title,'Provider tomorrow');
assert.equal(adapter.timeline({title:'A'},0,provider,'success').events[0].title,'Provider today',
 'name-only XMLTV suggestion must not block existing Xtream EPG');
TV.S.uiLang='pl';
assert.equal(adapter.timeline({epgId:'a'},1,provider,'success').status,'Dane EPG dostawcy');
const many=Array.from({length:230},(_,i)=>({
 title:'Broadcast '+i,time:{start:now+i*1000,end:now+(i+1)*1000}}));
assert.equal(adapter.timeline({epgId:'unmapped'},0,many,'success').events.length,201,
 '200 visible rows plus a truncation sentinel');
assert.throws(()=>adapter.timeline({epgId:'a'},5,provider),/day/);
const guide=readFileSync('src/vod-channel-guide.js','utf8');
assert.match(guide,/epgMetadata\.timeline\(selected,timelineDay,events,providerState\)/);
assert.match(guide,/status\(view\.status\)/);
assert.match(guide,/empty\.textContent=view\.status/);
console.log('EPG_PROVIDER_FALLBACK_PASS 10-day provider coverage, source truth, no playback/secrets, precedence, limits, PL/EN');
