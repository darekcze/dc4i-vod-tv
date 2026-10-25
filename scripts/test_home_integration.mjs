import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const app=readFileSync('build/dc4i-vodtv/app.js','utf8'),html=readFileSync('build/dc4i-vodtv/index.html','utf8');
assert.ok(html.indexOf('vod-personalization-ui.js')<html.indexOf('vod-home-ui.js'));
const storeCode=app.slice(app.indexOf('  function store('),app.indexOf('  // ---------- settings'));
const context={P:{prefix:'a:'},localStorage:{getItem(k){return Object.hasOwn(this,k)?this[k]:null;}},JSON};vm.createContext(context);vm.runInContext(storeCode,context);
context.store('homeRailsLayoutV1',{order:['series'],enabled:['series']});
context.P.prefix='b:';assert.equal(context.store('homeRailsLayoutV1'),null);
context.store('homeRailsLayoutV1',{enabled:[]});
await Promise.resolve();context.P.prefix='a:';assert.equal(context.store('homeRailsLayoutV1').order[0],'series');
const build=app.slice(app.indexOf('  function buildRows()'),app.indexOf('  function el('));
let renders=0,boots=0;const hero={hidden:false};
const ctx={window:{TV:{}},TV:{view:()=>'home',homeRails:{captureFocus:()=>null,restoreFocus(){},rows:()=>[{id:'cached',items:[{title:'fixture'}]}]}},rowProviders:[],base:[],recent:[],heroItems:[],render(){renders++;},booted(){boots++;},$:()=>hero};
ctx.window.TV=ctx.TV;vm.createContext(ctx);vm.runInContext(build+';buildRows();',ctx);
assert.equal(renders,1,'cold-start rows render without base catalogue');assert.equal(boots,1);assert.equal(hero.hidden,true);
assert.equal(ctx.rowsData[0].id,'cached');
assert.ok(app.includes("nav = [top].concat(heroItems.length?[[$('heroBtn')]]:[]).concat"),'no hidden empty hero in focus rows');
assert.ok(app.includes("if(row.key==='homeRailsLayout')"));
assert.ok(app.includes('if(it.homeRail && TV.homeRails)return TV.homeRails.card(it);'));
assert.equal(JSON.parse(readFileSync('build/dc4i-vodtv/appinfo.json')).version,'1.2.19');
console.log('HOME_INTEGRATION_PASS actual profile store, async namespace boundary, cold rendering, focus hooks, version preserved');

const step=app.slice(app.indexOf('  function stepHero('),app.indexOf('  var idleSince ='));
const heroContext={heroItems:[],heroIdx:0,showHero(){}};vm.createContext(heroContext);vm.runInContext(step+';stepHero(1);',heroContext);
assert.equal(heroContext.heroIdx,0,'empty cold-start autoplay cannot poison hero index');
heroContext.heroItems=[{},{}];vm.runInContext('stepHero(1)',heroContext);assert.equal(heroContext.heroIdx,1);

// Execute the generated successful loadHome lifecycle with the real swallowed-error store.
const freshAt=1792929600000,expiredAt=freshAt-90000001;
Object.assign(context,{homeFetchedAt:expiredAt,heroItems:[],base:[],cached:{hero:[],base:[{}],fetchedAt:expiredAt},
 S:{youtube:false},C:{REGION:'PL'},SERVICES:[],tries:0,pos:{r:0,c:0},
 Date:class extends Date{static now(){return freshAt;}},
 loadApps:async()=>{},trending:async()=>Array.from({length:8},(_,i)=>({title:'Fresh '+i,tmdb:{id:i+1,type:'movie'},vote_average:8,vote_count:50,genre_ids:[878]})),
 jwPicks:async()=>[],tmdb:async()=>({results:[]}),mergePicks:(a,b)=>b,visibleApps:()=>[],buildRows(){},showHero(){},booted(){},focus(){}});
context.P.prefix='lifecycle:';context.store('homeCache',context.cached);
context.localStorage=new Proxy(context.localStorage,{set(){throw Error('quota fixture');}});
const lifecycle=app.slice(app.indexOf('  function loadHome()'),app.indexOf('  loadHome();'));
vm.runInContext(lifecycle,context);await vm.runInContext('loadHome()',context);
const stampFunction=app.match(/homeCandidatesStamp:(function\(\)\{[^\n]+\}),/)[1];
vm.runInContext('var actualStamp='+stampFunction,context);
assert.equal(context.actualStamp(),freshAt,'fresh in-memory lifecycle timestamp survives failed homeCache write');
assert.equal(context.store('homeCache').fetchedAt,expiredAt,'test really retained expired persisted stamp');
assert.equal(context.base[0].items[0].title,'Fresh 6');
const focusElCode=app.slice(app.indexOf('  function focusEl('),app.indexOf('  function card('));
const baseline={app:{id:'com.synthetic.app'}},newRail={};let focusedTarget;
const focusContext={nav:[[newRail],[baseline]],pos:{r:0,c:0},focus(){focusedTarget=focusContext.nav[focusContext.pos.r][focusContext.pos.c];}};
vm.createContext(focusContext);vm.runInContext(focusElCode,focusContext);focusContext.focusEl(baseline);
assert.equal(focusContext.pos.r,1);assert.equal(focusedTarget,baseline);
focusContext.nav=[[baseline]];focusContext.focusEl(baseline);assert.equal(focusContext.pos.r,0);

const candidatesFunction=app.match(/homeCandidates: (function\(\) \{[\s\S]*?\n    \}),/)[1];
vm.runInContext('var actualCandidates='+candidatesFunction,context);
const element=()=>({children:[],setAttribute(){},appendChild(x){this.children.push(x);return x;}});
context.document={body:element(),createElement:element,querySelector:()=>null,querySelectorAll:()=>[]};
context.setInterval=()=>{};
context.window={TV:{S:{uiLang:'en'},store:context.store,readMetadataStorage:context.readMetadataStorage,homeCandidates:context.actualCandidates,homeCandidatesStamp:context.actualStamp,
 el:element,addView(){},addSetting(){},refresh(){},view:()=>'home'}};
for(const name of ['vod-recommendations.js','vod-home-rails.js','vod-home-ui.js'])vm.runInContext(readFileSync('build/dc4i-vodtv/'+name,'utf8'),context);
const liveRows=context.window.TV.homeRails.rows();
assert.ok(liveRows.find(r=>r.id==='films').items.some(x=>x.title==='Fresh 6'),'actual loadHome+failed store renders fresh live Films');
