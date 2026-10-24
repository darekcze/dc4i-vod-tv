#!/usr/bin/env python3
"""DC4I VOD TV 1.1.1 patch after build_vod_tv.py, before ares-package.
Never changes upstream checkout or secret values. Applies only to generated build output.
"""
from pathlib import Path
import shutil
import re

R = Path(__file__).resolve().parents[1]
APP = R / 'build/dc4i-boringtv'
SRC = R / 'src'
assert APP.is_dir()

def change(file, before, after, times=1):
    p = APP / file
    old = p.read_text(encoding='utf-8')
    n = old.count(before)
    if n != times:
        raise RuntimeError(f'{file}: expected {times} occurrences of {before[:50]!r}, got {n}')
    p.write_text(old.replace(before, after), encoding='utf-8')

# Explicit streaming-app launchers (only displayed after actual getAppLoadStatus).
change('config.js',
       "    {id: 'youtube.leanback.v4', title: 'YouTube',",
       """    {id: 'io.strem.tv', title: 'Stremio', color: '#6b4fb6',
      optional: true, candidates: ['io.strem.tv','io.strem.webos','com.razagr.stremio']},
    {id: 'com.iptvsmarters.player', title: 'IPTV Smarters Player', color: '#0869b5',
      optional: true, candidates: ['com.iptvsmarters.player','com.iptv.smarters',
        'com.iptvsmarterspro','com.whmcs.iptvsmarters','com.iptv.smarterspro','iptvsmarters']},
    {id: 'youtube.leanback.v4', title: 'YouTube',""")

# Probe optional apps against webOS before showing their tiles; never imply an unverified guessed ID works.
p = APP / 'app.js'
s = p.read_text(encoding='utf-8')
start = s.index('  function probeApps() {')
end = s.index('  // Apps row order', start)
s = s[:start] + """  function probeApps() {
    return Promise.all(C.APPS.map(function(a) {
      if (!a.optional || !a.candidates) {
        return luna('com.webos.applicationManager/getAppLoadStatus',{appId:a.id})
          .then(function(r){ return r.exist ? a : null; },function(){ return a; });
      }
      var lookups=a.candidates.map(function(id) {
        return luna('com.webos.applicationManager/getAppLoadStatus',{appId:id})
          .then(function(r){return r.exist===true?id:null;},function(){return null;});
      });
      return Promise.race([
        Promise.all(lookups).then(function(ids){
          var installed=ids.filter(Boolean)[0];
          return installed ? Object.assign({},a,{id:installed}) : null;
        }),
        new Promise(function(resolve){setTimeout(function(){resolve(null);},2200);})
      ]);
    })).then(function(list) {apps=list.filter(Boolean);});
  }
""" + s[end:]
# Existing installations can have auto selected. Migrate once to Warsaw on the next update,
# then respect any explicit later 'auto' choice by keeping the migration marker.
marker = "  C.LANG = (S.uiLang === 'en' ? 'en-US' : 'pl-PL');"
assert s.count(marker)==1
s = s.replace(marker,marker+"""
  if(!store('vodWeatherCityMigrated111')) {
    if(S.weatherCity==='auto') {
      S.weatherCity='Warsaw';
      store('settings',S);
    }
    store('vodWeatherCityMigrated111',true);
  }""")
# Improve Open-Meteo geocoding when city names also exist in the US or elsewhere.
before = """    var find = city === 'auto'
      ? get('https://ipapi.co/json/').then(function (r) { return {lat: r.latitude, lon: r.longitude, name: r.city}; })
      : get('https://geocoding-api.open-meteo.com/v1/search?count=1&name=' + encodeURIComponent(city))
        .then(function (r) { var g = r.results[0]; return {lat: g.latitude, lon: g.longitude, name: g.name}; });"""
