import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

// Pure mapping is isolated from the TV DOM to allow repeatable checks.
const source=readFileSync(new URL('../src/vod-channel-guide.js',import.meta.url),'utf8');
const start='/* CHANNEL_REMOTE_PURE_START';
const end='/* CHANNEL_REMOTE_PURE_END */';
const a=source.indexOf(start),b=source.indexOf(end,a);
assert.ok(a>=0&&b>a,'remote-control mapping is present');
const block=source.slice(source.indexOf('*/',a)+2,b);
const context=vm.createContext({});
vm.runInContext(block,context);
const direction=context.remoteDirection,wrap=context.wrapChannel;
for(const [input,expected] of [
 [{keyCode:427},1],[{keyCode:428},-1],
 [{keyCode:33},1],[{keyCode:34},-1],
 [{which:427},1],[{which:428},-1],
 [{key:'ChannelUp'},1],[{key:'ChannelDown'},-1],
 [{key:'PageUp'},1],[{code:'PageDown'},-1],
 [{keyCode:0,key:'ChannelUp'},1],[{keyCode:0,key:'ChannelDown'},-1],
 [{keyCode:38},0],[{keyCode:40},0],[{key:'ArrowUp'},0],
 [{keyCode:13},0],[{keyCode:461},0],[{},0]
])assert.equal(direction(input),expected,JSON.stringify(input));
assert.equal(wrap(0,0,1),-1);
assert.equal(wrap(3,-1,1),0);
assert.equal(wrap(3,-1,-1),2);
assert.equal(wrap(3,0,1),1);
assert.equal(wrap(3,2,1),0);
assert.equal(wrap(3,0,-1),2);
assert.equal(wrap(3,2,-1),1);
assert.equal(wrap(3,1,0),-1);
assert.ok(source.includes('TV.xtream.guideWatch(next)'),'must tune via existing Xtream player');
assert.ok(source.includes("TV.view()==='xtream'"),'must work during player overlay');
assert.ok(source.includes("TV.view()==='guide'"),'must work inside IPTV guide');
assert.ok(source.includes("ev.stopImmediatePropagation()"),'avoid old PageUp/Down paging');
console.log('CHANNEL_REMOTE_TEST_PASS (26 assertions)');
