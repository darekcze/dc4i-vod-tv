import assert from 'node:assert/strict';import fs from 'node:fs';import vm from 'node:vm';
const app=fs.readFileSync('build/dc4i-vodtv/app.js','utf8'),data={},P={prefix:'a:'};let fail=false;
const localStorage=new Proxy(data,{get(t,k){if(fail)throw Error();if(k==='getItem')return key=>Object.hasOwn(t,key)?t[key]:null;if(k==='setItem')return (key,v)=>{t[key]=v;};if(k==='removeItem')return key=>delete t[key];return t[k];}});const c={P,localStorage};
vm.runInNewContext(app.slice(app.indexOf('  function store('),app.indexOf('  // ---------- settings')),c);
for(const key of ['homeRailsLayoutV1','recommendationOpensV1','guideFavoritesV1']){assert.equal(c.readMetadataStorage(key),null);data['a:'+key]='{';assert.throws(()=>c.readMetadataStorage(key));delete data['a:'+key];}
assert.throws(()=>c.readMetadataStorage('accounts'));assert.throws(()=>c.backupRead('accounts'));assert.throws(()=>c.backupWrite('accounts','{}'));
assert.equal(c.profileSettingsReadable(),true);data['a:settings']='{';assert.equal(c.profileSettingsReadable(),false);c.store('settings',{recoLearnPlayback:true});assert.equal(data['a:settings'],'{','generic writer preserves unreadable settings');delete data['a:settings'];
fail=true;assert.equal(c.profileSettingsReadable(),false);assert.throws(()=>c.readMetadataStorage('homeRailsLayoutV1'));fail=false;
c.backupWrite('dc4iChartLinksV1','{"region":"global","category":"tv"}');P.prefix='b:';assert.equal(c.backupRead('dc4iChartLinksV1'),null);P.prefix='a:';assert.match(c.backupRead('dc4iChartLinksV1'),/global/);
assert.equal(JSON.parse(fs.readFileSync('build/dc4i-vodtv/appinfo.json')).version,'1.2.19');
console.log('HARDENING_GENERATED_PASS strict metadata/settings reads, settings write guard, backup key boundary and profile isolation');
