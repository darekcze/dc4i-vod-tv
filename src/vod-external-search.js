/* DC4I VOD TV: one source of truth for external title search controls. */
(function () {
  'use strict';
  var TV = window.TV;
  if (!TV) return;
  var engines = [
    {id:'youtube',label:'YouTube'},
    {id:'kodi',label:'Kodi'},
    {id:'plex',label:'Plex'},
    {id:'stremio',label:'Stremio'},
    {id:'smarters',label:'Smarters Player'}
  ];
  function tr(pl,en){return TV.S.uiLang==='en'?en:pl;}
  function open(id,options) {
    var opts=options || {}, name=String(opts.title||'').trim();
    if(!name){TV.toast(tr('Wpisz tytuł do wyszukania','Enter a title to search'));return false;}
    var tmdb=opts.tmdb, details=opts.details||null;
    if(id==='youtube')return TV.vodHandoff.youtubeSearch(name);
    if(id==='kodi'){
      if(tmdb && tmdb.id && tmdb.type) return TV.vodHandoff.kodi(name,tmdb);
      return TV.vodHandoff.kodiSearch(name);
    }
    if(id==='plex')return TV.vodHandoff.plexSearch(name);
    if(id==='stremio')return TV.vodPlayers.open('stremio',name,tmdb,details);
    if(id==='smarters')return TV.vodPlayers.open('iptv',name,tmdb,details);
    return false;
  }
  function render(container,opts) {
    var options=opts||{},heading=TV.el('div','vx-label',tr('Szukaj w:','Search in:'));
    var row=TV.el('div','vx-engines'),buttons=[];
    engines.forEach(function(engine){
      var el=TV.el('span','f vx-engine vx-'+engine.id,engine.label);
      el.onok=function(){return open(engine.id,options);};
      row.appendChild(el);buttons.push(el);
    });
    // Render is idempotent, including when TMDB details are refreshed.
    while(container.firstChild)container.removeChild(container.firstChild);
    container.appendChild(heading);container.appendChild(row);
    return buttons;
  }
  TV.vodExternalSearch={render:render,open:open,engines:engines};
})();
