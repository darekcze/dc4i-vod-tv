import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const root=new URL('../build/dc4i-vodtv/',import.meta.url);
const html=readFileSync(new URL('index.html',root),'utf8');
const guide=readFileSync(new URL('vod-channel-guide.js',root),'utf8');
const css=readFileSync(new URL('vod-channel-guide.css',root),'utf8');
const scripts=[...html.matchAll(/<script src="([^"]+)"/g)].map(x=>x[1]);
assert.ok(scripts.indexOf('vod-xtream.js')<scripts.indexOf('vod-channel-guide.js'));
assert.ok(guide.includes("TV.addView('guide'"),'own TV guide view');
for(const keyword of ['gd-groups','gd-channels','gd-detail','gd-watch','gd-favorite','gd-now','gd-next'])
 assert.ok(guide.includes(keyword),keyword);
for(const key of ["guideFavoritesV1","guideSelectedGroupV1","guideLastChannelV1"])
 assert.ok(guide.includes(key),'per-profile storage '+key);
assert.ok(guide.includes("TV.xtream.guideEpg"),'EPG of focused channel');
assert.ok(guide.includes("TV.xtream.guideWatch"),'existing Xtream player reused');
assert.ok(guide.includes('TV.guide={'),'return-to-guide API');
assert.ok(guide.includes('keydown:function'),'TV remote navigation');
assert.ok(guide.includes('dataset.group'),'group context');
assert.ok(guide.includes('dataset.channel'),'channel context');
assert.ok(css.includes('grid-template-columns'),'three-column guide layout');
assert.ok(css.includes('#dc4i-guide'),'scoped styling');
assert.ok(!guide.includes('password') && !guide.includes('username'),'no Xtream secrets in guide');
console.log('GUIDE_UI_STATIC_TEST_PASS');

assert.ok(scripts.indexOf('vod-rich-epg.js')<scripts.indexOf('vod-epg-metadata-ui.js'));
assert.ok(scripts.indexOf('vod-epg-metadata-ui.js')<scripts.indexOf('vod-channel-guide.js'));
assert.ok(guide.includes('TV.epgMetadata.guide(selected,events)'));
assert.ok(guide.includes("$('metadata').textContent=rich.label"));
const details=readFileSync(new URL('features/details.js',root),'utf8');
assert.ok(details.includes('TV.epgMetadata.renderDetails(epgHost,it.title,events)'));
assert.ok(details.includes('TV.epgMetadata.renderDetails(epgHost,it.title,[])'));
