/* DC4I VOD TV: metadata-aware TV-local Kodi handoff and title searches. */
(function () {
  'use strict';
  var TV=window.TV;
  if (!TV) return;
  function tr(pl,en){return TV.S.uiLang==='en'?en:pl;}
  function toast(msg){TV.toast(msg);}
  // LG may keep Kodi running in the background, or terminate it. In the first
  // case use its local-only service, in the second pass the title at native launch.
  var LOCAL_KODI='http://127.0.0.1:18761/open';
  function kodi(title,tmdb){
    if(!tmdb||!/^\d{1,10}$/.test(String(tmdb.id||''))){
      toast(tr('Brak identyfikatora TMDB','Missing TMDB ID'));
      return Promise.resolve(false);
    }
    if(!TV.onTV){toast(tr('Funkcja jest dostępna na LG TV','Requires LG TV'));return Promise.resolve(false);}
    var payload={title:String(title||'').slice(0,180),
      type:tmdb.type==='tv'?'series':'movie',tmdb:String(tmdb.id)};
    function launch(){
      return TV.luna('com.webos.applicationManager/launch',
        {id:'org.xbmc.kodi',params:{dc4i:payload}})
        .then(function(result){
          if(result&&result.returnValue!==false)return true;
          toast(tr('Nie udało się uruchomić Kodi','Cannot launch Kodi'));
          return false;
        },function(){toast(tr('Nie udało się uruchomić Kodi','Cannot launch Kodi'));return false;});
    }
    var probe = fetch(LOCAL_KODI,{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify(payload)}).then(function(resp){
        if(!resp.ok)throw Error('Kodi status '+resp.status);
        return resp.json();
      });
    // A non-running Kodi cannot answer on loopback. Do not make the user wait
    // for a long network timeout before starting the native application.
    var request = new Promise(function(resolve,reject){
      var timer=setTimeout(function(){reject(Error('bridge-timeout'));},1800);
      probe.then(function(v){clearTimeout(timer);resolve(v);},
        function(e){clearTimeout(timer);reject(e);});
    });
    return request.then(function(answer){
      if(answer&&answer.ok)return launch();
      if(answer&&answer.error==='not-in-provider'){
        toast(tr('Tytułu nie ma w Twoim katalogu Xtream','Title not found in Xtream'));
        return false;
      }
      if(answer&&answer.error==='xtream-not-configured'){
        toast(tr('Skonfiguruj konto Xtream w Kodi','Configure Xtream in Kodi'));
        return false;
      }
      return launch();
    },function(){return launch();});
  }
  function plexSearch(title){
    var url='https://app.plex.tv/desktop#!/search?query='+encodeURIComponent(String(title||''));
    if(!TV.onTV){toast(url);return Promise.resolve(false);}
    return TV.luna('com.webos.applicationManager/launch',
      {id:'com.webos.app.browser',params:{target:url,fullMode:true}})
      .then(function(r){return r&&r.returnValue!==false;},function(){toast(tr('Nie udało się otworzyć Plex Web','Plex Web could not open'));return false;});
  }
  function youtubeSearch(title){
    var url='https://www.youtube.com/tv#/search?q='+encodeURIComponent(String(title||''));
    if(!TV.onTV){toast(url);return Promise.resolve(false);}
    return TV.luna('com.webos.applicationManager/launch',
      {id:'youtube.leanback.v4',params:{contentTarget:url}})
      .then(function(r){return r&&r.returnValue!==false;},function(){toast(tr('YouTube nie otworzył wyszukiwarki','YouTube search could not open'));return false;});
  }
  TV.vodHandoff={kodi:kodi,plexSearch:plexSearch,youtubeSearch:youtubeSearch};
})();
