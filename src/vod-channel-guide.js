/* DC4I VODTV 1.2.19. TV-first guide without new server or credentials. */
(function(){
 'use strict';
 var TV=window.TV,modelAPI=window.DC4IGuideModel;
 if(!TV || !TV.xtream || !modelAPI)return;
 var tr=function(pl,en){return TV.S.uiLang==='en'?en:pl;};
 var root=TV.el('main','dc4i-guide',
  '<header class="gd-head"><div><h1>'+tr('Przewodnik IPTV','IPTV Guide')+'</h1>'+
  '<div id="gd-provider" class="gd-provider"></div></div>'+
  '<span id="gd-back" class="f gd-btn">'+tr('Wróć','Back')+'</span>'+
  '<span id="gd-config" class="f gd-btn">'+tr('Playlisty','Playlists')+'</span>'+
  '</header>'+
  '<div class="gd-layout">'+
   '<section class="gd-pane gd-group-pane"><h2>'+tr('Grupy kanałów','Channel groups')+'</h2>'+
   '<div class="gd-groups" id="gd-groups"></div></section>'+
   '<section class="gd-pane gd-channel-pane"><h2>'+tr('Kanały','Channels')+'</h2>'+
   '<div class="gd-page-label" id="gd-count"></div>'+
   '<div class="gd-channels" id="gd-channels"></div></section>'+
   '<section class="gd-pane gd-detail"><h2>'+tr('Teraz w telewizji','On TV now')+'</h2>'+
    '<div class="gd-current-channel" id="gd-current-channel"></div>'+
    '<div id="gd-status" class="gd-status"></div>'+
    '<div id="gd-metadata" class="gd-metadata"></div>'+
    '<div class="gd-program gd-now" id="gd-now"><div class="gd-eyebrow">'+tr('TERAZ','NOW')+'</div>'+
     '<div class="gd-title" id="gd-now-title"></div>'+
     '<div class="gd-time" id="gd-now-time"></div>'+
     '<div class="gd-bar"><span id="gd-progress"></span></div>'+
     '<p class="gd-description" id="gd-description"></p></div>'+
    '<div class="gd-program gd-next" id="gd-next"><div class="gd-eyebrow">'+tr('NASTĘPNIE','NEXT')+'</div>'+
     '<div class="gd-title" id="gd-next-title"></div>'+
     '<div class="gd-time" id="gd-next-time"></div></div>'+
    '<div id="gd-timeline" class="gd-timeline" hidden><div id="gd-range"></div><div id="gd-airings"></div></div>'+
    '<div class="gd-actions">'+
     '<span class="f gd-btn gd-primary" id="gd-watch">'+tr('▶ Oglądaj','▶ Watch')+'</span>'+
     '<span class="f gd-btn" id="gd-timeline-toggle">'+tr('Program 10 dni','10-day schedule')+'</span>'+
     '<span class="f gd-btn" id="gd-day-prev">'+tr('◀ Dzień','◀ Day')+'</span>'+
     '<span class="f gd-btn" id="gd-day-next">'+tr('Dzień ▶','Day ▶')+'</span>'+
     '<span class="f gd-btn" id="gd-favorite">'+tr('☆ Ulubione','☆ Favorite')+'</span>'+
     '<span class="f gd-btn" id="gd-page-prev">'+tr('◀ Poprzednia','◀ Previous')+'</span>'+
     '<span class="f gd-btn" id="gd-page-next">'+tr('Następna ▶','Next ▶')+'</span>'+
    '</div>'+
   '</section>'+
  '</div>');
 root.id='dc4i-guide';root.setAttribute('translate','no');root.hidden=true;document.body.appendChild(root);
 var $=function(id){return root.querySelector('#gd-'+id);};
 var fav=TV.store('guideFavoritesV1')||[];
 if(!Array.isArray(fav))fav=[];
 fav=fav.map(String);
 var groupId=TV.store('guideSelectedGroupV1')||'all';
 var lastChannel=String(TV.store('guideLastChannelV1')||'');
 var model=modelAPI.group([],[],fav),page=0,pageSize=48;
 var selected=null,pane='groups',groupIndex=0,channelIndex=0,actionIndex=0;
 var generation=0,epgEpoch=0,epgTimer=null,events=[],providerState='empty';
 var timelineVisible=false,timelineDay=0,timelineIndex=0;
 function storeValue(k,v){try{TV.store(k,v);}catch(e){TV.toast(tr('Nie można zapisać ustawienia','Cannot save preference'));}}
 function focusRows(){
  return [
    [ $('back'),$('config') ],
    [].slice.call($('groups').querySelectorAll('.gd-group.f')),
    [].slice.call($('channels').querySelectorAll('.gd-channel.f')),
    [].slice.call($('airings').querySelectorAll('.gd-airing.f')),
    [ $('watch'),$('favorite'),$('timeline-toggle'),$('day-prev'),$('day-next'),$('page-prev'),$('page-next') ].filter(function(el){return !el.hidden;})
  ];
 }
 function nav(){return focusRows();}
 function row(){return ({header:0,groups:1,channels:2,timeline:3,actions:4})[pane];}
 function index(){
  return pane==='header'?0:pane==='groups'?groupIndex:pane==='channels'?channelIndex:pane==='timeline'?timelineIndex:actionIndex;
 }
 function chooseFocus(){
  if(TV.view()!=='guide'||root.hidden)return;
  TV.rebuild(row(),index());
 }
 function groupForId(id){
  return model.groups.find(function(g){return g.id===id;})||model.groups[0];
 }
 function channels(){
  return model.byGroup[groupId]||[];
 }
 function shownChannels(){
  return channels().slice(page*pageSize,(page+1)*pageSize);
 }
 function status(text){$('status').textContent=text||'';}
 function setFavoriteText(){
  $('favorite').textContent=selected && fav.indexOf(selected.id)>=0 ?
    tr('★ Usuń z ulubionych','★ Remove favorite') : tr('☆ Dodaj do ulubionych','☆ Add favorite');
 }
 function groupRow(g){
  var el=TV.el('span','f gd-group'),name=TV.el('b','gd-group-name');
  el.dataset.group=g.id;name.textContent=g.title;
  el.appendChild(name);el.appendChild(TV.el('small','gd-group-count',String(g.count)));
  if(g.id===groupId)el.classList.add('gd-selected');
  el.onok=function(){switchGroup(g.id,true);};
  return el;
 }
 function renderGroups(){
  var container=$('groups');container.innerHTML='';
  model.groups.forEach(function(g){container.appendChild(groupRow(g));});
  var idx=model.groups.findIndex(function(g){return g.id===groupId;});
  groupIndex=Math.max(0,idx);
 }
 function channelRow(ch){
  var el=TV.el('span','f gd-channel'),icon=TV.el('span','gd-channel-icon');
  el.dataset.channel=ch.id;
  if(ch.icon){
    var img=document.createElement('img');img.alt='';img.loading='lazy';img.src=ch.icon;
    img.onerror=function(){img.remove();icon.textContent='TV';};
    icon.appendChild(img);
  }else icon.textContent='TV';
  var info=TV.el('span','gd-channel-info');
  var name=TV.el('b','gd-channel-name');name.textContent=ch.title;
  info.appendChild(name);
  var sub=TV.el('small','gd-channel-sub');
  sub.textContent=ch.group || tr('Kanał IPTV','IPTV channel');
  info.appendChild(sub);
  el.appendChild(icon);el.appendChild(info);
  if(fav.indexOf(ch.id)>=0)el.appendChild(TV.el('span','gd-star','★'));
  if(selected&&selected.id===ch.id)el.classList.add('gd-selected');
  el.onok=function(){selectChannel(ch,true);pane='actions';actionIndex=0;chooseFocus();};
  return el;
 }
 function renderChannels(){
  var list=channels(),pages=Math.max(1,Math.ceil(list.length/pageSize));
  page=Math.max(0,Math.min(page,pages-1));
  var from=page*pageSize,to=Math.min(from+pageSize,list.length);
  $('count').textContent=list.length ?
    tr('Kanały ','Channels ')+(from+1)+'-'+to+' / '+list.length+' · '+(page+1)+'/'+pages :
    tr('Brak kanałów w tej grupie','No channels in this group');
  var container=$('channels');container.innerHTML='';
  list.slice(from,to).forEach(function(ch){container.appendChild(channelRow(ch));});
  $('page-prev').classList.toggle('gd-disabled',page===0);
  $('page-next').classList.toggle('gd-disabled',page>=pages-1);
  var n=list.slice(from,to).findIndex(function(ch){return selected&&ch.id===selected.id;});
  channelIndex=n>=0?n:0;
 }
 function updateSelectionStyle(){
  [].slice.call(root.querySelectorAll('.gd-channel')).forEach(function(el){
    el.classList.toggle('gd-selected',!!selected&&el.dataset.channel===selected.id);
  });
  setFavoriteText();
 }
 function groupSwitchWithoutFocus(id){
  groupId=id;
  storeValue('guideSelectedGroupV1',groupId);
  page=0;
  var arr=channels();
  selected=arr.find(function(x){return x.id===lastChannel;})||arr[0]||null;
  renderGroups();renderChannels();updateSelectionStyle();
  showSelected();
 }
 function switchGroup(id,toChannels){
  if(!groupForId(id))return;
  groupSwitchWithoutFocus(id);
  pane=toChannels?'channels':'groups';
  chooseFocus();
 }
 function timeLabel(t){
  if(!Number.isFinite(+t))return '';
  return new Date(+t).toLocaleTimeString(TV.S.uiLang==='en'?'en-GB':'pl-PL',
    {hour:'2-digit',minute:'2-digit'});
 }
 function showEvent(el,titleId,timeId,event){
  $(titleId).textContent=event&&event.title||tr('Brak danych EPG','No EPG information');
  $(timeId).textContent=event&&event.time?
    timeLabel(event.time.start)+' - '+timeLabel(event.time.end):'';
 }
 function showPrograms(){
  var restoreTimelineFocus=pane==='timeline';
  var rich=TV.epgMetadata?TV.epgMetadata.guide(selected,events,providerState):{events:events,label:''};
  $('metadata').textContent=rich.label;
  if(selected && rich.status)status(rich.status);
  showTimeline();
  if(restoreTimelineFocus)chooseFocus();
  var current=modelAPI.nowNext(rich.events,Date.now());
  showEvent($('now'),'now-title','now-time',current.now);
  showEvent($('next'),'next-title','next-time',current.next);
  $('progress').style.width=modelAPI.progress(current.now,Date.now())+'%';
  $('description').textContent=current.now&&current.now.description||'';
 }
 function showTimeline(){
  $('timeline').hidden=!timelineVisible;$('now').hidden=timelineVisible;$('next').hidden=timelineVisible;
  $('day-prev').hidden=!timelineVisible;$('day-next').hidden=!timelineVisible;
  $('timeline-toggle').textContent=timelineVisible?tr('Teraz / następnie','Now / next'):tr('Program 10 dni','10-day schedule');
  var host=$('airings');host.innerHTML='';
  if(!timelineVisible||!TV.epgMetadata)return;
  var view=TV.epgMetadata.timeline(selected,timelineDay);
  $('metadata').textContent=view.label;
  status(view.events.length?tr('Lokalne metadane XMLTV','Local XMLTV metadata'):tr('Brak lokalnych danych w tym okresie','No local data in this period'));
  if(pane==='timeline'&&!view.events.length)pane='actions';
  function date(t){return new Date(t).toLocaleString(TV.S.uiLang==='en'?'en-GB':'pl-PL',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'});}
  $('range').textContent=date(view.from)+' — '+date(view.to)+' · '+(timelineDay+6)+'/10';
  view.events.slice(0,200).forEach(function(e){
   var el=TV.el('div','f gd-airing');el.setAttribute('tabindex','0');
   el.textContent=date(e.start)+' — '+date(e.end)+' · '+e.title+' · '+TV.epgMetadata.describe(e);
   // Metadata rows have no playback or reminder action.
   host.appendChild(el);
  });
  if(view.events.length>200){var limit=TV.el('div','gd-empty');limit.textContent=tr('Pokazano pierwsze 200 emisji','Showing first 200 airings');host.appendChild(limit);}
  if(!view.events.length){var empty=TV.el('div','gd-empty');empty.textContent=tr('Brak lokalnych danych w tym okresie','No local data in this period');host.appendChild(empty);}
  timelineIndex=Math.max(0,Math.min(timelineIndex,Math.min(200,view.events.length)-1));
 }
 function shiftDay(delta){timelineDay=Math.max(-5,Math.min(4,timelineDay+delta));timelineIndex=0;showPrograms();chooseFocus();}
 function showSelected(){
  ++epgEpoch;
  clearTimeout(epgTimer);
  events=[];providerState='loading';timelineIndex=0;
  if(!selected){
    $('current-channel').textContent=tr('Wybierz kanał','Select a channel');
    status(tr('Brak dostępnego kanału','No channel available'));
    showPrograms();setFavoriteText();return;
  }
  lastChannel=selected.id;storeValue('guideLastChannelV1',selected.id);
  $('current-channel').textContent=selected.title;
  status(tr('Pobieram program...','Loading programme...'));
  showPrograms();updateSelectionStyle();
  var token=epgEpoch,ch=selected;
  // Fast D-pad scrolling cancels unfired requests: do not flood a 1-connection provider.
  epgTimer=setTimeout(function(){
    TV.xtream.guideEpg(ch).then(function(list){
      if(token!==epgEpoch || root.hidden)return;
      events=Array.isArray(list)?list:[];providerState='success';
      status(events.length ? tr('Dane EPG dostawcy','Provider EPG') :
        tr('EPG niedostępne dla tego kanału','EPG not available for this channel'));
      showPrograms();
    },function(){
      if(token!==epgEpoch || root.hidden)return;
      events=[];providerState='error';status(tr('Nie można pobrać EPG','Could not load EPG'));showPrograms();
    });
  },320);
 }
 function selectChannel(ch,persist){
  if(!ch)return;
  selected=ch;
  if(persist!==false)storeValue('guideLastChannelV1',ch.id);
  showSelected();
 }
 function nextPage(delta){
  var limit=Math.max(1,Math.ceil(channels().length/pageSize));
  var n=Math.max(0,Math.min(limit-1,page+delta));
  if(n===page)return;
  page=n;channelIndex=0;selected=shownChannels()[0]||null;
  renderChannels();showSelected();pane='channels';chooseFocus();
 }
 function toggleFavorite(){
  if(!selected)return;
  var id=selected.id,index=fav.indexOf(id);
  if(index>=0)fav.splice(index,1);
  else fav.push(id);
  storeValue('guideFavoritesV1',fav.slice());
  var oldGroup=groupId,oldChannel=selected.id;
  model=modelAPI.group(model.channels,TV.xtream.getLiveCategories(),fav);
  groupId=groupForId(oldGroup).id;
  if(groupId==='favorites' && !model.byGroup.favorites.some(function(x){return x.id===oldChannel;})){
    selected=model.byGroup.favorites[0]||null;page=0;
  }
  renderGroups();renderChannels();showSelected();
  pane='actions';actionIndex=1;chooseFocus();
 }
 function watch(){
  if(!selected){
    TV.toast(tr('Najpierw wybierz kanał','Select a channel first'));return;
  }
  if(!TV.xtream.guideWatch(selected)){
    TV.toast(tr('Nie udało się uruchomić kanału','Could not open channel'));
  }
 }
 function openConfig(){
  root.hidden=true;
  TV.xtream.guideConfig(); // Legacy account management, return to guide on Back.
 }
 function renderData(items){
  model=modelAPI.group(items,TV.xtream.getLiveCategories(),fav);
  groupId=groupForId(groupId).id;
  groupSwitchWithoutFocus(groupId);
  if(!model.channels.length){
    status(TV.xtream.getAccounts().length ?
      tr('Brak kanałów w katalogu Xtream','No Xtream channels in catalog') :
      tr('Dodaj playlistę w sekcji Playlisty','Add a playlist under Playlists'));
  }
  pane='groups';chooseFocus();
 }
 function show(){
  root.hidden=false;
  var accountList=TV.xtream.getAccounts();
  $('provider').textContent=accountList.length?
    tr('Playlista: ','Playlist: ')+accountList[0].label:
    tr('Brak zapisanej playlisty','No saved playlist');
  status(tr('Ładowanie grup i kanałów...','Loading channel groups...'));
  var generationNow=++generation;
  TV.xtream.ensureCatalog().then(function(items){
    if(generationNow!==generation || TV.view()!=='guide')return;
    renderData(Array.isArray(items)?items:[]);
  },function(){
    if(generationNow!==generation || TV.view()!=='guide')return;
    renderData([]);status(tr('Nie można wczytać playlisty','Could not load playlist'));
  });
  TV.rebuild(0,0);
 }
 function hide(){
  ++generation;++epgEpoch;clearTimeout(epgTimer);root.hidden=true;
 }
 function resume(){
  root.hidden=false;
  if(TV.view()==='guide')chooseFocus();
 }
 function suspend(){root.hidden=true;}
 function navigate(k){
  var order=timelineVisible&&$('airings').querySelectorAll('.gd-airing.f').length?['header','groups','channels','timeline','actions']:['header','groups','channels','actions'];
  if(k===37||k===39){
    var n=order.indexOf(pane)+(k===39?1:-1);
    pane=order[Math.max(0,Math.min(order.length-1,n))];
    chooseFocus();return true;
  }
  if(k===38||k===40){
    var count=focusRows()[row()].length;
    if(pane==='header')return false;
    if(count<1)return true;
    var next=Math.max(0,Math.min(count-1,index()+(k===40?1:-1)));
    if(pane==='groups')groupIndex=next;
    else if(pane==='channels')channelIndex=next;
    else if(pane==='timeline')timelineIndex=next;
    else actionIndex=next;
    chooseFocus();return true;
  }
  if(k===33||k===34){
    if(pane==='channels')nextPage(k===34?1:-1);
    else if(pane==='groups'){
      groupIndex=Math.max(0,Math.min(model.groups.length-1,groupIndex+(k===34?10:-10)));
      chooseFocus();
    }
    return true;
  }
  if(k===13){
    var el=focusRows()[row()][index()];
    if(el&&el.onok)el.onok();return true;
  }
  return false;
 }
 var back=$('back'),config=$('config'),btnWatch=$('watch'),
   btnFavorite=$('favorite'),btnPrev=$('page-prev'),btnNext=$('page-next');
 back.onok=function(){TV.closeView();};
 config.onok=openConfig;btnWatch.onok=watch;btnFavorite.onok=toggleFavorite;
 $('timeline-toggle').onok=function(){timelineVisible=!timelineVisible;showPrograms();chooseFocus();};
 $('day-prev').onok=function(){shiftDay(-1);};$('day-next').onok=function(){shiftDay(1);};
 btnPrev.onok=function(){nextPage(-1);};btnNext.onok=function(){nextPage(1);};
 TV.addView('guide',{
  nav:nav,show:show,hide:hide,
  back:function(){TV.closeView();return true;},
  keydown:function(ev){return navigate(ev.keyCode);},
  onFocus:function(el){
    if(el.scrollIntoView)el.scrollIntoView({block:'nearest',inline:'nearest'});
    if(el.dataset.group && el.dataset.group!==groupId){
      groupSwitchWithoutFocus(el.dataset.group);
      pane='groups';chooseFocus();
    }else if(el.dataset.channel){
      var ch=shownChannels().find(function(x){return x.id===el.dataset.channel;});
      if(ch && (!selected || ch.id!==selected.id))selectChannel(ch,true);
    }
  }
 });
 // Existing Movies/Series views remain as-is; IPTV opens dedicated guide.
 var originalXtreamOpen=TV.xtream.open;
 TV.xtream.open=function(kind){
   if(kind==='all'||kind==='live'||kind===undefined)return TV.openView('guide');
   return originalXtreamOpen(kind);
 };
 TV.guide={resume:resume,suspend:suspend,refresh:function(){
  if(TV.view()==='guide')show();
 },key:navigate,model:function(){return model;}};
 setInterval(function(){if(TV.view()==='guide' && !root.hidden){showPrograms();if(pane==='timeline')chooseFocus();}},60000);
})();
