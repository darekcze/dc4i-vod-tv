import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import vm from 'node:vm';
const root=resolve(import.meta.dirname,'..');
const js=readFileSync(resolve(root,'src/vod-handoff.js'),'utf8');
async function scenario(response,error=false){
 const calls=[];const messages=[];
 const TV={onTV:true,S:{uiLang:'pl'},toast:x=>messages.push(x),
  luna:(method,params)=>{calls.push({method,params});return Promise.resolve({returnValue:true});}};
 const fetch=(url,opts)=>{calls.push({url,opts});return error?Promise.reject(Error('offline')):Promise.resolve({ok:true,json:()=>Promise.resolve(response)})};
 const context=vm.createContext({window:{TV},Promise,JSON,Error,String,fetch,encodeURIComponent,setTimeout:(fn,n)=>{const x=setTimeout(fn,n);x.unref?.();return x;},clearTimeout});
 vm.runInContext(js,context);
 return {TV,calls,messages};
}
let s=await scenario({ok:true,action:'open-series'});
assert.equal(await s.TV.vodHandoff.kodi('Breaking Bad',{type:'tv',id:1396}),true);
assert.equal(s.calls[0].url,'http://127.0.0.1:18761/open');
assert.deepEqual(JSON.parse(s.calls[0].opts.body),{title:'Breaking Bad',type:'series',tmdb:'1396'});
assert.equal(s.calls[1].params.params.dc4i.tmdb,'1396');
s=await scenario(null,true);
assert.equal(await s.TV.vodHandoff.kodi('The Matrix',{type:'movie',id:603}),true);
assert.equal(s.calls[1].params.params.dc4i.tmdb,'603');
s=await scenario({ok:false,error:'not-in-provider'});
assert.equal(await s.TV.vodHandoff.kodi('Not found',{id:999999,type:'movie'}),false);
assert.equal(s.calls.length,1);
s=await scenario({ok:true});
assert.equal(await s.TV.vodHandoff.plexSearch('The Matrix'),true);
assert.ok(s.calls.at(-1).params.params.target.includes('search?query=The%20Matrix'));
assert.equal(await s.TV.vodHandoff.youtubeSearch('The Matrix'),true);
assert.ok(s.calls.at(-1).params.params.contentTarget.includes('q=The%20Matrix'));
console.log('V128_HANDOFF_TESTS_PASS: ALIVE_KODI, COLD_START, NOT_FOUND, PLEX, YOUTUBE');
