import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
const A='build/dc4i-vodtv/';const html=readFileSync(A+'index.html','utf8');const app=readFileSync(A+'app.js','utf8');const xt=readFileSync(A+'vod-xtream.js','utf8');const search=readFileSync(A+'features/search.js','utf8');
const tabs=[...html.matchAll(/<span class="tab f"[^>]*>([^<]+)<\/span>/g)].map(x=>x[1]);
assert.deepEqual(tabs,['VOD','TV','IPTV','Filmy','Seriale','Szukaj','Aplikacje']);
assert.match(search,/\{mode:'all',\s*label:tr\('Wszystkie'/);
for(const name of ['VOD','TV','IPTV'])assert.ok(search.includes("label:'"+name+"'"),name);
for(const name of ['Filmy','Seriale'])assert.ok(search.includes("tr('"+name+"'"),name);
for(const lang of ['Polskie','Angielskie','Wszystkie języki'])assert.ok(search.includes(lang),lang);
assert.ok(search.includes('TV.xtream.searchCatalog'),'Xtream search integrated');
assert.ok(xt.includes('searchCatalog:function'),'Xtream API exposed');
assert.ok(xt.includes('dc4iXtreamPlaylistsV1'),'retained existing saved account key');
assert.ok(xt.includes('dc4iXtreamAccountsBackupV1'),'accounts backup');
assert.ok(xt.includes('indexedDB'),'TV-local catalog storage');
assert.ok(html.includes('data-act="live"')); // native live launch retained
console.log('XTREAM_NAVIGATION_ASSERTIONS_PASS');
