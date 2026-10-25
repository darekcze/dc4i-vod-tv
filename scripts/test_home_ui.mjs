import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import vm from 'node:vm';
class El{constructor(){this.children=[];this.dataset={};this.hidden=false;this.classList={};}setAttribute(){}appendChild(x){this.children.push(x);return x;}set innerHTML(v){this.children=[];}scrollIntoView(){}}
let focused=null,visibleCards=[];
let clock=1792929600000,profile='a',source=[],stamp=0,view='home',opened=[],messages=[],refreshes=0;
const storage={},views={},settings=[],intervals=[];
const movie={title:'Synthetic',tmdb:{id:1,type:'movie'},vote_average:8,vote_count:300,genre_ids:[878],release_date:'2026-01-01',img:'https://image.tmdb.org/t/p/w500/test.jpg'};
const TV={S:{uiLang:'en'},P:{},homeCandidates:()=>source,homeCandidatesStamp:()=>stamp,
 store(k,v){const key=profile+':'+k;if(arguments.length===2)storage[key]=JSON.stringify(v);return JSON.parse(storage[key]||'null');},
 focusHomeCard(el){focused=el;},el(){return new El();},addView(k,v){views[k]=v;},addSetting(r){settings.push(r);},refresh(){refreshes++;},rebuild(){},view:()=>view,
 openView(k){view=k;views[k].show();},closeView(){views[view].hide();view='home';},toast(x){messages.push(x);},itemOk(x){opened.push(x);},
 personalized:{settings:()=>({otherMin:0}),history:()=>[]},epgMetadata:{homeEvents:()=>[]}};
TV.readMetadataStorage=k=>TV.store(k);
const context={window:{TV},document:{createElement:()=>new El(),body:new El(),querySelector:()=>focused,querySelectorAll:()=>visibleCards},setInterval(fn){intervals.push(fn);},Date:class extends Date{static now(){return clock;}}};
for(const name of ['vod-recommendations.js','vod-home-rails.js','vod-home-ui.js'])if(existsSync('src/'+name))vm.runInNewContext(readFileSync('src/'+name,'utf8'),context);
assert.ok(TV.homeRails,'Home UI installed');
let rows=TV.homeRails.rows();assert.equal(rows[0].items[0].kind,'status');
source=[movie];stamp=clock;rows=TV.homeRails.rows();assert.ok(rows.some(r=>r.id==='films'));
let card=TV.homeRails.card(rows.find(r=>r.id==='films').items[0]);card.onok();assert.equal(opened[0].tmdb.id,1);
TV.homeRails.openSettings();let nav=views['home-layout'].nav();nav[2][0].onok(); // disable now
assert.ok(!TV.homeRails.config().enabled.includes('now'));
views['home-layout'].onFocus(nav[3][0]);views['home-layout'].keydown({keyCode:37});
assert.equal(TV.homeRails.config().order[0],'today');
TV.closeView();profile='b';source=[];stamp=0;assert.ok(TV.homeRails.config().enabled.includes('now'));
assert.equal(TV.homeRails.rows()[0].items[0].kind,'status','other profile cannot read cache');
profile='a';clock+=3600000;rows=TV.homeRails.rows();assert.match(rows.find(r=>r.id==='films').title,/Stale cache/);
assert.ok(!TV.homeRails.config().enabled.includes('now'),'profile order/settings restored');
TV.S.uiLang='pl';assert.match(TV.homeRails.rows().find(r=>r.id==='films').title,/Nieaktualny cache/);
clock+=86400000;assert.equal(TV.homeRails.rows()[0].items[0].kind,'status','expired cold start');
TV.homeRails.card({kind:'airing',title:'Upcoming',start:clock,end:clock+1000,source:'synthetic',playable:false}).onok();assert.equal(opened.length,1,'airing cannot dispatch title/player action');
assert.ok(refreshes>0);
console.log('HOME_UI_PASS actual store namespaces, remote settings/order, profile switching, cold/stale/expired, honest actions');

const priorRefreshes=refreshes;view='home';intervals.forEach(fn=>fn());assert.equal(refreshes,priorRefreshes+1);
view='home-layout';intervals.forEach(fn=>fn());assert.equal(refreshes,priorRefreshes+1,'no timer redraw of settings');
view='home';profile='a';clock=1792929600000;source=[movie];stamp=clock;TV.homeRails.rows();
const workingStore=TV.store;TV.store=function(k,v){return arguments.length===2?null:workingStore.call(TV,k);};
source=[{...movie,title:'Fresh live item',tmdb:{id:99,type:'movie'}}];stamp=clock+100;clock=stamp;
assert.equal(TV.homeRails.rows().find(r=>r.id==='films').items[0].tmdb.id,99,'failed persistence cannot replace live catalogue with old cache');
profile='new';assert.equal(TV.homeRails.rows().find(r=>r.id==='films').items[0].tmdb.id,99,'live rows work without any cache');
TV.store=workingStore;

const oldCard=TV.homeRails.card({kind:'airing',homeRowId:'now',channelId:'1',start:1,end:2,source:'synthetic',title:'A'});
focused=oldCard;const saved=TV.homeRails.captureFocus();
const moved=TV.homeRails.card({kind:'airing',homeRowId:'missedToday',channelId:'1',start:1,end:2,source:'synthetic',title:'A'});
visibleCards=[moved];TV.homeRails.restoreFocus(saved);assert.equal(focused,moved,'follow same airing after temporal row change');
assert.equal(card.item.tmdb.id,1,'custom canonical cards retain upstream focused-item contract');
const next=TV.homeRails.card({kind:'airing',homeRowId:'now',channelId:'2',start:3,end:4,source:'synthetic',title:'B'});
visibleCards=[next];TV.homeRails.restoreFocus(saved);assert.equal(focused,next,'missing item falls back to same row');

for(const value of [{app:{id:'com.synthetic.app'}},{item:{tmdb:{id:987,type:'movie'},title:'Baseline'}}]){
 const before={...value},after={...value};focused=before;const identity=TV.homeRails.captureFocus();
 visibleCards=[moved,after,next];TV.homeRails.restoreFocus(identity);assert.equal(focused,after,'baseline identity survives rail insertion');
 focused=after;visibleCards=[before];TV.homeRails.restoreFocus(identity);assert.equal(focused,before,'baseline identity survives rail removal');
}
TV.readMetadataStorage=()=>{throw Error('corrupt');};assert.equal(TV.homeRails.config().storageError,true);const prior=JSON.stringify(storage);TV.homeRails.openSettings();views['home-layout'].nav()[1][0].onok();assert.equal(JSON.stringify(storage),prior,'unreadable layout is never overwritten');assert.match(messages.at(-1),/zapisać|save/);
