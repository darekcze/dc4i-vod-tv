import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
const w={};
vm.runInNewContext(readFileSync('src/vod-title-mapping.js','utf8'),{window:w,String,Array,Object,Number});
let searches=0;
w.TV={
 xtream:{getAccounts:()=>[{id:'a'}],searchCatalog:async(term,o)=>{searches++;return [
   {id:'a01',title:'EN - KATSEYE: Wild Hearts (2026)',type:'movie',tmdb:'1728113',year:'2026',rating:'4.2'},
   {id:'a02',title:'EN - KATSEYE Argentina (2026)',type:'movie',tmdb:'1729999',year:'2026'},
   {id:'b01',title:'EN - KATSEYE: Wild Hearts (2025)',type:'movie',year:'2025'}
 ];}}
};
vm.runInNewContext(readFileSync('src/vod-source-index.js','utf8'),{window:w,String,Array,Object,Number,Promise});
const idx=w.TV.titleSources;
const t={id:1728113,title:'KATSEYE: Wild Hearts',media_type:'movie',release_date:'2026-01-02'};
let links=await idx.forTmdb(t);
assert.equal(links.length,1);
assert.equal(links[0].id,'a01');
assert.equal(searches,1);
links=await idx.forTmdb(t);
assert.equal(searches,1,'cache verified references');
assert.equal(idx.get(t).length,1);
assert.equal((await idx.forTmdb({id:1729999,media_type:'movie',title:'KATSEYE Argentina',release_date:'2026-04-01'})).length,1);
assert.equal((await idx.forTmdb({id:1728113,media_type:'tv',name:'KATSEYE: Wild Hearts',first_air_date:'2026-01-02'})).length,0,'series not movie');
assert.equal((await idx.forTmdb({id:99999999,media_type:'movie',title:'Unknown',release_date:'2026-01-02'})).length,0);
console.log('SOURCE_INDEX_TEST_PASS');
