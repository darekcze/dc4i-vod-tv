import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
const w={};
vm.runInNewContext(readFileSync('src/vod-title-mapping.js','utf8'),{window:w,String,Array,Object,Number});
const m=w.DC4ITitleMapping;
assert.ok(m);
const tmdb=[
{id:100,title:'KATSEYE: Wild Hearts',release_date:'2026-05-01',media_type:'movie'},
{id:101,title:'KATSEYE Argentina',release_date:'2026-06-01',media_type:'movie'},
{id:102,title:'KATSEYE Brasil',release_date:'2026-07-01',media_type:'movie'}
];
const xt=[
{type:'movie',id:'901',tmdb:'100',title:'[PL] KATSEYE Wild Hearts 2026',group:'[PL] Filmy',year:'2026'},
{type:'movie',id:'902',title:'[PL] KATSEYE Argentina 2026',group:'[PL] Filmy',year:'2026'},
{type:'movie',id:'903',title:'KATSEYE Wild Hearts 2025',group:'[EN] Movie',year:'2025'},
{type:'series',id:'904',title:'KATSEYE Wild Hearts 2026',group:'Series',year:'2026'},
{type:'movie',id:'905',title:'KATSEYE Brasil 2026',group:'[PL] Films',year:'2026'}
];
const all=m.merge(tmdb,xt);
assert.equal(all.length,5,'3 TMDB titles plus unverified 2025 and series versions');
const wild=all.find(x=>x.tmdb?.id===100);
assert.equal(wild.sources.length,1);
assert.equal(wild.sources[0].id,'901');
assert.equal(all.find(x=>x.tmdb?.id===101).sources[0].id,'902');
assert.equal(all.find(x=>x.tmdb?.id===102).sources[0].id,'905');
assert.ok(all.some(x=>x.sources?.[0]?.id==='903'),'year mismatch must stay separate');
assert.ok(all.some(x=>x.sources?.[0]?.id==='904'),'series must not merge with film');
const plain=m.merge([{id:111,title:'Wild Hearts',release_date:'2026-01-01',media_type:'movie'}],
 [{id:'9',type:'movie',title:'Wild Hearts',year:'2026'}]);
assert.equal(plain.length,1);
const unsafe=m.merge([{id:111,title:'Wild Hearts',release_date:'2026-01-01',media_type:'movie'}],
 [{id:'9',type:'movie',title:'Wild Hearts'}]);
assert.equal(unsafe.length,2,'no unverified title-only automatic link');
const real=m.merge([{id:1728113,media_type:'movie',title:'KATSEYE: Wild Hearts',release_date:'2026-05-01'}],
 [{id:'10001',type:'movie',tmdb:'1728113',title:'EN - KATSEYE: Wild Hearts (2026)',year:'2026',rating:'4.2'}]);
assert.equal(real.length,1,'actual Xtream release uses same TMDB identifier');
assert.equal(real[0].sources[0].id,'10001');
const invalidCollision=m.merge([{id:1728113,media_type:'movie',title:'KATSEYE: Wild Hearts',release_date:'2026-05-01'}],
 [{id:'10001',type:'movie',tmdb:'9999',title:'KATSEYE: Wild Hearts 2026',year:'2026'}]);
assert.equal(invalidCollision.length,2,'conflicting verified TMDB identifiers must not be merged');
const zeroId=m.merge([{id:777,media_type:'movie',title:'Example Film',release_date:'2026-01-02'}],
 [{type:'movie',id:'x',tmdb:'0',title:'[PL] Example Film 2026',year:'2026'}]);
assert.equal(zeroId.length,1,'Xtream tmdb=0 means unknown, allow matching exact title+year');


console.log('TITLE_MAPPING_TEST_PASS',all.map(x=>[x.tmdb?.title||null,x.sources.map(s=>s.id)]));
