import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
const context={window:{}, Date, JSON, Number, String, Array, Object, Math};
runInNewContext(readFileSync(new URL('../src/vod-rich-epg.js',import.meta.url),'utf8'),context);
const epg=context.window.DC4IRichEpg;
const source='review-orphan', now=1792890000000;
const valid={schemaVersion:1,source,fetchedAt:now,channels:[{id:'pl-hbo',names:['HBO Polska']}],events:[
  {channelId:'pl-hbo',title:'Valid Movie',start:now+100,end:now+10000}
]};
const orphan={...valid, events:[
  {channelId:'ghost-not-declared',title:'Unmapped Imported Movie',start:now+100,end:now+10000},
  valid.events[0]
]};
const fresh=epg.createCache({now:()=>now,ttlMs:1000,staleMs:2000});
assert.equal(fresh.put(valid).accepted,true);
assert.equal(fresh.put(orphan).reason,'partial','orphan should not silently replace valid cached source');
assert.deepEqual(Array.from(fresh.get(source).snapshot.events,e=>e.title),['Valid Movie']);
const cold=epg.createCache({now:()=>now,ttlMs:1000,staleMs:2000});
assert.equal(cold.put(orphan).accepted,true,'partial first import may still provide usable declared events');
const snapshot=cold.get(source).snapshot;
assert.equal(snapshot.partial,true,'orphan channel must be visibly marked partial');
assert.deepEqual(Array.from(snapshot.events,e=>e.channelId),['pl-hbo']);
assert.deepEqual(Array.from(epg.timeline(snapshot,'ghost-not-declared',now,now+11000)),[]);
assert.equal(epg.mapChannel({epg_channel_id:'ghost-not-declared'},snapshot.channels).status,'unmapped');
console.log('EPG_ORPHAN_CHANNEL_INTEGRITY_PASS');
