import assert from 'node:assert/strict';
import {existsSync,readFileSync} from 'node:fs';
import vm from 'node:vm';
const ctx={window:{},setTimeout,clearTimeout};
if(existsSync('src/vod-archive-capabilities.js'))vm.runInNewContext(readFileSync('src/vod-archive-capabilities.js','utf8'),ctx);
const api=ctx.window.DC4IArchive;assert.ok(api,'archive state machine');
let now=100000,plays=0,stops=0,seeks=[],pauses=0;
const offer={providerEnabled:true,archiveHint:true,providerId:'fixture',streamId:'123',start:1000,end:2000};
const proof={providerEnabled:true,mediaTypeVerified:true,playbackStarted:true,canPause:true,seekable:[{start:0,end:60}],bufferedBytes:1024};
const transport={verify:async()=>proof,play:async()=>{plays++;return {started:true};},stop(){stops++;},pause(){pauses++;},seek(t){seeks.push(t);},bounds:()=>({seekable:[{start:0,end:60}],bufferedBytes:1024})};
let player=api.create({transport,now:()=>now});
assert.equal(player.offer({...offer,providerEnabled:false}).status,'unavailable');
assert.equal(await player.start(),false);assert.equal(plays,0);
assert.equal(player.offer(offer).status,'unverified');assert.equal(await player.start(),false);
assert.equal((await player.verify()).status,'ready');assert.equal(await player.start(),true);
assert.equal(player.state().status,'playing');assert.equal(player.pause(),true);assert.equal(pauses,1);
assert.equal(player.seek(30),true);assert.equal(player.seek(-1),false);assert.equal(player.seek(61),false);assert.equal(seeks.length,1);
now+=120000;assert.equal(player.seek(1),false,'expired proof cannot authorize seek');
player.stop();assert.equal(player.state().status,'stopped');
const unknown=api.create({now:()=>now});unknown.offer(offer);assert.equal((await unknown.verify()).status,'unverified');
player=api.create({now:()=>now,transport:{...transport,verify:async()=>({providerEnabled:false})}});player.offer(offer);assert.equal((await player.verify()).status,'unavailable');
player=api.create({now:()=>now,transport:{...transport,verify:async()=>({providerEnabled:true,mediaTypeVerified:false,playbackStarted:true})}});player.offer(offer);assert.equal((await player.verify()).status,'unverified');
player=api.create({now:()=>now,transport:{...transport,verify:async()=>{throw Error('https://user:secret@private.invalid');}}});player.offer(offer);await player.verify();assert.equal(player.state().status,'failed');assert.ok(!JSON.stringify(player.state()).includes('secret'));
let resolve;player=api.create({now:()=>now,transport:{...transport,verify:()=>new Promise(r=>{resolve=r;})}});player.offer(offer);const pending=player.verify();player.stop();resolve(proof);await pending;assert.equal(player.state().status,'stopped','late result cannot revive stopped session');
player=api.create({now:()=>now,timeoutMs:5,transport:{...transport,verify:()=>new Promise(()=>{})}});player.offer(offer);assert.equal((await player.verify()).status,'failed');
for(const bounds of [{seekable:[{start:0,end:500}],bufferedBytes:1024},{seekable:[{start:0,end:60}],bufferedBytes:999999999},{seekable:[{start:0,end:10},{start:20,end:30}],bufferedBytes:1024}]){
 player=api.create({now:()=>now,transport:{...transport,bounds:()=>bounds}});player.offer(offer);await player.verify();await player.start();assert.equal(player.seek(15),false,'oversize buffers and gaps denied');player.stop();
}
console.log('ARCHIVE_CAPABILITIES_PASS flags are hints, verification/cancel/deadline/failure, pause/seek/buffer bounds, no secret errors');

player=api.create({now:()=>now,transport:{...transport,verify:()=>new Promise(()=>{})}});player.offer(offer);
const cancelled=player.verify();player.stop();assert.equal((await cancelled).status,'stopped','stop cancels unresolved deadline');
let rejectSeek;player=api.create({now:()=>now,transport:{...transport,seek:()=>new Promise((_,reject)=>{rejectSeek=reject;})}});
player.offer(offer);await player.verify();await player.start();player.seek(5);player.stop();player.offer(offer);await player.verify();await player.start();
rejectSeek(Error('private credential-bearing transport error'));await Promise.resolve();await Promise.resolve();assert.equal(player.state().status,'playing','old control rejection cannot fail new session');player.stop();
assert.throws(()=>api.create({maxBufferBytes:67108865}),/limits/);

let incompleteCalls=0;
const incomplete=api.create({now:()=>now,transport:{verify:async()=>{incompleteCalls++;return proof;}}});
incomplete.offer(offer);assert.equal((await incomplete.verify()).status,'unverified');assert.equal(incompleteCalls,0,'no probe without playback and cleanup contract');
