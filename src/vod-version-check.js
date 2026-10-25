/* DC4I VODTV version discovery, public Homebrew catalog is authoritative. */
(function(root) {
  'use strict';
  var URL = 'https://lg.darc.dev/api/apps.json';
  var CURRENT_VERSION = '__DC4I_CURRENT_VERSION__';
  function parse(version) {
    var m = /^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?$/.exec(String(version || '').trim());
    if (!m) return null;
    return {parts:[+m[1],+m[2],+m[3]],pre:m[4] || ''};
  }
  function compare(a,b) {
    var x=parse(a), y=parse(b);
    if (!x || !y) return null;
    for(var i=0;i<3;i++) {
      if(x.parts[i] !== y.parts[i]) return x.parts[i] > y.parts[i] ? 1:-1;
    }
    if(x.pre === y.pre) return 0;
    if(!x.pre) return 1;
    if(!y.pre) return -1;
    var sx=x.pre.split('.'),sy=y.pre.split('.');
    for(var j=0;j<Math.max(sx.length,sy.length);j++) {
      if(sx[j]===undefined) return -1;
      if(sy[j]===undefined) return 1;
      if(sx[j]===sy[j]) continue;
      var ax=/^\d+$/.test(sx[j]),by=/^\d+$/.test(sy[j]);
      if(ax && by) return (+sx[j] > +sy[j]) ? 1:-1;
      if(ax!==by) return ax ? -1:1;
      return sx[j] > sy[j] ? 1:-1;
    }
    return 0;
  }
  function extract(data) {
    if(!data || !Array.isArray(data.packages)) return null;
    for(var i=0;i<data.packages.length;i++) {
      var p=data.packages[i];
      if(p && p.id==='com.dc4i.vodtv') {
        var m=p.manifest || {};
        var v=m.version || p.version;
        if(!parse(v)) return null;
        return {version:v,releaseDate:m.releaseDate || m.published_at || p.releaseDate || ''};
      }
    }
    return null;
  }
  function formatDate(date) {
    var s=String(date||'').slice(0,10);
    if(!/^\d{4}-\d{2}-\d{2}$/.test(s)) return '';
    var split=s.split('-');
    return split[2]+'.'+split[1]+'.'+split[0];
  }
  function refresh(options) {
    var opts=options || {};
    var doc=root.document;
    var latest=opts.latestElement || (doc && doc.getElementById('dc4i-latest-version'));
    var badge=opts.statusElement || (doc && doc.getElementById('dc4i-build-badge'));
    var current=opts.currentVersion || CURRENT_VERSION;
    if(!latest || !badge) return Promise.resolve({state:'no-ui'});
    function show(state,version,date,label) {
      latest.textContent=version ? version+(formatDate(date) ? ' · '+formatDate(date) : ' · online') : label;
      latest.dataset.state=state;
      latest.title=label;
      badge.dataset.state=state;
      badge.textContent=label;
      badge.title=label;
      return {state:state,version:version || null};
    }
    show('checking',null,'','Sprawdzanie...');
    var fetcher=opts.fetch || root.fetch;
    if(typeof fetcher !== 'function') return Promise.resolve(show('offline',null,'','Offline'));
    // Bust any intermediaries that disregard no-store, without caching secrets.
    var url=URL+'?check='+Date.now();
    return Promise.resolve().then(function(){return fetcher(url,{cache:'no-store',credentials:'omit'});})
      .then(function(response){if(!response || !response.ok)throw Error('catalog status');return response.json();})
      .then(function(json){
        var pub=extract(json);
        if(!pub) return show('unknown',null,'','Brak danych');
        var cmp=compare(pub.version,current);
        if(cmp===null) return show('unknown',null,'','Brak danych');
        if(cmp>0) return show('update',pub.version,pub.releaseDate,'Aktualizacja dostępna');
        if(cmp===0) return show('current',pub.version,pub.releaseDate,'Aktualna');
        return show('ahead',pub.version,pub.releaseDate,'Wersja nowsza niż repo');
      })
      .catch(function(){return show('offline',null,'','Offline');});
  }
  root.DC4IVersions={compare:compare,extract:extract,refresh:refresh};
})(window);
