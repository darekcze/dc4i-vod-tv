import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import vm from 'node:vm';
const root=resolve(import.meta.dirname,'..');
const code=readFileSync(resolve(root,'src/vod-fallback.js'),'utf8');
function setup(options={}){
 const launches=[],logs=[],toast=[],saved={};
 const installed=options.installed===undefined?{'com.smarterstvplayers.net':true,'io.strem.tv':true}:options.installed;
 const launchAllowed=options.launchAllowed || installed;
 const TV={
  onTV:true,S:{uiLang:'pl'},
  store(k,v){if(arguments.length===2){saved[k]=v;return v;}return saved[k]??null;},
  luna(method,params){
   logs.push({method,params});
   if(method.endsWith('/listLaunchPoints')){
    if(options.deniedList)return Promise.reject({errorText:'Denied method call'});
    return Promise.resolve({launchPoints:options.launchPoints||[]});
   }
   if(method.endsWith('/getAppLoadStatus')){
    if(options.hanging?.includes(params.appId))return new Promise(()=>{});
    if(options.deniedGetStatus)return Promise.reject({errorText:'Denied method call'});
    return Promise.resolve({returnValue:true,exist:!!installed[params.appId]});
   }
   if(method.endsWith('/launch')){
    launches.push({id:params.id,params:params.params});
    if(options.launchHang?.includes(params.id))return new Promise(()=>{});
    if(!launchAllowed[params.id])return Promise.reject({errorCode:-101,errorText:'The app was not found'});
    return Promise.resolve({returnValue:true});
   }
   throw Error('Unexpected luna '+method);
  },
  findInstalledApp:options.fromList?()=>options.fromList:null,
  tmdb(path){if(path.includes('/external_ids'))return Promise.resolve({imdb_id:'tt0133093'});throw Error(path);},
  toast(t){toast.push(t);}
 };
 const context=vm.createContext({window:{TV},Promise,setTimeout,clearTimeout,encodeURIComponent,console,Date});
 vm.runInContext(code,context);
 return {TV,launches,logs,toast,saved};
}
const a=setup({hanging:['com.iptvsmarters.player','com.iptv.smarters']});
assert.equal(await a.TV.vodPlayers.find('iptv'),'com.smarterstvplayers.net');
assert.equal(await a.TV.vodPlayers.open('iptv','Własny film',{type:'movie',id:101}),true);
assert.equal(a.launches[0].id,'com.smarterstvplayers.net');
assert.equal(a.launches[0].params.search,'Własny film');
console.log('PASS: SMARTERS_CONFIRMED_APP_AND_SEARCH_HINT');
const b=setup();
assert.equal(await b.TV.vodPlayers.open('stremio','Matrix',{type:'movie',id:603},{external_ids:{imdb_id:'tt0133093'}}),true);
assert.equal(b.launches[0].id,'io.strem.tv');
assert.equal(b.launches[0].params.contentTarget,'stremio:///detail/movie/tt0133093/tt0133093');
console.log('PASS: STREMIO_NATIVE_MOVIE_DETAIL_URL');
const c=setup();
await c.TV.vodPlayers.open('stremio','Series',{type:'tv',id:1399},{external_ids:{imdb_id:'tt0944947'}});
assert.equal(c.launches[0].params.contentTarget,'stremio:///detail/series/tt0944947');
console.log('PASS: STREMIO_NATIVE_SERIES_DETAIL_URL');
const d=setup();
assert.equal(await d.TV.vodPlayers.openWeb('Matrix',{type:'movie',id:603},{external_ids:{imdb_id:'tt0133093'}}),false);
// The default mocks do not include the browser; verify actual URL was attempted.
assert.equal(d.launches[0].id,'com.webos.app.browser');
assert.equal(d.launches[0].params.target,'https://web.stremio.com/#/detail/movie/tt0133093/tt0133093');
console.log('PASS: STREMIO_WEB_SELECTED_TITLE_URL');
const e=setup({installed:{},launchAllowed:{'com.smarterstvplayers.net':true},deniedList:true});
assert.equal(await e.TV.vodPlayers.find('iptv'),null);
assert.equal(await e.TV.vodPlayers.open('iptv','Warsaw film'),true);
assert.ok(e.launches.some(x=>x.id==='com.smarterstvplayers.net'));
assert.equal(e.saved.vodInstalledPlayerIds.iptv ,'com.smarterstvplayers.net');
console.log('PASS: VERIFIED_TV_APP_ID_LAUNCH');
const f=setup({installed:{},launchAllowed:{},deniedList:true});
assert.equal(await f.TV.vodPlayers.open('iptv','No film'),false);
assert.ok(f.toast.some(x=>x.includes('Nie udało się uruchomić IPTVSmartersPlayer')));
assert.ok(f.saved.vodNativeDiagnostics122.some(x=>x.phase==='launch' && x.error.includes('found')));
console.log('PASS: UNKNOWN_APP_ID_DIAGNOSTICS_AND_TRUTHFUL_ERROR');
const g=setup({installed:{},launchAllowed:{},launchPoints:[{title:'IPTVSmartersPlayer',id:'com.smarterstvplayers.net'}]});
assert.equal(await g.TV.vodPlayers.find('iptv') ,'com.smarterstvplayers.net');
console.log('PASS: DISCOVERY_BY_INSTALLED_APP_TITLE');
const h=setup({fromList:{id:'com.smarterstvplayers.net',title:'IPTVSmartersPlayer'},installed:{}});
assert.equal(await h.TV.vodPlayers.find('iptv'),'com.smarterstvplayers.net');
assert.equal(h.logs.length,0);
console.log('PASS: ROOT_SERVICE_LIST_FIRST');
const z=setup({installed:{}});
z.TV.onTV=false;
assert.equal(await z.TV.vodPlayers.open('iptv','Movie'),false);
assert.equal(z.launches.length,0);
console.log('PASS: NO_LAUNCH_FROM_DESKTOP');
const source=readFileSync(resolve(root,'build/dc4i-vodtv/app.js'),'utf8');
const start=source.indexOf('  function probeApps() {'),end=source.indexOf('  // Apps row order',start);
assert.ok(start>0&&end>start);
const simulated={
 C:{APPS:[{id:'com.smarterstvplayers.net',title:'IPTVSmartersPlayer',playerKey:'iptv',
    optional:true,keepTile:true,candidates:['com.smarterstvplayers.net']}]},
 apps:[],luna(){return Promise.resolve({exist:false,returnValue:true});},
 Promise,setTimeout,clearTimeout,Object
};
vm.runInNewContext(source.slice(start,end),simulated);
await simulated.probeApps();
assert.equal(simulated.apps.length,1);
assert.equal(simulated.apps[0].id,'vod-smarters-unverified');
assert.equal(simulated.apps[0].unverified,true);
assert.equal(simulated.apps[0].playerKey,'iptv');
console.log('PASS: SMARTERS_TILE_IS_NOT_HIDDEN_WHEN_UNVERIFIED');
console.log('NATIVE_PLAYER_UNIT_PASS');

const pro=setup({installed:{'com.iptvsmarters.app':true},launchAllowed:{'com.iptvsmarters.app':true},deniedList:true});
assert.equal(await pro.TV.vodPlayers.open('iptv','Film'),false);
assert.equal(pro.launches.some(x=>x.id==='com.iptvsmarters.app'),false);
console.log('PASS: PRO_VARIANT_NOT_LAUNCHED');
