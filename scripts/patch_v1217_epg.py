#!/usr/bin/env python3
"""On-device provider EPG query, conservative CatchUp and foreground reminder metadata."""
from pathlib import Path
import shutil
A=Path(__file__).resolve().parents[1]/'build/dc4i-vodtv'
R=A.parents[1]
shutil.copy2(R/'src/vod-epg.js',A/'vod-epg.js')
p=A/'index.html';s=p.read_text()
needle='<script src="vod-title-mapping.js"></script>'
assert s.count(needle)==1
s=s.replace(needle,'<script src="vod-epg.js"></script>\n'+needle)
p.write_text(s)
p=A/'vod-xtream.js';s=p.read_text()
needle="year:i.year||i.releaseDate||'',languageTag:"
assert s.count(needle)==1
s=s.replace(needle,"year:i.year||i.releaseDate||'',epgId:i.epg_channel_id||'',archive:Number(i.tv_archive||0),archiveDays:Number(i.tv_archive_duration||0),languageTag:")
needle="function errorMsg(e){"
assert s.count(needle)==1
helper="""var epgCache={};
var reminders=TV.store('dc4iEpgRemindersV1')||[];
function remindEpg(event){
 if(!event || event.state!=='future')return false;
 var key=event.channelId+':'+event.time.start;
 if(!reminders.some(function(r){return r.key===key})){
  reminders.push({key:key,title:event.title,channel:event.channelTitle,start:event.time.start});
  TV.store('dc4iEpgRemindersV1',reminders);
 }
 TV.toast('Przypomnienie zapisane. Powiadomienie działa, gdy VODTV jest uruchomiona.');
 return true;
}
setInterval(function(){
 if(!reminders.length)return;
 var now=Date.now(),keep=[];
 reminders.forEach(function(item){
  if(now>=item.start && now<item.start+300000) {
   TV.toast('Teraz w TV: '+item.title+' · '+item.channel);
  }else if(item.start>=now)keep.push(item);
 });
 if(keep.length!==reminders.length){
  reminders=keep;TV.store('dc4iEpgRemindersV1',reminders);
 }
},60000);
function chosenEpgChannels(){
 var available=records.filter(function(x){return x.type==='live'&&x.epgId;});
 var region=TV.S.region||'PL';
 if(region!=='ALL'){
  var filtered=available.filter(function(x){
   var markers=x.title+' '+x.group;
   return region==='PL' ? /\\[(?:PL|POL)\\]/i.test(markers) : markers.indexOf('['+region+']')>=0;
  });
  if(filtered.length)available=filtered;
 }
 available.sort(function(a,b){
  var priority=function(x){return /HBO|CANAL\\+|CINEMAX|AMC|FILM|MOVIE|TVN|POLSAT|TVP/i.test(x.title)?0:1;};
  return priority(a)-priority(b);
 });
 return available.slice(0,12);
}
function searchEpg(title){
 var phrase=String(title||'').trim();
 if(phrase.length<3 || !window.DC4IEPG)return Promise.resolve([]);
 function query(){
  var channels=chosenEpgChannels(),list=[],examined=0;
  return channels.reduce(function(chain,channel){
   return chain.then(function(){
    var key=selected+':'+channel.id,c=epgCache[key];
    if(c&&Date.now()-c.at<2*3600*1000){
     c.rows.forEach(function(e){if(window.DC4IEPG.matches(e.title,phrase))list.push(e);});
     examined++;return;
    }
    var accountItem=account();if(!accountItem)return;
    return request(accountItem,'get_simple_data_table',{stream_id:channel.id}).then(function(data){
     var parsed=(data.epg_listings||[]).map(function(r){var e=window.DC4IEPG.parse(r,channel);if(e)e.channel=channel;return e;}).filter(Boolean);
     epgCache[key]={at:Date.now(),rows:parsed};
     parsed.forEach(function(e){if(window.DC4IEPG.matches(e.title,phrase))list.push(e);});
     examined++;
    },function(){});
   });
  },Promise.resolve()).then(function(){
   list.sort(function(a,b){return Math.abs(a.time.start-Date.now())-Math.abs(b.time.start-Date.now())});
   list.checkedChannels=examined;
   return list.slice(0,35);
  });
 }
 if(records.length)return query();
 return restoreCatalog().then(function(ok){return ok?query():Promise.resolve([]);});
}
function playEpg(entry){
 if(!entry || !entry.channel)return false;
 if(entry.state==='now')return choose(entry.channel);
 if(entry.state==='future')return remindEpg(entry);
 if(entry.state==='past'){
  if(!entry.archiveFlag)return TV.toast('Brak potwierdzonego archiwum dla tej emisji.');
  var a=account();if(!a||!entry.startParam)return false;
  var ext='ts';
  var src=a.host+'/timeshift/'+encodeURIComponent(a.username)+'/'+encodeURIComponent(a.password)+
   '/'+entry.duration+'/'+entry.startParam+'/'+encodeURIComponent(entry.channelId)+'.'+ext;
  // Provider reports has_archive, but archive playback must be checked at runtime.
  playing=true;playerFocus=document.querySelector('.focus');$('player').hidden=false;
  var video=$('video');video.src=src;video.load();
  $('playmsg').textContent='Sprawdzam CatchUp: '+entry.title;
  var p=video.play();
  if(p&&p.catch)p.catch(function(){$('playmsg').textContent='CatchUp nie odtwarza się u dostawcy / nieobsługiwany kodek.';});
  rows();return true;
 }
 return false;
}
"""
s=s.replace(needle,helper+needle)
needle=" sync:sync,search:runSearch,select:choose,"
assert s.count(needle)==1
s=s.replace(needle," sync:sync,search:runSearch,select:choose,\n searchEpg:searchEpg,remindEpg:remindEpg,playEpg:playEpg,")
p.write_text(s)
# Search view: EPG results appear with clear verified/unverified states.
p=A/'features/search.js';s=p.read_text()
s=s.replace("results = [], xtResults = [], filter", "results = [], xtResults = [], epgResults = [], filter")
needle="results=[];xtResults=[];"
assert s.count(needle)==1
s=s.replace(needle,"results=[];xtResults=[];epgResults=[];")
needle="    if(filter==='tv'||filter==='iptv'||filter==='movie'||filter==='series') {"
assert s.count(needle)==1
s=s.replace(needle,"""    if(term.length>=3 && (filter==='all'||filter==='tv'||filter==='iptv') &&
       TV.xtream && TV.xtream.getAccounts().length && TV.xtream.searchEpg){
      TV.xtream.searchEpg(term).then(function(programs){
        if(seq!==sequence)return;
        epgResults=programs||[];draw();
      },function(){});
    }
"""+needle)
needle="    chosen=chosen.slice(0,MAX);"
assert s.count(needle)==1
s=s.replace(needle,"""    epgResults.forEach(function(e){
      var exact=chosen.find(function(item){
        if(!item.tmdb)return false;
        var itemTitle=item.tmdb.item.title||item.tmdb.item.name;
        return window.DC4IEPG.normalize(itemTitle)===window.DC4IEPG.normalize(e.title);
      });
      if(exact){(exact.epg=exact.epg||[]).push(e);}
      else if(filter==='all'||filter==='tv'||filter==='iptv')chosen.push({epg:e});
    });
"""+needle)
needle="        card.appendChild(badge);strip.appendChild(card);"
assert s.count(needle)==1
s=s.replace(needle,"""        if(entry.epg && entry.epg.length)badge.textContent+=' · TV EPG: '+entry.epg[0].channelTitle;
        card.appendChild(badge);strip.appendChild(card);""")
