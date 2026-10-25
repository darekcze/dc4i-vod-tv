/* DC4I guide model: deterministic, no provider access, no credentials. */
(function(root){
  'use strict';
  function validEvent(e) {
    return !!(e && e.time && isFinite(+e.time.start) && isFinite(+e.time.end) &&
      +e.time.end > +e.time.start);
  }
  function nowNext(events, now) {
    var when=isFinite(+now)?+now:Date.now(), live=null, upcoming=null;
    (Array.isArray(events)&&events.length<=20000?events:[]).filter(validEvent).slice().sort(function(a,b) {
      return +a.time.start - +b.time.start;
    }).forEach(function(e){
      var start=+e.time.start, stop=+e.time.end;
      if(start<=when && when<stop){
        if(!live || +live.time.start<start)live=e;
      }else if(start>when && (!upcoming || start<+upcoming.time.start))upcoming=e;
    });
    return {now:live,next:upcoming};
  }
  function progress(event, now) {
    if(!validEvent(event))return 0;
    var current=isFinite(+now)?+now:Date.now();
    return Math.max(0,Math.min(100,Math.round((current-(+event.time.start)) /
      ((+event.time.end)-(+event.time.start))*100)));
  }
  function group(records,categories,favorites) {
    var live=[],seen=Object.create(null),favoriteSet=Object.create(null),byGroup=Object.create(null);byGroup.all=[];byGroup.favorites=[];
    if(!Array.isArray(records)||records.length>200000||!Array.isArray(categories)||categories.length>5000||!Array.isArray(favorites)||favorites.length>5000)return {groups:[{id:'all',title:'Wszystkie kanały',count:0},{id:'favorites',title:'Ulubione',count:0}],byGroup:byGroup,channels:[],limited:true};
    (favorites||[]).forEach(function(id){favoriteSet[String(id)]=true;});
    (records||[]).forEach(function(raw){
      if(!raw || raw.type!=='live' || !raw.id)return;
      var id=String(raw.id);if(id.length>200)return;
      if(seen[id])return;
      seen[id]=true;
      var x={id:id,type:'live',title:String(raw.title||raw.name||'Nieznany kanał').slice(0,500),
        group:String(raw.group||'').slice(0,200),category:String(raw.category||'').slice(0,200),
        icon:/^https?:\/\//.test(String(raw.icon||''))?String(raw.icon).slice(0,2048):'',
        epgId:String(raw.epgId||'').slice(0,200),archive:Number(raw.archive||0)};
      live.push(x);
    });
    var groupList=[
      {id:'all',title:'Wszystkie kanały',count:live.length},
      {id:'favorites',title:'Ulubione',count:0}
    ];
    byGroup.all=live;
    var named=Object.create(null);
    (categories||[]).filter(function(c){return c && c.type==='live' && c.id;})
      .forEach(function(c){named[String(c.id)]=String(c.title||c.name||'').slice(0,200);});
    var groupOrder=[];
    live.forEach(function(x){
      var gid=x.category ? 'g:'+x.category : 'g:unknown';
      if(!byGroup[gid]){byGroup[gid]=[];groupOrder.push(gid);}
      byGroup[gid].push(x);
      if(favoriteSet[x.id])byGroup.favorites.push(x);
    });
    groupList[1].count=byGroup.favorites.length;
    groupOrder.forEach(function(gid){
      var xs=byGroup[gid],rawId=gid.slice(2);
      groupList.push({id:gid,title:named[rawId]||xs[0].group||'Pozostałe',
        count:xs.length});
    });
    return {groups:groupList,byGroup:byGroup,channels:live};
  }
  root.DC4IGuideModel={group:group,nowNext:nowNext,progress:progress};
})(window);
