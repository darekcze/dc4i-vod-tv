#!/usr/bin/env node
// Native Chrome DevTools smoke tests without Playwright or paid runners.
import {spawn} from 'node:child_process';
import {browserPath} from './browser_path.mjs';
const chromePath = browserPath();
import {readFileSync,writeFileSync,mkdirSync,rmSync} from 'node:fs';
import {join,resolve} from 'node:path';
import {setTimeout as sleep} from 'node:timers/promises';
const root=resolve(import.meta.dirname,'..');
const webroot=join(root,'build','dc4i-vodtv');
const workspace=join(root,'private','guide-ui-tests');
const port=28779,debugPort=29249;
mkdirSync(workspace,{recursive:true});
const server=spawn('python3',['-m','http.server',String(port),'--bind','127.0.0.1','--directory',webroot],{stdio:'ignore'});
const chrome=spawn(chromePath,[
 '--headless=new','--disable-gpu','--no-first-run','--disable-extensions',
 '--no-default-browser-check','--disable-background-networking',
 '--user-data-dir='+join(workspace,'test-only-'+process.pid),
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
 if(r.exceptionDetails)throw Error('JS_RUNTIME '+(r.exceptionDetails.exception?.description||r.exceptionDetails.text)+' expr: '+code.slice(0,120));
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
 await waitFor(async()=>evaluate('Boolean(window.TV && window.TV.xtream && window.TV.guide && document.querySelector("#top"))'),16000);

 const sourceMock =
  "(()=>{var now=Date.now();var records=["+
  "{id:'11',type:'live',title:'TVP 1 HD',group:'[PL] Ogólne',category:'7',icon:'http://127.0.0.1:"+port+"/icon.png'},"+
  "{id:'12',type:'live',title:'HBO HD',group:'[PL] Filmowe',category:'8',icon:''},"+
  "{id:'13',type:'live',title:'TVN24',group:'[PL] Ogólne',category:'7',icon:''}];"+
  "TV.xtream.getAccounts=()=>[{id:'a',label:'Moja TV'}];"+
  "TV.xtream.getLiveCategories=()=>[{id:'7',type:'live',title:'[PL] Ogólne'},{id:'8',type:'live',title:'[PL] Filmowe'}];"+
  "TV.xtream.ensureCatalog=()=>Promise.resolve(records);"+
  "TV.xtream.guideEpg=(ch)=>Promise.resolve(ch.id==='11'?["+
   "{title:'Daily News',description:'News from Poland',time:{start:now-600000,end:now+600000}},"+
   "{title:'Next Show',time:{start:now+600000,end:now+4200000}}]:[]);"+
  "TV.xtream.guideWatch=(ch)=>{window.guideWatched=ch.id;return true;};"+
  "TV.xtream.open('all');return true;})()";
 await evaluate(sourceMock);
 try{await waitFor(async()=>evaluate('Boolean(window.TV.guide && !document.querySelector("#dc4i-guide").hidden && document.querySelectorAll("#gd-groups .gd-group").length===4)'),6500); }catch(err){
  console.error('GUIDE_INIT_DEBUG',await evaluate('({view:TV.view(),groups:document.querySelectorAll("#gd-groups .gd-group").length,guide:!!TV.guide,hidden:document.querySelector("#dc4i-guide")?.hidden,status:document.querySelector("#gd-status")?.textContent,last:TV.store("guideLastChannelV1"),group:TV.store("guideSelectedGroupV1")})'));
  throw err;
 }
 await waitFor(async()=>evaluate('document.querySelector("#gd-now-title").textContent==="Daily News"'),6500);
 const initial=await evaluate('({view:TV.view(),groups:[...document.querySelectorAll("#gd-groups .gd-group-name")].map(x=>x.textContent),channels:document.querySelectorAll("#gd-channels .gd-channel").length,firstLogo:!!document.querySelector("#gd-channels .gd-channel img"),now:document.querySelector("#gd-now-title").textContent,next:document.querySelector("#gd-next-title").textContent,progress:document.querySelector("#gd-progress").style.width})');
 assert(initial.view==='guide','IPTV opens guide');
 assert(initial.groups.join('|')==='Wszystkie kanały|Ulubione|[PL] Ogólne|[PL] Filmowe','real groups');
 assert(initial.channels===3 && initial.firstLogo,'channel icons and count');
 console.log('GUIDE_DEBUG_INITIAL',JSON.stringify(initial));
 const diagnosis=await evaluate('(async function(){var a=await TV.xtream.guideEpg({id:"11"});var e=document.querySelector("#gd-next-title");return {raw:a.map(x=>x.title),shown:e.textContent,translate:document.querySelector("#dc4i-guide").getAttribute("translate"),closest:Boolean(e.closest("[translate=no]")),locale:window.DC4I_I18N?.language};})()');
 console.log('GUIDE_I18N_DEBUG',JSON.stringify(diagnosis));
 assert(initial.now==='Daily News' && initial.next==='Next Show','selected now-next EPG');
 assert(parseFloat(initial.progress)>40 && parseFloat(initial.progress)<61,'progress is relative to current time');
 console.log('GUIDE_E2E_INITIAL',JSON.stringify(initial));
 const rects=await evaluate('([".gd-group-pane",".gd-channel-pane",".gd-detail"].map(s=>{const r=document.querySelector(s).getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width}}))');
 assert(rects.length===3 && rects.every(x=>x.left>=0&&x.right<=1920&&x.top>=100&&x.bottom<=1080),'no clipped TV panes');
 assert(rects[0].right<rects[1].left && rects[1].right<rects[2].left,'three non-overlapping columns');
 console.log('GUIDE_E2E_GEOMETRY',JSON.stringify(rects));
 const shot=await cdp('Page.captureScreenshot',{format:'png'});
 writeFileSync(join(workspace,'guide-1219.png'),Buffer.from(shot.data,'base64'));
 await evaluate('TV.guide.key(39)');
 await evaluate('TV.guide.key(40)');
 await waitFor(async()=>evaluate('document.querySelector("#gd-current-channel").textContent==="HBO HD"'),6000);
 const missing=await evaluate('({name:document.querySelector("#gd-current-channel").textContent,msg:document.querySelector("#gd-status").textContent})');
 assert(missing.name==='HBO HD','remote focuses next channel');
 await evaluate('document.querySelector("#gd-favorite").onok()');
 const favorite=await evaluate('({saved:TV.store("guideFavoritesV1"),label:document.querySelector("#gd-favorite").textContent,groups:[...document.querySelectorAll("#gd-groups .gd-group")].map(x=>x.textContent)})');
 assert(favorite.saved.length===1 && favorite.saved[0]==='12' && favorite.label.includes('Usuń'),'favorite saved per profile');
 assert(favorite.groups[1].includes('1'),'favorite group count');
 await evaluate('document.querySelector("#gd-watch").onok()');
 assert(await evaluate('window.guideWatched==="12"'),'Watch dispatches exact selected channel');
 await evaluate('TV.guide.key(37)');
 await evaluate('TV.guide.key(37)');
 await evaluate('document.querySelectorAll("#gd-groups .gd-group")[1].onok()');
 const favlist=await evaluate('({group:document.querySelector("#gd-groups .gd-selected")?.dataset.group,channels:[...document.querySelectorAll("#gd-channels .gd-channel-name")].map(x=>x.textContent)})');
 assert(favlist.group==='favorites' && favlist.channels.join('|')==='HBO HD','favorites group includes saved channel');
 await evaluate('document.querySelector("#gd-config").onok()');
 assert(await evaluate('TV.view()==="xtream"'),'playlist edit navigates into existing Xtream config');
 await evaluate('TV.closeView()');
 console.log("GUIDE_RETURN_DEBUG",await evaluate(`({view:TV.view(),guideHidden:document.querySelector("#dc4i-guide").hidden,xtreamHidden:document.querySelector("#dc4i-xtream").hidden})`));
 assert(await evaluate('TV.view()==="guide" && !document.querySelector("#dc4i-guide").hidden'),
    'Back from playlist configuration restores visible guide');
 console.log('GUIDE_E2E_CONFIG_RETURN_PASS');

 console.log('GUIDE_E2E_FAVORITES',JSON.stringify(favlist));
 await evaluate('TV.closeView()');
 console.log("GUIDE_RETURN_DEBUG",await evaluate(`({view:TV.view(),guideHidden:document.querySelector("#dc4i-guide").hidden,xtreamHidden:document.querySelector("#dc4i-xtream").hidden})`));
 assert(await evaluate('document.querySelector("#dc4i-guide").hidden'), 'Back hides guide');
 console.log('GUIDE_E2E_PASS');
} catch(e) {
 console.error('E2E_FAIL',e.stack||String(e));
 process.exitCode=1;
} finally {
 try{ws?.close();}catch{}
 chrome.kill('SIGTERM');server.kill('SIGTERM');
 await sleep(500);
}
