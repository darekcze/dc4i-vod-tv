import assert from 'node:assert/strict';import fs from 'node:fs';import vm from 'node:vm';
const root='build/dc4i-vodtv/',app=fs.readFileSync(root+'app.js','utf8');let opened=0;const c={TV:{chartLinks:{openSettings(){opened++;}}},SROWS:[{key:'chartLinks',opts:[['edit','Configure']]}],draft:{}};
vm.runInNewContext(app.slice(app.indexOf('  function choose(e)'),app.indexOf('  // ---------- quick settings')),c);c.choose({dataset:{r:'0',i:'0'}});assert.equal(opened,1);
const html=fs.readFileSync(root+'index.html','utf8');assert.ok(html.indexOf('vod-chart-links.js')<html.indexOf('vod-chart-ui.js'));assert.ok(html.includes('vod-chart-ui.js'));
for(const name of ['vod-chart-links.js','vod-chart-ui.js']){const src=fs.readFileSync(root+name,'utf8');assert.doesNotMatch(src,/fetch\s*\(|XMLHttpRequest|<iframe|\.tmdb\s*\(/);}
assert.equal(JSON.parse(fs.readFileSync(root+'appinfo.json')).version,'1.2.19');
console.log('CHART_INTEGRATION_PASS generated settings route, script order, no feed requests, version preserved');
