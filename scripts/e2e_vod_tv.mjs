#!/usr/bin/env node
// Native Chrome DevTools smoke tests without Playwright or paid runners.
import {spawn} from 'node:child_process';
import {readFileSync,writeFileSync,mkdirSync,rmSync} from 'node:fs';
import {join,resolve} from 'node:path';
import {setTimeout as sleep} from 'node:timers/promises';
const root=resolve(import.meta.dirname,'..');
const webroot=join(root,'build','dc4i-vodtv');
const workspace=join(root,'private','ui-tests');
const port=28767,debugPort=29237;
mkdirSync(workspace,{recursive:true});
const server=spawn('python3',['-m','http.server',String(port),'--bind','127.0.0.1','--directory',webroot],{stdio:'ignore'});
const chrome=spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',[
 '--headless=new','--disable-gpu','--no-first-run','--disable-extensions',
 '--no-default-browser-check','--disable-background-networking',
 '--user-data-dir='+join(workspace,'profile'),
 '--remote-debugging-port='+debugPort,'--remote-allow-origins=*',
 '--window-size=1920,1080','http://127.0.0.1:'+port+'/'
],{stdio:'ignore'});
function assert(x,msg){if(!x)throw Error('E2E_ASSERT: '+msg);}
let ws,reqId=0;
const waiters=new Map();
async function waitFor(fn,ms=12000){const now=Date.now();while(Date.now()-now<ms){let r=await fn();if(r)return r;await sleep(250);}throw Error('E2E_TIMEOUT');}
async function cdp(method,params={}){
 const id=++reqId;
 const msg={id,method,params};
 return new Promise((resolve,reject)=>{
   let timer=setTimeout(()=>{waiters.delete(id);reject(Error('CDP_TIMEOUT '+method));},12000);
   waiters.set(id,{resolve(value){clearTimeout(timer);resolve(value)},reject(error){clearTimeout(timer);reject(error)}});
   ws.send(JSON.stringify(msg));
 });
}
async function evaluate(code){
 const r=await cdp('Runtime.evaluate',{expression:code,returnByValue:true,awaitPromise:true});
 if(r.exceptionDetails)throw Error('JS_RUNTIME '+r.exceptionDetails.text);
 return r.result?.value;
}
try{
 await waitFor(async()=>{try{const r=await fetch('http://127.0.0.1:'+port+'/');return r.ok;}catch{return false;}},10000);
 const target=await waitFor(async()=>{try{const res=await fetch('http://127.0.0.1:'+debugPort+'/json/list');const j=await res.json();return j.find(x=>x.type==='page'&&x.url.includes(String(port)));}catch{return null;}});
 ws=new WebSocket(target.webSocketDebuggerUrl);
 await new Promise((ok,fail)=>{ws.addEventListener('open',ok,{once:true});ws.addEventListener('error',fail,{once:true});});
 ws.addEventListener('message',(ev)=>{const m=JSON.parse(ev.data);if(!m.id)return;const p=waiters.get(m.id);if(!p)return;waiters.delete(m.id);if(m.error)p.reject(Error(m.error.message));else p.resolve(m.result);});
 await cdp('Runtime.enable');
 await cdp('Page.enable');
 await cdp('Page.navigate',{url:'http://127.0.0.1:'+port+'/'});
 await waitFor(async()=>evaluate('Boolean(window.TV && document.querySelector("#top"))'),16000);
 const intro=await evaluate('({title:document.title, lang:window.TV.S.uiLang, region:window.TV.C.REGION, city:window.TV.S.weatherCity,rootOnly:window.getComputedStyle(document.querySelector("[data-q=picture]")).display})');
 assert(intro.title==='DC4I VOD TV','title');
 assert(intro.region==='PL','region Poland');
 assert(intro.lang==='pl','language Polish');
 assert(intro.city==='Warsaw','default city Warszawa');
 assert(intro.rootOnly==='none','root-only picture button hidden');
 console.log('E2E_BOOT_PL',JSON.stringify(intro));
 await waitFor(async()=>evaluate('Boolean(document.querySelector("#grid .app") && document.querySelector("#rows"))'),9000);
 const smarters=await evaluate('Array.from(document.querySelectorAll("#grid .app")).filter(x=>/Smarters Player/i.test(x.innerText)).length');
 // Optional Smarters launcher tile depends on webOS discovery. The five search actions are always visible.
 console.log('E2E_SMARTERS_TILE_VISIBLE',smarters);
 // Deterministic movie offers: TMDB search includes one title in Poland, one without subscriptions.
 const installMock=String.raw`(()=> {
  const orig=TV.tmdb;
  TV.tmdb=function(path,q){
   if(path==='search/multi')return Promise.resolve({results:[
    {id:101,media_type:'movie',title:'Film dostępny',backdrop_path:'/x.jpg',poster_path:'/p.jpg',overview:''},
    {id:202,media_type:'movie',title:'Film bez streamingu',backdrop_path:'/y.jpg',poster_path:'/p.jpg',overview:''}
   ]});
   if(path==='movie/101/watch/providers')return Promise.resolve({results:{PL:{flatrate:[{provider_name:'Netflix'}]}}});
   if(path==='movie/202/watch/providers')return Promise.resolve({results:{PL:{}}});
   if(path==='movie/101')return Promise.resolve({id:101,overview:'',credits:{cast:[]},genres:[],videos:{results:[]},
      'watch/providers':{results:{PL:{flatrate:[{provider_name:'Netflix'}]}}},recommendations:{results:[]},
      external_ids:{imdb_id:'tt0133093'}});
   if(path==='movie/202')return Promise.resolve({id:202,overview:'',credits:{cast:[]},genres:[],videos:{results:[]},
      'watch/providers':{results:{PL:{}}},recommendations:{results:[]}});
   return orig(path,q);
  };
  TV.openView('search');
  const keys=[...document.querySelectorAll('#skb .skey')];
  for(const ch of 'matrix')keys.find(x=>x.textContent.trim()===ch).onok();
  return true;
})()`;
 await evaluate(installMock);
 const providersInSearch=await evaluate(`Array.from(document.querySelectorAll("#syt .vx-engine")).map(x=>x.textContent.trim())`);
 assert(providersInSearch.join('|')==='YouTube|Kodi|Plex|Stremio|Smarters Player','search has exactly five external services');
 console.log('E2E_SEARCH_PROVIDERS',providersInSearch.join('|'));
 const tabs=await evaluate(`Array.from(document.querySelectorAll('#top .dc4i-top-navigation .tab')).map(x=>x.textContent.trim())`);
 assert(tabs.join('|')==='VOD|TV|IPTV|Filmy|Seriale|Szukaj|Aplikacje','ordered Polish menu');
 const filters=await evaluate(`Array.from(document.querySelectorAll('#sfilters .vod-filter')).map(x=>x.textContent.trim())`);
 assert(filters.join('|')==='Wszystkie|VOD|TV|IPTV|Filmy|Seriale','six filter names');
 const languages=await evaluate(`Array.from(document.querySelectorAll('#slangs .language-filter')).map(x=>x.textContent.trim())`);
 assert(languages.join('|')==='Polskie|Angielskie|Wszystkie języki','language options');
 console.log('E2E_TOP_NAVIGATION',tabs.join('|'),'FILTERS',filters.join('|'),'LANGUAGES',languages.join('|'));
 const g=await evaluate(`Array.from(document.querySelectorAll('#top .dc4i-top-navigation .tab')).map(x=>{const r=x.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom};})`);
 assert(g.length===7&&g.every((x,i)=>x.left>=0&&x.right<=1920&&x.bottom<=1080&&(i===0||x.left>=g[i-1].right-4)),'seven tabs fit viewport without overlap');
 console.log('E2E_MENU_GEOMETRY',JSON.stringify(g));
 await evaluate(`document.querySelectorAll('#sfilters .vod-filter')[1].onok()`);
 await waitFor(async()=>evaluate('document.querySelectorAll("#sres .card").length===1 && document.querySelector("#sres").innerText.includes("Netflix")'),8000);
 const available=await evaluate('({title:document.querySelector("#sresTitle").textContent,count:document.querySelectorAll("#sres .card").length, label:document.querySelector("#sres .vod-status").textContent})');
 assert(available.count===1&&available.label.includes('Netflix'),'streaming filter');
 console.log('E2E_STREAMING_AVAILABLE',JSON.stringify(available));
 const searchSnap=await cdp('Page.captureScreenshot',{format:'png'});
 writeFileSync(join(workspace,'search-v1213.png'),Buffer.from(searchSnap.data,'base64'));
 await evaluate('document.querySelector("#sres .card").onok()');
 await waitFor(async()=>evaluate(`document.querySelectorAll("#details .dexternal .vx-engine").length===5`),6000);
 const availableActions=await evaluate('document.querySelector("#details .dexternal").innerText');
 const geometry=await evaluate(`Array.from(document.querySelectorAll("#details .dexternal .vx-engine")).map(e=>{const r=e.getBoundingClientRect();return {text:e.textContent,top:r.top,bottom:r.bottom,left:r.left,right:r.right}})`);
 assert(geometry.length===5&&geometry.every(x=>x.bottom<=1080&&x.right<=1920&&x.top>=0),'five detail providers visible inside TV viewport');
 console.log('E2E_DETAIL_GEOMETRY',JSON.stringify(geometry));
 assert(['YouTube','Kodi','Plex','Stremio','Smarters Player'].every(x=>availableActions.includes(x)),
   'external-player actions should be available for ALL titles, including Netflix-supported titles');
 console.log('E2E_PLAYERS_ON_AVAILABLE_TITLE',availableActions.replaceAll('\n',' | '));
 const detailSnap=await cdp('Page.captureScreenshot',{format:'png'});
 writeFileSync(join(workspace,'details-v1213.png'),Buffer.from(detailSnap.data,'base64'));
 await evaluate('window.TV.closeView()');
 await evaluate(`document.querySelectorAll('#sfilters .vod-filter')[0].onok()`);
 const other=await evaluate('({count:document.querySelectorAll("#sres .card").length,label:document.querySelector("#sres .vod-status")?.textContent})');
 assert(other.count===2&&other.label.includes('Netflix'),'all categories include unavailable titles');
 console.log('E2E_OTHERS',JSON.stringify(other));
 await evaluate(`document.querySelectorAll('#sres .card')[1].onok()`);
 await waitFor(async()=>evaluate(`document.querySelectorAll("#details .dexternal .vx-engine").length===5`),6000);
 const fallback=await evaluate('document.querySelector("#details .dexternal").innerText');
 assert(await evaluate(`document.querySelector("#details .dbtns").innerText.includes("Brak w wybranych serwisach")`), "missing VOD shows exact message");
 assert(['YouTube','Kodi','Plex','Stremio','Smarters Player'].every(x=>fallback.includes(x)),'fallback buttons');
 console.log('E2E_DETAILS_FALLBACK',fallback.replaceAll('\n',' | '));
 // Provider catalog mock validates local Xtream filters without disclosing credentials.
 await evaluate('window.TV.closeView()');
 await evaluate(`(()=>{window.TV.xtream.getAccounts=()=>[{id:'mock'}];
 window.TV.xtream.searchCatalog=async()=>[
   {type:'live',id:'301',title:'[PL] MATRIX TV',group:'[PL] TV',icon:''},
   {type:'movie',id:'302',title:'[PL] MATRIX Film',group:'[PL] Filmy',icon:''},
   {type:'series',id:'303',title:'[PL] MATRIX Serial',group:'[PL] Seriale',icon:''},
   {type:'series',id:'304',title:'[EN] MATRIX Series',group:'[EN] Series',icon:''}
 ];return true})()`);
 await evaluate(`document.querySelectorAll('#sfilters .vod-filter')[0].onok()`);
 await waitFor(async()=>evaluate(`document.querySelectorAll('#sres .xtream-result').length===3`),6000);
 console.log('E2E_XTREAM_ALL',await evaluate(`Array.from(document.querySelectorAll('#sres .xtream-result .ttl')).map(x=>x.textContent).join('|')`));
 await evaluate(`document.querySelectorAll('#sfilters .vod-filter')[4].onok()`);
 await waitFor(async()=>evaluate(`document.querySelectorAll('#sres .xtream-result').length===1`),6000);
 console.log('E2E_XTREAME_MOVIES',await evaluate(`document.querySelector('#sres .xtream-result .ttl').textContent`));
 await evaluate(`document.querySelectorAll('#sfilters .vod-filter')[5].onok()`);
 await waitFor(async()=>evaluate(`document.querySelectorAll('#sres .xtream-result').length===1`),6000);
 console.log('E2E_XTREAME_SERIES_PL',await evaluate(`document.querySelector('#sres .xtream-result .ttl').textContent`));
 await evaluate(`document.querySelectorAll('#slangs .language-filter')[1].onok()`);
 await waitFor(async()=>evaluate(`document.querySelectorAll('#sres .xtream-result').length===1`),6000);
 console.log('E2E_XTREAME_SERIES_EN',await evaluate(`document.querySelector('#sres .xtream-result .ttl').textContent`));
 // Identity regression: the same KATSEYE-style TMDB ID must add Xtream as
 // a second source on ONE detail card rather than duplicate/drop it.
 await evaluate(`document.querySelectorAll('#slangs .language-filter')[0].onok()`);
 await evaluate(`(()=>{TV.xtream.searchCatalog=async()=>[
 {type:'movie',id:'501',tmdb:'101',title:'[PL] Film dostępny (2026)',year:'2026',rating:'4.2',group:'[PL] Movies',icon:''},
 {type:'movie',id:'502',tmdb:'999',title:'[PL] Film bez streamingu (2026)',year:'2026',group:'[PL] Movies',icon:''}
 ];return true;})()`);
 await evaluate(`document.querySelectorAll('#sfilters .vod-filter')[0].onok()`);
 await waitFor(async()=>evaluate(`document.querySelectorAll('#sres .card').length>=2`),7000);
 const merged=await evaluate(`(()=>{const r=Array.from(document.querySelectorAll('#sres .card'));return {cards:r.length,links:TV.titleSources.get({id:101,media_type:'movie'}).map(x=>x.id)}})()`);
 assert(merged.cards===3 && merged.links.join(',')==='501','merged TMDB + Xtream source and unmerged mismatched source');
 await evaluate(`document.querySelector('#sres .card').onok()`);
 await waitFor(async()=>evaluate(`Array.from(document.querySelectorAll('#details .dbtns .dbtn')).some(x=>x.textContent.includes('Xtream Filmy'))`),7000);
 console.log('E2E_MERGED_DETAILS',await evaluate(`Array.from(document.querySelectorAll('#details .dbtns .dbtn')).map(x=>x.textContent).join(' | ')`));

 await evaluate(`window.TV.xtream.searchEpg=async()=>[
 {title:'Film dostępny',channelTitle:'[PL] HBO HD',channelId:'100',time:{start:Date.now()+7200000,end:Date.now()+10800000},duration:60,state:'future',archiveFlag:false}
 ]`);
 await evaluate(`document.querySelector('#sres .card') && document.querySelector('#details .depg') ? true : false`);
 // Reopen details to trigger an EPG lookup with a future airing.
 await evaluate('window.TV.closeView()');
 await evaluate(`document.querySelector('#sres .card').onok()`);
 await waitFor(async()=>evaluate(`document.querySelector('#details .depg').textContent.includes('HBO HD')`),5000);
 const epgInfo=await evaluate(`document.querySelector('#details .depg').innerText`);
 assert(epgInfo.includes('Przypomnij'),'future HBO airing has in-app reminder');
 console.log('E2E_EPG_FUTURE',epgInfo.replaceAll('\n',' | '));
 await evaluate('window.TV.closeView()');
 // Owner's Xtream catalogue cards open detail first with poster and rating.
 await evaluate(`TV.xtream.openItem({type:'movie',id:'902',title:'[PL] KATSEYE Wild Hearts 2026',rating:'4.2',tmdb:'1728113',icon:'https://image.tmdb.org/t/p/w500/test.jpg',year:'2026',group:'[PL] Movies'})`);
 const detailState=await evaluate(`({visible:!document.querySelector('#dx-details').hidden,title:document.querySelector('#dx-detailtitle').textContent,rating:document.querySelector('#dx-detailrating').textContent,poster:document.querySelector('#dx-detailposter').getAttribute('src'),play:!!document.querySelector('#dx-detailplay')})`);
 assert(detailState.visible&&detailState.title.includes('KATSEYE')&&detailState.rating.includes('4.2')&&detailState.poster&&detailState.play,'Xtream poster + rating + details');
 console.log('E2E_XTREAM_DETAILS',JSON.stringify(detailState));
 await evaluate('window.TV.closeView()');
 await evaluate('window.TV.closeView()');
 // Weather with deterministic mock data prevents dependency on current forecast.
 const mockWeather=String.raw`(()=> {
  const original=window.fetch;
  const data={current:{time:'2026-10-24T12:00',temperature_2m:11,weather_code:3,is_day:1,
    apparent_temperature:9,relative_humidity_2m:65,wind_speed_10m:12},
   daily:{time:['2026-10-24','2026-10-25'],weather_code:[3,2],precipitation_probability_max:[10,20],
    temperature_2m_max:[13,14],temperature_2m_min:[6,7],
    sunrise:['2026-10-24T07:00','2026-10-25T07:01'],sunset:['2026-10-24T17:00','2026-10-25T16:59']},
   hourly:{time:Array.from({length:24},(_,i)=>'2026-10-24T'+String(i).padStart(2,'0')+':00'),
    weather_code:Array(24).fill(3),is_day:Array(24).fill(1),
    temperature_2m:Array(24).fill(10)}};
  TV.store('weatherLoc',null);
  window.fetch=function(url,options){
    let u=String(url);
    if(u.includes('geocoding-api.open-meteo.com'))return Promise.resolve({ok:true,json:()=>Promise.resolve({results:[{country_code:'PL',name:'Warszawa',latitude:52.23,longitude:21.01}]})});
    if(u.includes('api.open-meteo.com/v1/forecast'))return Promise.resolve({ok:true,json:()=>Promise.resolve(data)});
    return original(url,options);
  };
  TV.openView('weather');
  return true;
})()`;
 await evaluate(mockWeather);
 await waitFor(async()=>evaluate('document.querySelector("#wxpanel")?.innerText.includes("Wilgotność")'),6500);
 const weather=await evaluate('({city:document.querySelector("#wxpanel .wxcity")?.textContent,desc:document.querySelector("#wxpanel .wxcond")?.textContent, body:document.querySelector("#wxpanel").innerText})');
 assert(weather.city==='Warszawa','Warsaw weather');
 assert(weather.desc.includes('Pochmurno'),'Polish weather code');
 assert(weather.body.includes('Odczuwalna')&&weather.body.includes('Zmień miasto'),'Polish weather labels');
 console.log('E2E_WEATHER_PL',JSON.stringify({city:weather.city,desc:weather.desc,labels:true}));
 console.log('E2E_PASS');
} catch(e) {
 console.error('E2E_FAIL',e.stack||String(e));
 process.exitCode=1;
} finally {
 try{ws?.close();}catch{}
 chrome.kill('SIGTERM');server.kill('SIGTERM');
 await sleep(500);
}
