#!/usr/bin/env python3
"""VODTV 1.2.19 guide: public model and private Xtream EPG bridge."""
from pathlib import Path
import shutil
R=Path(__file__).resolve().parents[1]
A=R/'build/dc4i-vodtv'
for name in ('vod-guide-model.js','vod-guide-epg.js'):
    shutil.copy2(R/'src'/name, A/name)
p=A/'index.html';html=p.read_text(encoding='utf-8')
anchor='<script src="vod-xtream.js"></script>'
assert html.count(anchor)==1
html=html.replace(anchor,'<script src="vod-guide-model.js"></script>\n'
     '<script src="vod-guide-epg.js"></script>\n'+anchor)
p.write_text(html,encoding='utf-8')
p=A/'vod-xtream.js';s=p.read_text(encoding='utf-8')
anchor='TV.xtream={getAccounts:'
assert s.count(anchor)==1
bridge="""// 1.2.19: on-demand single-flight Xtream EPG for the user-visible guide.
var returnToGuide=false,guideLoading=null;
var guideAdapter=window.DC4IGuideEpg.create(
 function(channel){
  var a=account();
  if(!a || channel.accountId!==selected) return Promise.resolve([]);
  return request(a,'get_short_epg',{stream_id:channel.id,limit:7});
 },
 function(raw,channel){
  return window.DC4IEPG.parse(raw,channel);
 },
 {ttlMs:300000}
);
function ensureGuideCatalog(){
 if(records.length)return Promise.resolve(records.slice());
 if(!selected && saved.length)selected=saved[0].id;
 if(!selected || !account())return Promise.resolve([]);
 if(guideLoading)return guideLoading;
 guideLoading=restoreCatalog().then(function(ok){
  if(ok)return records.slice();
  if(isLoading)return new Promise(function(resolve){
   var left=50;
   function check(){if(!isLoading || --left<=0)return resolve(records.slice());
     setTimeout(check,600);}
   check();
  });
  return sync(false).then(function(){return records.slice();});
 },function(){return [];}).then(function(items){guideLoading=null;return items;},
 function(){guideLoading=null;return [];});
 return guideLoading;
}
function guideEpg(channel){
 if(!channel || !channel.id)return Promise.resolve([]);
 if(!selected && saved.length)selected=saved[0].id;
 if(!account())return Promise.resolve([]);
 var copy=Object.assign({},channel,{accountId:selected});
 return guideAdapter.get(copy);
}
function guideConfig(){
 returnToGuide=true;
 if(TV.guide && TV.guide.suspend)TV.guide.suspend();
 TV.openView('xtream','all');
}
function guideWatch(channel){
 if(!channel || channel.type!=='live')return false;
 if(!selected && saved.length)selected=saved[0].id;
 if(!account())return false;
 returnToGuide=true;
 if(TV.guide && TV.guide.suspend)TV.guide.suspend();
 TV.openView('xtream','live');
 choose(channel);
 return true;
}
function leaveGuidePlayback(){
 if(playing)stop();
 if(!returnToGuide)return;
 returnToGuide=false;
 TV.closeView();
 if(TV.guide && TV.guide.resume)TV.guide.resume();
}
"""
s=s.replace(anchor,bridge+anchor,1)
anchor=" searchEpg:searchEpg,remindEpg:remindEpg,playEpg:playEpg,"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+
  "\n ensureCatalog:ensureGuideCatalog,guideEpg:guideEpg,guideWatch:guideWatch,guideConfig:guideConfig,"
  "\n getLiveCategories:function(){return categories.filter(function(c){return c.type==='live';}).slice();},",1)
anchor="bind('playerclose',stop);"
assert s.count(anchor)==1
s=s.replace(anchor,"bind('playerclose',function(){if(returnToGuide)leaveGuidePlayback();else stop();});",1)
anchor=" back:function(){if(playing){stop();return true;}"
assert s.count(anchor)==1
s=s.replace(anchor," back:function(){if(playing){if(returnToGuide)leaveGuidePlayback();else stop();return true;}",1)
anchor="  if(e.keyCode===461||e.keyCode===27||e.keyCode===8){stop();return true;}"
assert s.count(anchor)==1
s=s.replace(anchor,"  if(e.keyCode===461||e.keyCode===27||e.keyCode===8){if(returnToGuide)leaveGuidePlayback();else stop();return true;}",1)
anchor=" hide:function(){if(playing)stop();detailPanel.hidden=true;detailItem=null;root.hidden=true;},"
assert s.count(anchor)==1
s=s.replace(anchor," hide:function(){if(playing)stop();detailPanel.hidden=true;detailItem=null;root.hidden=true;"+
  "if(returnToGuide){returnToGuide=false;if(TV.guide&&TV.guide.resume)TV.guide.resume();}},",1)
p.write_text(s,encoding='utf-8')
# UI module must load after its Xtream API provider is ready.
shutil.copy2(R/'src/vod-channel-guide.js',A/'vod-channel-guide.js')
shutil.copy2(R/'src/vod-channel-guide.css',A/'vod-channel-guide.css')
p=A/'index.html';t=p.read_text(encoding='utf-8')
anchor='<script src="vod-xtream.js"></script>'
assert t.count(anchor)==1
t=t.replace(anchor,anchor+'\\n<script src="vod-channel-guide.js"></script>')
css='<link rel="stylesheet" href="vod-xtream.css">'
assert t.count(css)==1
t=t.replace(css,css+'\\n<link rel="stylesheet" href="vod-channel-guide.css">')
p.write_text(t,encoding='utf-8')
print('GUIDE_EPG_BRIDGE_PATCH_READY')
