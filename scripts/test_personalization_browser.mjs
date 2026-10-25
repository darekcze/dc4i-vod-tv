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
 '--user-data-dir='+join(workspace,'test-only-v1218-'+process.pid),
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
 const target=await waitFor(async()=>{try{const r=await fetch('http://127.0.0.1:'+debugPort+'/json/list');const pages=await r.json();return pages.find(x=>x.type==='page'&&x.url.includes(String(port)));}catch{return null;}},10000);
 ws=new WebSocket(target.webSocketDebuggerUrl);
 await new Promise((ok,fail)=>{ws.addEventListener('open',ok,{once:true});ws.addEventListener('error',fail,{once:true});});
 ws.addEventListener('message',ev=>{const m=JSON.parse(ev.data);if(!m.id)return;const p=waiters.get(m.id);if(!p)return;waiters.delete(m.id);if(m.error)p.reject(Error(m.error.message));else p.resolve(m.result);});
 await cdp('Runtime.enable');await cdp('Page.enable');
 await cdp('Page.navigate',{url:'http://127.0.0.1:'+port+'/'});
 await waitFor(async()=>evaluate("!!(window.TV && TV.personalized && TV.homeCandidates)"),16000);
 await waitFor(async()=>evaluate("document.querySelectorAll('#rows .row').length > 0"),24000);
 const boot=await evaluate("({version:document.title,profile:TV.P.name,region:TV.C.REGION, settings:TV.personalized.settings(),rows:document.querySelectorAll('#rows .row').length})");
 assert(boot.settings.sciFiMin===6&&boot.settings.horrorMin===9&&boot.settings.favouriteGenre==='scifi','default ranking prefs');
 assert(boot.region==='PL','default country PL');

 const fixture="(()=>{TV.homeCandidates=()=>[{id:5001,tmdb:{type:'movie',id:5001},title:'SciFi QA',img:'https://image.tmdb.org/t/p/w500/a.jpg',bg:'',sub:'Test',meta:'2026 · Film',src:'TMDB',genre_ids:[878],vote_average:8.3,vote_count:700,popularity:80,release_date:'2026-03-01'},{id:5002,tmdb:{type:'movie',id:5002},title:'Horror QA',img:'https://image.tmdb.org/t/p/w500/b.jpg',bg:'',sub:'Test',meta:'2026 · Film',src:'TMDB',genre_ids:[27],vote_average:9.4,vote_count:700,popularity:90,release_date:'2026-03-01'},{id:5003,tmdb:{type:'movie',id:5003},title:'Romance QA',img:'https://image.tmdb.org/t/p/w500/c.jpg',bg:'',sub:'Test',meta:'2026 · Film',src:'TMDB',genre_ids:[10749],vote_average:7.7,vote_count:700,popularity:70,release_date:'2026-03-01'},{id:5004,tmdb:{type:'movie',id:5004},title:'Unrated QA',img:'https://image.tmdb.org/t/p/w500/d.jpg',bg:'',sub:'Test',meta:'2026 · Film',src:'TMDB',genre_ids:[878],vote_average:0,vote_count:0,popularity:70,release_date:'2026-03-01'}];TV.refresh();return true;})()";
 await evaluate(fixture);
 await waitFor(async()=>evaluate("document.querySelector('#rows .row:first-child h3')?.textContent==='Dopasowane do profilu'"),7000);
 const ranked=await evaluate("Array.from(document.querySelectorAll('#rows .row:first-child .card')).map(c=>({title:c.item.title,match:c.querySelector('.reco-match')?.textContent,score:c.item.recoScore}))");
 assert(ranked.length===3 && ranked.some(x=>x.title==='Horror QA') && !ranked.some(x=>x.title==='Unrated QA'),'ranked cards, no invented unrated item');
 assert(ranked.every(x=>x.match.includes('Dopasowanie') && x.score<=100),'badge shows score/reason');
 const overlaps=await evaluate("Array.from(document.querySelectorAll('#rows .row:first-child .card')).map(card=>{const badge=card.querySelector('.reco-match'),title=card.querySelector('.ttl');if(!badge||!title)return true;return badge.getBoundingClientRect().bottom > title.getBoundingClientRect().top-4;})");
 assert(overlaps.every(x=>!x),'recommendation labels must not obscure card title');

 console.log('E2E_PROFILE_HOME_ROW',JSON.stringify(ranked));
 const shot=await cdp('Page.captureScreenshot',{format:'png'});
 writeFileSync(join(workspace,'home-v1218-personalized.png'),Buffer.from(shot.data,'base64'));

 // Open full user settings by actual click navigation (same document click path as TV remote pointer).
 await evaluate("document.querySelector('#top [data-act=settings]').click()");
 await waitFor(async()=>evaluate("TV.view()==='quick'"),3000);
 await evaluate("document.querySelector('[data-q=settings]').click()");
 await waitFor(async()=>evaluate("TV.view()==='settings'"),3000);
 const rows=await evaluate("Array.from(document.querySelectorAll('#settings .srow h4')).map(x=>x.textContent)");
 assert(rows.filter(x=>x.startsWith('Polecane:')).length>=9,'all recommendation controls in settings');
 assert(rows.some(x=>x.includes('horrory')),'horror control visible');
 const before=await evaluate("TV.S.recoHorrorMode");
 assert(before==='high','default high-rated-only horror');
 await evaluate("(()=>{const head=Array.from(document.querySelectorAll('#settings .srow h4')).find(x=>x.textContent==='Polecane: horrory');const chip=Array.from(head.closest('.srow').querySelectorAll('.chip')).find(x=>x.textContent==='Nie pokazuj horrorów');chip.click();return true})()");
 await evaluate("document.querySelector('#sclose').click()");
 await waitFor(async()=>evaluate("TV.S.recoHorrorMode==='hide' && TV.view()==='home'"),14000);
 const persisted=await evaluate("TV.store('settings').recoHorrorMode");
 assert(persisted==='hide','horror setting persisted on reload');
 // Correct profile context and privacy.
 await evaluate("(()=>{const a=TV.store('recommendationOpensV1')||[];TV.itemOk({tmdb:{id:5001,type:'movie'},genre_ids:[878],title:'SciFi QA'});return true})()");
 const opened=await evaluate("TV.store('recommendationOpensV1')");
 assert(opened.length>0 && opened.at(-1).action==='opened' && !opened.some(x=>x.action==='watched'),'opening never recorded as watched');
 await evaluate("localStorage.profiles=JSON.stringify([{id:'default',name:'Primary',color:'#8ab4f8',kids:false,hideApps:[]},{id:'p-other',name:'Other',color:'#8ab4f8',kids:false,hideApps:[]}]);localStorage.profile='p-other';location.reload()");
 await waitFor(async()=>evaluate("TV.P.name==='Other' && TV.S.recoHorrorMode==='high' && TV.personalized.history().length===0"),14000);
 const second=await evaluate("({name:TV.P.name,history:TV.personalized.history().length,mode:TV.S.recoHorrorMode,otherProfileSettings:localStorage.getItem('p-other.settings')})");
 assert(second.history===0 && second.mode==='high','profiles do not inherit sensitive preferences/history');
 console.log('E2E_PROFILE_ISOLATION',JSON.stringify(second));
 console.log('E2E_PERSONALIZATION_PASS');

} catch(e) {
 console.error('E2E_FAIL',e.stack||String(e));
 process.exitCode=1;
} finally {
 try{ws?.close();}catch{}
 chrome.kill('SIGTERM');server.kill('SIGTERM');
 await sleep(500);
 try{rmSync(join(workspace,'test-only-v1218-'+process.pid),{recursive:true,force:true});}catch{}
}