needle="      } else {\n        var x=entry.xtream;"
assert s.count(needle)==1
s=s.replace(needle,"""      } else if(entry.epg) {
        var e=entry.epg;
        var card=TV.el('div','card f epg-result');
        var pic=TV.el('div','pic'),title=TV.el('b','ttl');
        title.textContent=e.title;pic.appendChild(title);card.appendChild(pic);
        var date=new Date(e.time.start);
        card.appendChild(TV.el('div','cap',TV.esc(e.channelTitle+' · '+date.toLocaleString('pl-PL'))));
        var badge=TV.el('div','swhere vod-status');
        badge.textContent='EPG · '+(e.state==='now'?'Teraz':e.state==='future'?'Planowana emisja':
          e.archiveFlag?'Archiwum (sprawdź odtwarzanie)':'Archiwalna emisja');
        card.appendChild(badge);
        card.onok=function(){TV.xtream.playEpg(e);};
        strip.appendChild(card);
      } else {
        var x=entry.xtream;""")
p.write_text(s)
# In details, EPG section is beneath verified VOD and Xtream matches.
p=A/'features/details.js';s=p.read_text()
needle='<div class="dexternal"></div><div class="dextra"></div>'
assert s.count(needle)==1
s=s.replace(needle,'<div class="depg"></div><div class="dexternal"></div><div class="dextra"></div>')
needle="    var wl = btn(inList(it) ?"
assert s.count(needle)==1
s=s.replace(needle,"""    if(d && TV.xtream && TV.xtream.getAccounts().length && TV.xtream.searchEpg){
      var epgHost=box.querySelector('.depg');
      epgHost.textContent='TV / EPG: sprawdzam wybrane kanały...';
      TV.xtream.searchEpg(it.title).then(function(events){
        if(box.hidden || stack[stack.length-1]!==it)return;
        epgHost.innerHTML='';
        if(!events.length){
          epgHost.textContent='EPG: brak dopasowania w sprawdzonych kanałach (niepełny indeks).';
          return;
        }
        var header=TV.el('h3','', 'Emisje TV / EPG');epgHost.appendChild(header);
        events.slice(0,8).forEach(function(e){
          var date=new Date(e.time.start).toLocaleString('pl-PL');
          var row=TV.el('div','depgrow');
          var label=TV.el('div','depginfo');
          label.textContent=e.channelTitle+' · '+date+' · '+
            (e.state==='now'?'Trwa emisja':e.state==='future'?'Zaplanowana emisja':'Wcześniejsza emisja');
          row.appendChild(label);
          if(e.state==='now')row.appendChild(btn('▶ Oglądaj na żywo',function(){TV.xtream.playEpg(e);}));
          else if(e.state==='future')row.appendChild(btn('Przypomnij (w aplikacji)',function(){TV.xtream.remindEpg(e);}));
          else if(e.archiveFlag)row.appendChild(btn('Sprawdź CatchUp',function(){TV.xtream.playEpg(e);}));
          else row.appendChild(TV.el('span','depg-noarchive','Nagranie niedostępne'));
          epgHost.appendChild(row);
        });
        if(TV.view()==='details')TV.rebuild();
      },function(){
        if(stack[stack.length-1]===it)epgHost.textContent='EPG jest obecnie niedostępne.';
      });
    }
"""+needle)
needle="[].slice.call(box.querySelectorAll('.dexternal .f')), strip ?"
assert s.count(needle)==1
s=s.replace(needle,"[].slice.call(box.querySelectorAll('.depg .f')), [].slice.call(box.querySelectorAll('.dexternal .f')), strip ?")
p.write_text(s)
p=A/'dc4i.css';s=p.read_text()
s+='''\n/* TV/EPG source matches in canonical TMDB title details. */\n#details .depg{max-width:1240px;margin:14px 0 16px;font-size:19px;color:#cbdffb;}\n#details .depg h3{font-size:24px;margin:13px 0 10px;color:#eff4ff;}\n#details .depgrow{display:flex;justify-content:space-between;align-items:center;gap:14px;min-height:48px;margin:6px 0;padding:6px 12px;background:#152d50d0;border-radius:9px;}\n#details .depginfo{font-size:19px;line-height:1.3;max-width:820px;}\n#details .depgrow .dbtn{font-size:18px;padding:8px 12px;margin:0;white-space:nowrap;}\n#details .depg-noarchive{font-size:17px;color:#9fb1cd;}\n'''
p.write_text(s)
print('EPG_INTEGRATION_PATCH_OK')
