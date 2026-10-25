import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
const w={};
vm.runInNewContext(readFileSync(new URL('../src/vod-guide-model.js', import.meta.url),'utf8'),{window:w,String,Number,Math,Array,Object,Date});
const guide=w.DC4IGuideModel;
assert.ok(guide,'guide model installed');
const records=[
  {id:'1',type:'live',title:'TVP 1 HD',group:'[PL] Ogólne',category:'7',icon:'https://example.org/tvp1.png'},
  {id:'2',type:'live',title:'HBO HD',group:'[PL] Filmowe',category:'8',icon:''},
  {id:'2',type:'live',title:'HBO HD duplicate',category:'8',icon:''},
  {id:'3',type:'live',title:'No category',group:'[PL] Pozostałe',category:'',icon:''},
  {id:'4',type:'movie',title:'Not a channel',category:'8'},
  {id:'5',type:'series',title:'Not live either',category:'7'}
];
const cats=[
  {id:'7',type:'live',title:'[PL] Ogólne'},
  {id:'8',type:'live',title:'[PL] Filmowe'},
  {id:'8',type:'movie',title:'Film category sharing id'},
  {id:'99',type:'live',title:'Empty group'}
];
const m=guide.group(records,cats,['2','not-there']);
assert.deepEqual(Array.from(m.groups.map(x=>x.id)),['all','favorites','g:7','g:8','g:unknown']);
assert.deepEqual(Array.from(m.byGroup.all.map(x=>x.id)),['1','2','3']);
assert.deepEqual(Array.from(m.byGroup.favorites.map(x=>x.id)),['2']);
assert.deepEqual(Array.from(m.byGroup['g:8'].map(x=>x.title)),['HBO HD']);
assert.equal(m.groups.find(x=>x.id==='g:7').count,1);
assert.equal(m.groups.find(x=>x.id==='g:8').title,'[PL] Filmowe');
assert.equal(m.groups.find(x=>x.id==='g:unknown').title,'[PL] Pozostałe');
assert.equal(m.groups.find(x=>x.id==='all').count,3);
assert.equal(m.byGroup.all[1].icon,'','missing real logo stays missing');

const current={title:'Movie',time:{start:1000,end:2000}};
const next={title:'Next',time:{start:2000,end:4000}};
const late={title:'Yesterday',time:{start:-4000,end:-3000}};
let selection=guide.nowNext([next,late,current],1500);
assert.equal(selection.now.title,'Movie');
assert.equal(selection.next.title,'Next');
assert.equal(guide.progress(current,1000),0);
assert.equal(guide.progress(current,1500),50);
assert.equal(guide.progress(current,2500),100);
assert.equal(guide.progress(current,-5000),0);
selection=guide.nowNext([next,current],2100);
assert.equal(selection.now.title,'Next');
assert.equal(selection.next,null);
selection=guide.nowNext([next,current],4000);
assert.equal(selection.now,null);
assert.equal(selection.next,null);
selection=guide.nowNext([{title:'bad',time:{start:4000,end:3000}},next],1500);
assert.equal(selection.now,null);
assert.equal(selection.next.title,'Next');
assert.equal(guide.progress({time:{start:1000,end:1000}},1000),0);
console.log('GUIDE_MODEL_TEST_PASS');
