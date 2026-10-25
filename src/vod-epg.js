/* Local metadata-only EPG matcher. Actual programs come exclusively from user's
   configured Xtream API. It does not imply that archives/recordings can play. */
(function(root){
'use strict';
function text(encoded){
 var s=String(encoded||'');
 try{
  if(!s)return '';
  var raw=atob(s),bytes=new Uint8Array(raw.length);
  for(var i=0;i<raw.length;i++)bytes[i]=raw.charCodeAt(i);
  return new TextDecoder('utf-8').decode(bytes);
 }catch(e){return s;}
}
function normalize(x){
 return String(x||'').normalize('NFKD').replace(/[\u0300-\u036f]/g,'')
 .toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
}
function matches(title,query){
 var q=normalize(query),name=normalize(title);
 return !!(q.length>=3 && name.includes(q));
}
function parse(raw,channel,now){
 try{
  if(!raw || !channel)return null;
  var start=Number(raw.start_timestamp)*1000;
  var end=Number(raw.stop_timestamp)*1000;
  if(!start||!end||end<=start)return null;
  var title=text(raw.title),timestamp=now===undefined?Date.now():now;
  var state=timestamp>=start&&timestamp<end?'now':timestamp>=end?'past':'future';
  var days=Number(channel.archiveDays)||0;
  var archiveFlag=state==='past' && Number(channel.archive)===1
    && Number(raw.has_archive)===1 && days>0 && timestamp-end<=days*86400000;
  var localStart=String(raw.start||'');
  var m=localStart.match(/^(\d{4}-\d{2}-\d{2})\s(\d{2}):(\d{2})/);
  return {title:title,description:text(raw.description),channelTitle:channel.title,channelId:String(channel.id),
    time:{start:start,end:end},duration:Math.ceil((end-start)/60000),state:state,
    archiveFlag:archiveFlag,startParam:m?m[1]+':'+m[2]+'-'+m[3]:'',source:'Xtream EPG'};
 }catch(e){return null;}
}
root.DC4IEPG={parse:parse,matches:matches,normalize:normalize};
})(window);
