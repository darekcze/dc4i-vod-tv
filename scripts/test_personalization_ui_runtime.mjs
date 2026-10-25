import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
let profile='a',refreshCount=0;
const prefs={},histories={a:{},b:{}},rows=[],opened=[],settings=[];
const titles=[
 {tmdb:{type:'movie',id:1},genre_ids:[878],vote_average:7.8,vote_count:900,popularity:50,release_date:'2026-01-01',title:'Sci-Fi',img:'sci.jpg'},
 {tmdb:{type:'movie',id:2},genre_ids:[27],vote_average:9.9,vote_count:700,popularity:30,release_date:'2026-01-01',title:'Horror',img:'h.jpg'},
 {tmdb:{type:'movie',id:3},genre_ids:[10749],vote_average:7.2,vote_count:900,popularity:45,release_date:'2026-01-01',title:'Romance',img:'r.jpg'},
 {tmdb:{type:'movie',id:4},genre_ids:[878],vote_average:0,vote_count:0,popularity:90,release_date:'2026-01-01',title:'Unknown',img:'u.jpg'}
];
const tv={
 S:{},P:{extraQ:''},
 homeCandidates:()=>titles,
 addSetting(row,def){settings.push(row);if(this.S[row.key]===undefined)this.S[row.key]=def;},
 addRow(fn){rows.push(fn);},
 store(k,v){if(arguments.length>1){histories[profile][k]=JSON.parse(JSON.stringify(v));return v;}return histories[profile][k]||null;},
 itemOk(x){opened.push(['item',x.title]);},
 openItem(x){opened.push(['open',x.title]);},
 toast(){},refresh(){refreshCount++;}
};
tv.readMetadataStorage=k=>tv.store(k);
tv.profileSettingsReadable=()=>true;
tv.profileFlagEnabled=k=>tv.S[k]!==false&&(tv.store('settings')||{})[k]!==false;
const window={TV:tv};
const ctx=vm.createContext({window,Date,Number,Math,String,Object,Array});
vm.runInContext(readFileSync('src/vod-recommendations.js','utf8'),ctx);
vm.runInContext(readFileSync('src/vod-personalization-ui.js','utf8'),ctx);
assert.ok(tv.personalized);
assert.equal(settings.length,10);
assert.equal(rows.length,1);
let row=rows[0]();
assert.equal(row.title,'Dopasowane do profilu');
assert.ok(row.items.length>=2);
assert.equal(row.items.find(i=>i.title==='Unknown'),undefined,'no invented rating');
assert.ok(row.items.some(x=>x.recoReason&&x.recoScore>=0),'visible reason');
tv.S.recoHorrorMode='hide';row=rows[0]();
assert.ok(!row.items.some(x=>x.title==='Horror'),'hide horror in user profile');
tv.S.recoEnabled=false;assert.equal(rows[0](),null,'turn off row');
tv.S.recoEnabled=true;tv.itemOk(titles[0]);
assert.equal(tv.personalized.history()[0].action,'opened');
assert.ok(tv.personalized.history()[0].key==='movie:1');
assert.ok(!tv.personalized.history().some(x=>x.action==='watched'));
profile='b';assert.equal(tv.personalized.history().length,0,'new profile does not see another profile history');
tv.itemOk(titles[2]);assert.equal(histories.b.recommendationOpensV1.length,1);
profile='a';assert.equal(tv.personalized.history().length,1);
tv.personalized.clear();assert.equal(tv.personalized.history().length,0);
assert.equal(histories.b.recommendationOpensV1.length,1,'clear respects profile');
assert.equal(refreshCount,1,'clear refreshes recommendations');
tv.P.extraQ='&certification_country=US';tv.S.recoHorrorMode='high';row=rows[0]();
assert.ok(!row.items.some(x=>x.title==='Horror'),'kids profile must hide horror even when enabled');
console.log('PERSONALIZATION_UI_RUNTIME_PASS',row.items.map(x=>({title:x.title,score:x.recoScore})));
const beforeCorrupt=JSON.stringify(histories);tv.readMetadataStorage=()=>{throw Error('corrupt');};tv.openItem(titles[0]);assert.equal(JSON.stringify(histories),beforeCorrupt,'unreadable opened history preserved');
