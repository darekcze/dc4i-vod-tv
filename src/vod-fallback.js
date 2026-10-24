/* DC4I VOD TV: LG webOS local-app fallback, no illegal streaming sources. */
(function() {
  'use strict';
  var TV=window.TV;if(!TV)return;
  var tr=function(pl,en){return TV.S.uiLang==='en'?en:pl;};
  // Official LG Content Store Stremio app ID is io.strem.tv.
  // IPTV Smarters LG app ID differs by publisher/region; candidates are probes ONLY, not verified app IDs.
  var players={
    stremio:{name:'Stremio',ids:['io.strem.tv','io.strem.webos','com.razagr.stremio']},
    iptv:{name:'IPTV Smarters Player',
      ids:['com.iptvsmarters.player','com.iptv.smarters','com.iptvsmarterspro','com.whmcs.iptvsmarters','com.iptv.smarterspro','iptvsmarters']}
  };
  var resolved={};
  function test(id) {
    if(!TV.onTV) return Promise.resolve(null);
    return TV.luna('com.webos.applicationManager/getAppLoadStatus',{appId:id})
      .then(function(r){return r.exist===true?id:null;},function(){return null;});
  }
  function find(name) {
    if(resolved[name])return Promise.resolve(resolved[name]);
    var list=(players[name]||{}).ids||[];
    var lookups=list.map(test);
    return Promise.race([
      Promise.all(lookups).then(function(ids){
        var installed=ids.filter(Boolean)[0]||null;
        if(installed)resolved[name]=installed;
        return installed;
      }),
      new Promise(function(resolve){setTimeout(function(){resolve(null);},3500);})
    ]);
  }
  function open(name,title) {
    var cfg=players[name];
    if(!cfg)return TV.toast(tr('Nieznana aplikacja','Unknown app'));
    if(!TV.onTV)return TV.toast(tr('Na telewizorze otworzy się ','Would open ')+cfg.name);
    find(name).then(function(id){
      if(!id) {
        TV.toast(tr('Nie udało się wykryć '+cfg.name+' na tym telewizorze',
          'Could not confirm '+cfg.name+' on this TV'));
        return;
      }
      // Stremio's deep-link convention is documented, webOS handling is NOT verified.
      // If the app ignores the link it still opens normally; the user can search there.
      var args=name==='stremio' && title?
        {contentTarget:'stremio:///search?search='+encodeURIComponent(title)}:{};
      TV.launch(id,args);
    });
  }
  TV.vodPlayers={find:find,open:open,players:players};
})();
