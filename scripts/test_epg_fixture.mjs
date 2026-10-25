import assert from 'node:assert/strict';
import {mkdtempSync,readFileSync,rmSync,existsSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {execFileSync} from 'node:child_process';
import vm from 'node:vm';
assert.ok(existsSync('scripts/render_epg_fixture.py'),'deterministic EPG preview generator must exist');
const dir=mkdtempSync(join(tmpdir(),'epg-preview-test-'));
try{
 const output=join(dir,'preview.html');
 execFileSync('python3',['scripts/render_epg_fixture.py','--output',output]);
 const html=readFileSync(output,'utf8');
 const script=html.match(/<script[^>]*>([\s\S]*?)<\/script>/)?.[1];
 assert.ok(script);
 assert.ok(html.includes("connect-src 'none'") && !html.includes('<script src='));
 const nodes={};
 const document={getElementById(id){return nodes[id]||(nodes[id]={textContent:'',children:[],replaceChildren(){this.children=[];},appendChild(n){this.children.push(n);}});},createElement(){return {textContent:''};}};
 const window={};
 vm.runInNewContext(script,{window,document,Date,JSON,Number,String,Array,Object,Math});
 assert.equal(window.fixtureState.status,'fresh');
 assert.equal(nodes.events.children.length,2);
 assert.match(nodes.events.children[0].textContent,/Pierwsza godzina/);
 nodes.stale.onclick();assert.equal(window.fixtureState.status,'stale');
 nodes.expire.onclick();assert.equal(window.fixtureState.status,'missing');assert.equal(nodes.events.children.length,0);
 assert.throws(()=>execFileSync('python3',['scripts/render_epg_fixture.py','--output',output],{stdio:'pipe'}),'must not overwrite an existing preview');
 console.log('EPG_FIXTURE_CONTROLLER_PASS deterministic fresh/stale/expired preview (VM, not browser)');
}finally{rmSync(dir,{recursive:true,force:true});}