after = """    var cityCountries = {Warsaw:'PL',Krakow:'PL',Gdansk:'PL',Berlin:'DE',Paris:'FR',London:'GB',
      Rome:'IT',Madrid:'ES',Lisbon:'PT',Prague:'CZ',Vienna:'AT',Budapest:'HU',Amsterdam:'NL',
      Brussels:'BE',Copenhagen:'DK',Oslo:'NO',Stockholm:'SE',Helsinki:'FI',Dublin:'IE',
      Athens:'GR',Bucharest:'RO',Sofia:'BG',Bratislava:'SK',Ljubljana:'SI',Zagreb:'HR',
      Vilnius:'LT',Riga:'LV',Tallinn:'EE',Bern:'CH',Washington:'US',
      'New York':'US','Los Angeles':'US','San Francisco':'US',Chicago:'US',Boston:'US',
      Seattle:'US',Miami:'US',Austin:'US',Denver:'US',Sacramento:'US'};
    var cityLabels = {Warsaw:'Warszawa',Krakow:'Kraków',Gdansk:'Gdańsk',Paris:'Paryż',
      London:'Londyn',Rome:'Rzym',Madrid:'Madryt',Lisbon:'Lizbona',Prague:'Praga',
      Vienna:'Wiedeń',Stockholm:'Sztokholm',Copenhagen:'Kopenhaga',
      'New York':'Nowy Jork',Washington:'Waszyngton DC'};
    var fixedLocations={Warsaw:[52.2297,21.0122],Krakow:[50.0647,19.9450],Gdansk:[54.3520,18.6466],
      London:[51.5074,-0.1278],Paris:[48.8566,2.3522],Berlin:[52.5200,13.4050],
      Rome:[41.9028,12.4964],Madrid:[40.4168,-3.7038],
      'New York':[40.7128,-74.0060],'San Francisco':[37.7749,-122.4194],
      'Los Angeles':[34.0522,-118.2437],Washington:[38.9072,-77.0369]};
    var find = fixedLocations[city] ? Promise.resolve({
      lat:fixedLocations[city][0],lon:fixedLocations[city][1],
      name:S.uiLang==='en'?city:(cityLabels[city]||city)
    }) : city === 'auto'
      ? get('https://ipapi.co/json/').then(function (r) { return {lat: r.latitude, lon: r.longitude, name: r.city}; })
      : get('https://geocoding-api.open-meteo.com/v1/search?count=8&language='+
          (S.uiLang==='en'?'en':'pl')+'&name=' + encodeURIComponent(city))
        .then(function (r) {
          var all = r.results || [];
          var g = all.filter(function(v){return v.country_code === cityCountries[city];})[0] || all[0];
          if (!g) throw new Error('City not found: '+city);
          return {lat:g.latitude, lon:g.longitude,
            name:S.uiLang==='en' ? city : (cityLabels[city] || g.name || city)};
        });"""
assert s.count(before)==1, 'weatherLoc() source changed'
s = s.replace(before,after)
# Full weather-code translation, not text-node-only substitution.
s = s.replace('  var WXTEXT = {', '  var WXTEXT_EN = {',1)
end_obj="86: 'Snow showers', 95: 'Thunderstorm', 96: 'Thunderstorm, hail', 99: 'Thunderstorm, hail'};"
assert end_obj in s
s = s.replace(end_obj,end_obj+"""
  var WXTEXT_PL = {0:'Bezchmurnie',1:'Przeważnie bezchmurnie',2:'Częściowe zachmurzenie',
    3:'Pochmurno',45:'Mgła',48:'Mgła osadzająca szadź',51:'Lekka mżawka',53:'Mżawka',
    55:'Silna mżawka',61:'Słaby deszcz',63:'Deszcz',65:'Silny deszcz',
    66:'Marznący deszcz',67:'Intensywny marznący deszcz',71:'Słaby śnieg',
    73:'Śnieg',75:'Intensywny śnieg',77:'Ziarnisty śnieg',
    80:'Przelotny deszcz',81:'Przelotne opady',82:'Ulewa',
    85:'Przelotny śnieg',86:'Silny przelotny śnieg',
    95:'Burza',96:'Burza z gradem',99:'Silna burza z gradem'};
  var WXTEXT = S.uiLang==='en' ? WXTEXT_EN : WXTEXT_PL;
  function wt(pl,en) {return S.uiLang==='en'?en:pl;}""")
