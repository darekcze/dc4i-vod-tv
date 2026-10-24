import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {resolve} from 'node:path';
const root=resolve(import.meta.dirname,'..');
const code=readFileSync(resolve(root,'src/vod-fallback.js'),'utf8');
function setup(options={}){
 const launches=[],lookups=[],stored={};
 const installed=options.installed??{'com.iptvsmarters.app':true,'io.strem.tv':true};
 const TV={
  onTV:true,S:{uiLang:'pl'},
  store(k,v){if(arguments.length===2){stored[k]=v;return v;}return stored[k]??null;},
  luna(url,params){
   lookups.push({url,params});
   if(url.includes('listLaunchPoints'))return Promise.resolve({launchPoints:options.launchPoints??[]});
   const id=params.appId;
   if(options.hanging?.includes(id))return new Promise(()=>{});
   return Promise.resolve({returnValue:true,exist:!!installed[id]});
  },
  findInstalledApp:options.fromList?()=>options.fromList:null,
  tmdb(path){
   if(path.includes('/external_ids'))return Promise.resolve({imdb_id:'tt0133093'});
   throw Error('Unexpected '+path);
  },
  launch(id,params){launches.push({id,params});},
  toast(){}
 };
 const context=vm.createContext({window:{TV},Promise,setTimeout,clearTimeout,encodeURIComponent,console});
 vm.runInContext(code,context);
 return {TV,launches,lookups};
}
const a=setup({hanging:['com.iptvsmarters.player','com.iptv.smarters']});
const start=Date.now();
assert.equal(await a.TV.vodPlayers.find('iptv'),'com.iptvsmarters.app');
assert.ok(Date.now()-start<800,'Smarters detection must not wait for unresponsive candidates');
await a.TV.vodPlayers.open('iptv','Nieznany film',{type:'movie',id:101});
assert.equal(a.launches[0].id,'com.iptvsmarters.app');
assert.equal(a.launches[0].params.search,'Nieznany film');
assert.equal(a.launches[0].params.searchQuery,'Nieznany film');
console.log('PASS: IPTV_SMARTERS_ID_AND_SEARCH_HINT');
const b=setup();
await b.TV.vodPlayers.open('stremio','Matrix',{type:'movie',id:603},{external_ids:{imdb_id:'tt0133093'}});
assert.equal(b.launches[0].id,'io.strem.tv');
assert.equal(b.launches[0].params.contentTarget,'stremio:///detail/movie/tt0133093/tt0133093');
console.log('PASS: STREMIO_IMDB_MOVIE_HANDOFF');
const c=setup();
await c.TV.vodPlayers.open('stremio','Game of Thrones',{type:'tv',id:1399},{external_ids:{imdb_id:'tt0944947'}});
assert.equal(c.launches[0].params.contentTarget,'stremio:///detail/series/tt0944947');
console.log('PASS: STREMIO_IMDB_SERIES_HANDOFF');
const d=setup();
await d.TV.vodPlayers.open('stremio','Matrix',{type:'movie',id:603});
assert.equal(d.launches[0].params.contentTarget,'stremio:///detail/movie/tt0133093/tt0133093');
console.log('PASS: STREMIO_TMDB_EXTERNAL_ID_LOOKUP');
const e=setup({installed:{},launchPoints:[{title:'Smarters Player',id:'com.actual.smarters.player'}]});
assert.equal(await e.TV.vodPlayers.find('iptv'),'com.actual.smarters.player');
console.log('PASS: SMRTERS_DETECTED_FROM_LAUNCHPOINTS_IF_ALLOWED');
const f=setup({fromList:{id:'com.iptvsmarters.app',title:'IPTV Smarters Player'},installed:{}});
assert.equal(await f.TV.vodPlayers.find('iptv'),'com.iptvsmarters.app');
assert.equal(f.lookups.length,0);
console.log('PASS: ROOTED_SERVICE_APP_LIST_MATCH');
const z=setup({installed:{}});
z.TV.onTV=false;
assert.equal(await z.TV.vodPlayers.open('iptv','Movie'),false);
assert.equal(z.launches.length,0);
console.log('PASS: SAFETY_NO_HOST_LAUNCH_ON_DESKTOP');
const fullApp=readFileSync(resolve(root,'build/dc4i-vodtv/app.js'),'utf8');
const startProbe=fullApp.indexOf('  function probeApps() {');
const endProbe=fullApp.indexOf('  // Apps row order',startProbe);
assert.ok(startProbe>0&&endProbe>startProbe,'Generated probe function not found');
const snippet=fullApp.slice(startProbe,endProbe);
const contexts={
 C:{APPS:[{id:'com.iptvsmarters.app',title:'IPTV Smarters Player',optional:true,
  candidates:['com.iptvsmarters.app','invalid-player-one','invalid-player-two']}]},
 apps:[],
 luna(url,params){
  if(params.appId==='com.iptvsmarters.app')return Promise.resolve({returnValue:true,exist:true});
  return new Promise(()=>{});
 },
 Promise,setTimeout,clearTimeout,Object
};
vm.runInNewContext(snippet,contexts);
const timer=Date.now();
await contexts.probeApps();
assert.equal(contexts.apps.length,1);
assert.equal(contexts.apps[0].id,'com.iptvsmarters.app');
assert.ok(Date.now()-timer<1000,'App tile should not wait for absent candidates');
console.log('PASS: IPTV_SMARTERS_TILE_DETECTED_WITH_HANGING_OTHER_IDS');
