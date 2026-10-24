#!/usr/bin/env python3
"""Release 1.2.2: Smarters Player tile and external title handoff UI."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
A=R/'build/dc4i-vodtv'
def replace(path,old,new,expected=1):
 p=A/path
 s=p.read_text(encoding='utf-8')
 found=s.count(old)
 if found!=expected:raise RuntimeError(str(path)+' expected '+str(expected)+' matches, found '+str(found)+': '+old[:120])
 p.write_text(s.replace(old,new),encoding='utf-8')
# Old documented com.iptvsmarters.app ID may refer to a different LG distribution.
# The owner's LG Store catalog number 1231221 is NOT verified as an app launch ID.
replace('config.js',"""    {id: 'com.iptvsmarters.app', title: 'IPTV Smarters Player', color: '#0869b5',
      optional: true, candidates: ['com.iptvsmarters.app','com.iptvsmarters.player',
        'com.iptv.smarters','com.smartersplayer.app','smartersplayer',
        'com.iptvsmarterspro','com.whmcs.iptvsmarters',
        'com.iptv.smarterspro','iptvsmarters']},""",
"""    {id: 'com.iptvsmarters.app', title: 'Smarters Player', color: '#0869b5',
      playerKey: 'iptv', keepTile: true, storeId: '1231221',
      optional: true, candidates: ['com.iptvsmarters.app','com.iptvsmarters.player',
        '1231221','com.iptv.smarters','com.smartersplayer.app',
        'smartersplayer','com.iptvsmarterspro','com.whmcs.iptvsmarters',
        'com.iptv.smarterspro','iptvsmarters']},""")
# In non-root mode a failed/denied getAppLoadStatus must NOT hide a player
# that the user confirmed is installed.
replace('app.js',"""          resolve(id ? Object.assign({},a,{id:id}):null);""",
"""          resolve(id ? Object.assign({},a,{id:id,unverified:false}) :
            a.keepTile ? Object.assign({},a,{id:'vod-smarters-unverified',
              unverified:true,playerKey:'iptv'}) : null);""")
# Preserve Smarters tile with a rooted helper too, even if its ID is absent in
# the native list because it is a store app without launch-point permissions.
replace('app.js',"""      apps = r.apps;
      return Promise.all(apps.map(function (a) {""",
"""      apps = r.apps;
      var smarters=C.APPS.filter(function(a){return a.keepTile;})[0];
      if(smarters && !apps.some(function(a){
        return /smarters|iptv\\s*smarter/i.test((a.title||'')+' '+(a.id||''));
      }))apps.push(Object.assign({},smarters,{id:'vod-smarters-unverified',unverified:true}));
      return Promise.all(apps.map(function (a) {""")
# Avoid treating a deliberate unverified tile as an actual native installed app.
replace('app.js',"""        if(re.test((apps[i].title||'')+' '+(apps[i].id||'')))return apps[i];""",
"""        if(!apps[i].unverified && re.test((apps[i].title||'')+' '+(apps[i].id||'')))return apps[i];""")
replace('app.js',"""    t.onok = function () { editing ? openAppMenu(a) : launch(a.id); };""",
"""    t.onok = function () {
      if(editing)return openAppMenu(a);
      if(a.playerKey==='iptv' || /smarters|iptv\\s*smarter/i.test(a.title||'')){
        return TV.vodPlayers ? TV.vodPlayers.open('iptv','') : launch(a.id);
      }
      return launch(a.id);
    };""")
# Native Stremio's webOS shell may ignore contentTarget. Give a separately
# labeled direct web-app URL, whose browser can navigate to the selected IMDb ID.
replace('features/details.js',
"""        btns.appendChild(btn('▶ '+(TV.S.uiLang==='en'?'Open Stremio':'Otwórz Stremio'),
          function(){TV.vodPlayers.open('stremio',it.title,it.tmdb,d);}));
        btns.appendChild(btn('▶ '+(TV.S.uiLang==='en'?'Open IPTV Smarters Player':'Otwórz IPTV Smarters Player'),
          function(){TV.vodPlayers.open('iptv',it.title,it.tmdb,d);}));""",
"""        btns.appendChild(btn('▶ '+(TV.S.uiLang==='en'?'Stremio app':'Stremio - aplikacja'),
          function(){TV.vodPlayers.open('stremio',it.title,it.tmdb,d);}));
        btns.appendChild(btn('▶ '+(TV.S.uiLang==='en'?'Stremio Web (open title)':'Stremio Web (otwórz tytuł)'),
          function(){TV.vodPlayers.openWeb(it.title,it.tmdb,d);}));
        btns.appendChild(btn('▶ '+(TV.S.uiLang==='en'?'Smarters Player':'Smarters Player'),
          function(){TV.vodPlayers.open('iptv',it.title,it.tmdb,d);}));""")
# Mark a forced tile as not yet confirmed by LG, without hiding it.
p=A/'app.js'
s=p.read_text(encoding='utf-8')
start=s.index('  function appTile(a) {')
end=s.index('  // Edit mode',start)
part=s[start:end]
old="esc(a.title) + '</div>';"
new="esc(a.title) + (a.unverified ? ' · sprawdź' : '') + '</div>';"
assert part.count(old)==1, 'appTile markup changed'
s=s[:start]+part.replace(old,new)+s[end:]
p.write_text(s,encoding='utf-8')
replace('features/details.js',
    "    if (prev) render(prev, d && !d.then ? d : null); else { box.hidden = true; box.innerHTML = ''; }",
    "    if (prev) render(prev, d && !d.then ? d : null); else { box.hidden = true; box.innerHTML = ''; var search=document.getElementById('search'); if(search && document.querySelector('#sres .card'))search.hidden=false; }")
# Do not launch the distinct Smarters Player Pro product from LG Store 950615.
# Only trial the user's requested LG Store listing 1231221.
p=A/'config.js';s=p.read_text(encoding='utf-8')
start=s.index("    {id: 'com.iptvsmarters.app', title: 'Smarters Player'")
end=s.index("    {id: 'youtube.leanback.v4'",start)
s=s[:start]+'''    {id: '1231221', title: 'IPTV Smarters Player', color: '#0869b5',
      playerKey:'iptv', keepTile:true, storeId:'1231221',
      optional:true, candidates:['1231221']},
'''+s[end:]
p.write_text(s,encoding='utf-8')
print('V122_PATCH_READY: store ID 1231221, persistent Smarters tile, launch diagnostics, native/web Stremio links')
