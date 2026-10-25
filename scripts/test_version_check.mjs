import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';

function load() {
  const win = {};
  const ctx = vm.createContext({window:win, Date, Promise, Error, JSON, String, Number});
  vm.runInContext(readFileSync('src/vod-version-check.js', 'utf8'), ctx);
  return win.DC4IVersions;
}
const version = load();
assert.equal(version.compare('1.2.12','1.2.11'),1);
assert.equal(version.compare('1.2.12','1.2.12'),0);
assert.equal(version.compare('1.2.9','1.2.12'),-1);
assert.equal(version.compare('1.10.0','1.9.99'),1);
assert.equal(version.compare('1.2.12','1.2.12-beta'),1);
assert.equal(version.compare('1.2.12-beta','1.2.12'),-1);
assert.equal(version.compare('bad','1.2.11'),null);
const validCatalog = {packages:[
  {id:'unrelated',manifest:{version:'9.9.9'}},
  {id:'com.dc4i.vodtv',manifest:{version:'1.2.13',releaseDate:'2026-11-02'}}]};
assert.equal(version.extract(validCatalog).version,'1.2.13');
assert.equal(version.extract(validCatalog).releaseDate,'2026-11-02');
assert.equal(version.extract({packages:[]}),null);
const out={textContent:'',dataset:{},title:''},badge={textContent:'',dataset:{},title:''};
const urlLog=[];
const response=await version.refresh({
  currentVersion:'1.2.12',
  latestElement:out,statusElement:badge,
  fetch:async (url,opts)=>{
    urlLog.push(url);
    assert.ok(url.startsWith('https://lg.darc.dev/api/apps.json'));
    assert.equal(opts.cache,'no-store');
    return {ok:true,json:async()=>validCatalog};
  }});
assert.equal(response.state,'update');
assert.equal(out.dataset.state,'update');
assert.equal(badge.textContent,'Aktualizacja dostępna');
assert.equal(out.textContent,'1.2.13 · 02.11.2026');
assert.equal(urlLog.length,1);
await version.refresh({currentVersion:'1.2.12',latestElement:out,statusElement:badge,
  fetch:async()=>({ok:true,json:async()=>({packages:[{id:'com.dc4i.vodtv',manifest:{version:'1.2.12',releaseDate:'2026-10-25'}}]})})});
assert.equal(out.dataset.state,'current');
assert.equal(badge.textContent,'Aktualna');
await version.refresh({currentVersion:'1.2.12',latestElement:out,statusElement:badge,
  fetch:async()=>({ok:true,json:async()=>({packages:[{id:'com.dc4i.vodtv',manifest:{version:'1.2.5',releaseDate:'2026-10-24'}}]})})});
assert.equal(out.dataset.state,'ahead');
assert.equal(badge.textContent,'Wersja nowsza niż repo');
await version.refresh({currentVersion:'1.2.12',latestElement:out,statusElement:badge,
  fetch:async()=>{throw Error('offline');}});
assert.equal(out.dataset.state,'offline');
assert.equal(badge.textContent,'Offline');
console.log('VERSION_CHECK_TEST_PASS');
