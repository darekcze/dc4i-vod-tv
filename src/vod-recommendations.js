/* DC4I VOD TV: deterministic local recommendations, per-profile storage belongs
   to the caller. Rating source is TMDB, not a claimed independent IMDb score. */
(function (root) {
  'use strict';
  var GENRES = {
    scifi: [878, 10765], horror: [27],
    family: [10751, 10762], romance: [10749],
    reality: [10764], comedy: [35], drama: [18],
    action: [28, 10759], documentary: [99]
  };
  var defaults = {
    enabled: true, favouriteGenre: 'scifi', sciFiMin: 6, horrorMin: 9,
    otherMin: 7, hideHorror: false, eveningBoost: true,
    learnHistory: true, hideOpened: false
  };
  function settings(input) {
    var x = Object.assign({}, defaults, input || {});
    ['sciFiMin','horrorMin','otherMin'].forEach(function (k) {
      var n=Number(x[k]);
      x[k] = Number.isFinite(n) ? Math.max(0,Math.min(10,n)) : defaults[k];
    });
    if (!GENRES[x.favouriteGenre] && x.favouriteGenre !== 'auto') x.favouriteGenre='scifi';
    return x;
  }
  function genres(item) {
    var data=item.genre_ids || item.genres || [];
    return Array.isArray(data) ? data.map(function (g) {
      return Number((typeof g==='object'&&g) ? g.id : g);
    }).filter(function (g) {return Number.isFinite(g);}) : [];
  }
  function has(g,cat){return GENRES[cat].some(function(id){return g.indexOf(id)>=0;});}
  function typeOf(item) {
    var t=(item.tmdb||{}).type || item.media_type || item.type || (item.title?'movie':'tv');
    return t==='series'?'tv':t;
  }
  function identity(item) {
    var id=(item.tmdb||{}).id || item.id;
    if(id)return typeOf(item)+':'+String(id);
    return typeOf(item)+':'+String(item.title||item.name||'').toLowerCase();
  }
  function ratingOf(item) {
    var value=item.vote_average!=null?item.vote_average:item.rating;
    var n=Number(value);
    return value!=null && value!=='' && Number.isFinite(n) && n>0 && n<=10 ? n : null;
  }
  function yearOf(item) {
    var m=String(item.release_date||item.first_air_date||item.year||'').match(/(?:19|20)\d{2}/);
    return m ? Number(m[0]) : null;
  }
  function score(item, input, history, clock) {
    var pref=settings(input), zero={eligible:false,score:0,reason:'',rating:null};
    if (!pref.enabled || !item) return zero;
    var g=genres(item), horror=has(g,'horror'), sciFi=has(g,'scifi'), rating=ratingOf(item);
    if (horror&&pref.hideHorror)return Object.assign({},zero,{reason:'Horrory ukryte'});
    if(rating===null)return Object.assign({},zero,{reason:'Brak potwierdzonej oceny'});
    var min=horror ? pref.horrorMin : sciFi ? pref.sciFiMin : pref.otherMin;
    if(rating<min)return Object.assign({},zero,{rating:rating,reason:'Ocena poniżej progu'});
    var historyArr=Array.isArray(history)?history:[];
    var key=identity(item);
    if(pref.hideOpened && historyArr.some(function(e){return e&&e.key===key && e.action==='opened';}))
      return Object.assign({},zero,{rating:rating,reason:'Wcześniej otwarte'});
    var now=Number.isFinite(Number(clock))?Number(clock):Date.now();
    var date=new Date(now),evening=date.getHours()>=18 && date.getHours()<=23;
    var favourite=pref.favouriteGenre!=='auto'&&has(g,pref.favouriteGenre);
    var votes=Math.max(0,Number(item.vote_count)||0);
    var popularity=Math.max(0,Number(item.popularity)||0);
    var base=rating*5.5;
    var confidence=Math.min(7,Math.log1p(votes)*1.2);
    var popularityBonus=Math.min(7,Math.log1p(popularity)*1.8);
    var release=yearOf(item),current=date.getFullYear();
    var newTitle=release && release>=current-2 && release<=current+1;
    var temporal= newTitle ? 4:0;
    var eveningFamily=pref.eveningBoost && evening && (has(g,'romance')||has(g,'family'));
    var bonus=favourite ? 17:0;
    var recentSignals=0;
    if(pref.learnHistory && historyArr.length && g.length){
      historyArr.forEach(function(e){
        var observed=e&&e.provenance==='native-media-progression'&&e.seconds>=30&&(e.action==='observed-partial'||e.action==='observed-completed');
        if (!e || (!observed&&e.action!=='opened' && e.action!=='completed') || !Array.isArray(e.genres))return;
        if(now-Number(e.at)>90*86400000 || now<Number(e.at))return;
        if(e.genres.some(function(x){return g.indexOf(x)>=0;})){
          recentSignals+=observed?(e.action==='observed-completed'?2:1):1;
          if(observed&&new Date(e.at).getDay()===date.getDay()&&Math.abs(new Date(e.at).getHours()-date.getHours())<=1)recentSignals+=0.5;
        }
      });
    }
    var affinity=Math.min(9,recentSignals*3);
    var scoreNum=Math.max(0,Math.min(100,Math.round(base+confidence+popularityBonus+temporal+bonus+affinity+(eveningFamily?9:0))));
    var reason=eveningFamily?'Wieczorne familijne / romantyczne':
      favourite ? ({scifi:'Sci-Fi',family:'Familijne',romance:'Romantyczne',reality:'Reality',comedy:'Komedia',drama:'Dramat',action:'Akcja',documentary:'Dokument',horror:'Horror'}[pref.favouriteGenre]||'Ulubiony gatunek') :
      affinity>=6 ? 'Podobne do Twoich wyborów' : rating>=8.5 ? 'Wysoko oceniane' : newTitle ? 'Nowa produkcja' : 'Dopasowanie do profilu';
    return {eligible:true,score:scoreNum,reason:reason,rating:rating};
  }
  function rank(candidates,pref,history,now) {
    var visited={};
    var ranked=(candidates||[]).map(function(item,index){
      return {item:item,details:score(item,pref,history,now),index:index};
    }).filter(function(row){
      if(!row.details.eligible)return false;
      var k=identity(row.item);
      if(visited[k])return false;
      visited[k]=true;return true;
    }).sort(function(a,b){return b.details.score-a.details.score || a.index-b.index;});
    return ranked.map(function(row){
      return {item:row.item,score:row.details.score,reason:row.details.reason,rating:row.details.rating};
    });
  }
  function record(history,item,action,at) {
    var list=Array.isArray(history)?history.slice():[];
    if(!item || (action!=='opened'&&action!=='completed'))return list;
    var time=Number.isFinite(Number(at))?Number(at):Date.now();
    list.push({key:identity(item),action:action,at:time,genres:genres(item)});
    return list.slice(-150);
  }
  root.DC4IRecommender={defaults:defaults,settings:settings,score:score,rank:rank,record:record,identity:identity,genres:genres};
})(window);