for before,after in [
    ("i === start ? 'Now'","i === start ? wt('Teraz','Now')"),
    ("j === 0 ? 'Today'","j === 0 ? wt('Dziś','Today')"),
    ("'  ·  H ' +", "'  ·  ' + wt('maks. ','H ') +"),
    ("'°  L ' +", "'°  ' + wt('min. ','L ') +"),
    ("<small>Feels like</small>","<small>' + wt('Odczuwalna','Feels like') + '</small>"),
    ("<small>Humidity</small>","<small>' + wt('Wilgotność','Humidity') + '</small>"),
    ("<small>Wind</small>","<small>' + wt('Wiatr','Wind') + '</small>"),
    ("<small>Sunrise</small>","<small>' + wt('Wschód słońca','Sunrise') + '</small>"),
    ("<small>Sunset</small>","<small>' + wt('Zachód słońca','Sunset') + '</small>"),
    ("<h4>Next 12 hours</h4>","<h4>' + wt('Kolejne 12 godzin','Next 12 hours') + '</h4>"),
    ("<h4>Next ' + d.time.length + ' days</h4>",
     "<h4>' + wt('Kolejne ','Next ') + d.time.length + wt(' dni',' days') + '</h4>"),
    ("<span class=\"wxbtn wide f\" data-wx=\"city\">Change city</span>",
     "<span class=\"wxbtn wide f\" data-wx=\"city\">' + wt('Zmień miasto','Change city') + '</span>"),
    ("<div class=\"wxload\">Loading weather…</div>",
     "<div class=\"wxload\">' + wt('Ładowanie pogody…','Loading weather…') + '</div>"),
    ("'Couldn’t load the weather. Check the connection.'",
     "wt('Nie udało się pobrać pogody. Sprawdź połączenie.','Could not load weather. Check connection.')")
]:
    if before not in s: raise RuntimeError('weather patch pattern missing: '+before)
    s=s.replace(before,after)
p.write_text(s,encoding='utf-8')

# Smart contextual links, shown only when selected-country providers don't offer a streaming subscription.
p=APP/'features/details.js'
s=p.read_text(encoding='utf-8')
old="""      var tr = ((d.videos || {}).results || []).filter(function (v) { return v.site === 'YouTube' && v.type === 'Trailer'; })[0];"""
insert="""      var subscriptions=(here.flatrate||[]).concat(here.free||[],here.ads||[]);
      if (!subscriptions.length && TV.vodPlayers) {
        btns.appendChild(btn('▶ '+(TV.S.uiLang==='en'?'Open Stremio':'Otwórz Stremio'),
          function(){TV.vodPlayers.open('stremio',it.title);}));
        btns.appendChild(btn('▶ '+(TV.S.uiLang==='en'?'Open IPTV Smarters Player':'Otwórz IPTV Smarters Player'),
          function(){TV.vodPlayers.open('iptv',it.title);}));
        extra += (extra ? '  ·  ':'')+
          (TV.S.uiLang==='en'?'Own legal sources are required.':'Wymagane własne, legalne źródła.');
      }
""" + old
assert s.count(old)==1
p.write_text(s.replace(old,insert),encoding='utf-8')

# Dedicated TV search replaces upstream search module, with TMDB regional classification.
shutil.copy2(SRC/'vod-search.js',APP/'features/search.js')
with (APP/'features/search.css').open('a',encoding='utf-8') as output:
    output.write('\n'+(SRC/'vod-search.css').read_text(encoding='utf-8'))

# Player launcher loaded after TV exists, before details/search features initialise.
shutil.copy2(SRC/'vod-fallback.js',APP/'vod-fallback.js')
p=APP/'index.html'
s=p.read_text(encoding='utf-8')
old='<script src="features/details.js"></script>'
assert s.count(old)==1
p.write_text(s.replace(old,'<script src="vod-fallback.js"></script>\n'+old),encoding='utf-8')
print('V111_PATCH_OK','weather_pl','city_geocode','stremio','iptv_probe','vod_search_filter')
