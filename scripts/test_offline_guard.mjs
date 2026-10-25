// A classic-script error must not leave network available to later scripts.
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import vm from 'node:vm';
const code=execFileSync('python3',['-c',"import runpy; print(runpy.run_path('scripts/build_offline_fixture.py')['EMPTY_KEYS'])"],{encoding:'utf8'});
for(const onTV of [false,true]){
 let calls=0;
 function XHR(){}
 XHR.prototype.open=()=>{calls++;};
 const window={fetch:()=>{calls++;return Promise.resolve();},XMLHttpRequest:XHR};
 const ctx=vm.createContext({window,Promise,Error,...(onTV?{PalmSystem:{}}:{})});
 if(onTV)assert.throws(()=>vm.runInContext(code,ctx),/Offline fixture/);
 else vm.runInContext(code,ctx);
 // Simulate later classic scripts even after the first script throws.
 await assert.rejects(window.fetch('https://example.invalid'),/network disabled/);
 assert.throws(()=>new window.XMLHttpRequest().open('GET','https://example.invalid'),/network disabled/);
 assert.equal(calls,0);
}
console.log('OFFLINE_GUARD_PASS browser and PalmSystem: later fetch/XHR blocked');

const bootstrap=execFileSync('python3',['-c',"import runpy; m=runpy.run_path('scripts/build_offline_fixture.py'); print(m.get('BOOTSTRAP', ''))"],{encoding:'utf8'});
assert.ok(bootstrap.trim(), 'refusal must gate application loading, not only keys.js');
for(const [hostname,protocol,onTV,expected] of [['127.0.0.1','http:',false,2],['localhost','http:',true,0],['','file:',false,0],['example.com','https:',false,0]]){
 const loaded=[];const originals=[{getAttribute:()=> 'config.js'},{getAttribute:()=> 'app.js'}];
 const doc={currentScript:{nonce:'test'},querySelectorAll:()=>originals,
  createElement:()=>({}),head:{appendChild(s){loaded.push(s.src);s.onload();}},
  body:{textContent:''},addEventListener(name,fn){assert.equal(name,'DOMContentLoaded');fn();}};
 const window={location:{hostname,protocol},fetch:()=>Promise.resolve(),XMLHttpRequest:function(){},...(onTV?{PalmSystem:{}}:{})};
 const context=vm.createContext({window,document:doc,Promise,Error});
 vm.runInContext(bootstrap,context);
 await new Promise(resolve=>setTimeout(resolve,0));
 assert.equal(loaded.length,expected, hostname+' '+protocol+' TV='+onTV);
 if(!expected)assert.match(doc.body.textContent,/refused/i);
 await assert.rejects(window.fetch('https://example.invalid'),/network disabled/);
}
console.log('OFFLINE_BOOTSTRAP_PASS refuses TV/non-loopback before application scripts');
