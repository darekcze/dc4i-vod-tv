#!/usr/bin/env node
// Native Chrome DevTools smoke tests without Playwright or paid runners.
import {spawn} from 'node:child_process';
import {readFileSync,writeFileSync,mkdirSync,rmSync} from 'node:fs';
import {join,resolve} from 'node:path';
import {setTimeout as sleep} from 'node:timers/promises';
const root=resolve(import.meta.dirname,'..');
const webroot=join(root,'build','dc4i-boringtv');
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
 await waitFor(async()=>evaluate('document.querySelectorAll("#sres .card").length===1 && document.querySelector("#sres").innerText.includes("Netflix")'),8000);
 const available=await evaluate('({title:document.querySelector("#sresTitle").textContent,count:document.querySelectorAll("#sres .card").length, label:document.querySelector("#sres .vod-status").textContent})');
 assert(available.count===1&&available.label.includes('Netflix'),'streaming filter');
 console.log('E2E_STREAMING_AVAILABLE',JSON.stringify(available));
 await evaluate('document.querySelectorAll("#sfilters .schip")[1].onok()');
 const other=await evaluate('({count:document.querySelectorAll("#sres .card").length,label:document.querySelector("#sres .vod-status")?.textContent})');
 assert(other.count===1&&other.label.includes('Brak streamingu'),'non-PL fallback');
 console.log('E2E_OTHERS',JSON.stringify(other));
 await evaluate('document.querySelector("#sres .card").onok()');
 await waitFor(async()=>evaluate('document.querySelector("#details .dbtns")?.innerText.includes("Stremio")'),6000);
 const fallback=await evaluate('document.querySelector("#details .dbtns").innerText');
 assert(fallback.includes('Stremio')&&fallback.includes('IPTV Smarters Player'),'fallback buttons');
 console.log('E2E_DETAILS_FALLBACK',fallback.replaceAll('\n',' | '));
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
