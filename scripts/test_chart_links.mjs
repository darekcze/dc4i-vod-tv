import assert from 'node:assert/strict';import fs from 'node:fs';import vm from 'node:vm';
const c={window:{}};vm.runInNewContext(fs.readFileSync('src/vod-chart-links.js','utf8'),c);const a=c.window.DC4IChartLinks;
for(const region of ['global','poland'])for(const category of ['film','tv']){const url=a.resolve({region,category});assert.ok(a.allowed(url));assert.ok(url.startsWith('https://www.netflix.com/tudum/top10'));}
for(const value of ['https://evil.test','https://www.netflix.com.evil.test/tudum/top10','https://www.netflix.com/tudum/top10?x=1','http://www.netflix.com/tudum/top10','https://www.netflix.com/tudum/top10/','javascript:alert(1)'])assert.equal(a.allowed(value),false);
for(const choice of [{region:'us',category:'film'},{region:'global',category:'movie'},{region:'__proto__',category:'tv'},null])assert.equal(a.resolve(choice),null);
assert.equal(a.feedEnabled,false);assert.equal(a.rightsStatus,'unverified');assert.equal(a.resolve({region:'poland',category:'tv'}),'https://www.netflix.com/tudum/top10/poland/tv');
console.log('CHART_LINKS_PASS exact allowlist, four region/category choices, unsupported rejection, feed disabled');
