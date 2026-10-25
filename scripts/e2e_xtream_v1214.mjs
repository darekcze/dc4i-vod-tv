#!/usr/bin/env node
// Native Chrome DevTools smoke tests without Playwright or paid runners.
import {spawn} from 'node:child_process';
import {readFileSync,writeFileSync,mkdirSync,rmSync} from 'node:fs';
import {join,resolve} from 'node:path';
import {setTimeout as sleep} from 'node:timers/promises';
const root=resolve(import.meta.dirname,'..');
const webroot=join(root,'build','dc4i-vodtv');
const workspace=join(root,'private','ui-tests-xtream');
const port=28768,debugPort=29238;
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
 await waitFor(async()=>{try{return (await fetch('http://127.0.0.1:'+port+'/')).ok;}catch{return false;}},10000);
 const target=await waitFor(async()=>{try{const r=await fetch('http://127.0.0.1:'+debugPort+'/json/list');return (await r.json()).find(x=>x.type==='page'&&x.url.includes(String(port)));}catch{return null;}},10000);
 ws=new WebSocket(target.webSocketDebuggerUrl);
 await new Promise((ok,fail)=>{ws.addEventListener('open',ok,{once:true});ws.addEventListener('error',fail,{once:true});});
 ws.addEventListener('message',ev=>{const m=JSON.parse(ev.data);if(!m.id)return;const p=waiters.get(m.id);if(!p)return;waiters.delete(m.id);if(m.error)p.reject(Error(m.error.message));else p.resolve(m.result);});
 await cdp('Runtime.enable');await cdp('Page.enable');
 await cdp('Page.navigate',{url:'http://127.0.0.1:'+port+'/'});
 await waitFor(async()=>evaluate('!!(window.TV && window.TV.xtream && document.getElementById("dc4i-xtream"))'),13000);
 const tab=await evaluate('Array.from(document.querySelectorAll("#top .tab")).some(x=>x.textContent.includes("IPTV"))');
 assert(tab,'IPTV tab present');
 const mock=String.raw`(()=>{
  const oldFetch=window.fetch;
  window.fetch=(u,opts)=>{
   let s=String(u);
   if(s.startsWith('https://xtream.mock/')){
    const q=new URL(s).searchParams,action=q.get('action')||'auth';
    const response={auth:{user_info:{auth:1,status:'Active'}},
     get_live_categories:[{category_id:'5',category_name:'[PL] INFORMACJE'}],
     get_vod_categories:[{category_id:'6',category_name:'[PL] FILMY'}],
     get_series_categories:[{category_id:'7',category_name:'[PL] SERIALE'}],
     get_live_streams:[{stream_id:21,name:'TVP Info HD',category_id:'5'}],
     get_vod_streams:[{stream_id:31,name:'Film testowy',category_id:'6',container_extension:'mp4'}],
     get_series:[{series_id:41,name:'Serial testowy',category_id:'7'}],
     get_series_info:{episodes:{'1':[{id:55,title:'Pierwszy odcinek',container_extension:'mp4'}]}}};
    return Promise.resolve({ok:true,json:()=>Promise.resolve(response[action]||{})});
   }
   return oldFetch(u,opts);
  };
  TV.openView('xtream');
  TV.xtream.putAccount({label:'Test IPTV',host:'https://xtream.mock',username:'testuser',password:'testpassword'});
  return true;
})()`;
 await evaluate(mock);
 await waitFor(async()=>evaluate('document.getElementById("dx-status").textContent.includes("Katalog gotowy")'),8000);
 const loaded=await evaluate('({msg:document.getElementById("dx-status").textContent,accounts:TV.xtream.getAccounts(),cards:document.querySelectorAll("#dx-results .dx-item").length})');
 assert(loaded.accounts.length===1,'Playlist persisted');assert(loaded.cards>=3,'Catalog loaded');
 console.log('XTREAM_MOCK_CATALOG',JSON.stringify({message:loaded.msg,playlistCount:loaded.accounts.length,resultCards:loaded.cards}));
 const searchTitle=async (type,q)=>evaluate(`(()=>{document.getElementById('dx-query').value=${JSON.stringify(q)};document.getElementById('dx-type').value=${JSON.stringify(type)};document.getElementById('dx-search').onok();return [...document.querySelectorAll('#dx-results .dx-item b')].map(x=>x.textContent);})()`);
 let live=await searchTitle('live','TVP Info');assert(live.length===1&&live[0]==='TVP Info HD','TVP Info search');
 let movie=await searchTitle('movie','Film testowy');assert(movie.length===1&&movie[0]==='Film testowy','movie search');
 let series=await searchTitle('series','Serial testowy');assert(series.length===1&&series[0]==='Serial testowy','series search');
 console.log('XTREAM_SEARCH_LIVE_MOVIE_SERIES_OK');
 await evaluate('document.querySelector("#dx-results .dx-item").onok()');
 await waitFor(async()=>evaluate('document.querySelectorAll("#dx-episodelist .dx-item").length===1'));
 console.log('XTREAM_EPISODES_OK');
 await evaluate('document.querySelector("#dx-episodelist .dx-item").onok()');
 const player=await evaluate('({visible:!document.getElementById("dx-player").hidden,url:document.getElementById("dx-video").currentSrc||document.getElementById("dx-video").src})');
 assert(player.visible&&player.url.includes('/series/testuser/testpassword/55.mp4'),'native video player URL');
 console.log('XTREAM_PLAYER_OPEN_OK');
 await evaluate('document.getElementById("dx-playerclose").onok()');
 const snap=await cdp('Page.captureScreenshot',{format:'png'});writeFileSync(join(workspace,'xtream-v1214.png'),Buffer.from(snap.data,'base64'));
 await cdp('Page.reload',{ignoreCache:true});
 await waitFor(async()=>evaluate('!!(window.TV && TV.xtream)'),13000);
 const persisted=await evaluate('TV.xtream.getAccounts().length');
 assert(persisted===1,'local configuration survives app restart');
 console.log('XTREAM_STORAGE_PERSISTED_RELOAD_OK',persisted);
 console.log('XTREAM_E2E_PASS');
} catch(e){console.error('XTREAM_E2E_FAIL',e.stack||String(e));process.exitCode=1;
} finally {try{ws?.close();}catch{} chrome.kill('SIGTERM');server.kill('SIGTERM');await sleep(500);}
