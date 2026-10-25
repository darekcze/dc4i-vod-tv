#!/usr/bin/env python3
"""DC4I VOD TV, spacious TV-readable, owner-personalized quick panel."""
from pathlib import Path
import json, re

R = Path(__file__).resolve().parents[1]
APP = R / "build/dc4i-vodtv"
html_path = APP / "index.html"
source = html_path.read_text(encoding="utf-8")

new_about = '''<section class="dc4i-about" aria-label="O aplikacji">
    <div class="dc4i-about-heading">
      <div class="dc4i-about-brand">
        <span class="f dc4i-about-logo" data-q="logo" title="Otwórz stronę DC4i"><img src="icon.png" alt="DC4i VODTV"></span>
        <div><b>DC4i VODTV</b><small>O aplikacji · LG webOS</small></div>
      </div>
      <span class="dc4i-build-badge">v1.2.11</span>
    </div>
    <div class="dc4i-about-data">
      <div><span>App Version</span><strong id="dc4i-app-version">1.2.11 · 25.10.2026</strong></div>
      <div><span>Latest Version</span><strong id="dc4i-latest-version">Sprawdzanie...</strong></div>
      <div class="dc4i-about-developer"><span>Developer</span><strong>Dariusz Czechowicz · DC4i Labs</strong></div>
    </div>
    <div class="dc4i-quick-links qrow">
      <a class="f" data-q="repo" href="https://lg.darc.dev"><span>App repo</span><b>lg.darc.dev ↗</b></a>
      <a class="f" data-q="website" href="https://www.dc4i.com"><span>Website</span><b>dc4i.com ↗</b></a>
    </div>
    <div class="dc4i-dedication">
      <h3>Z dedykacją dla mojej najdroższej Ani i ukochanej rodziny.</h3>
      <p>Mojej miłości, mojemu wsparciu i najpiękniejszej części każdego dnia.</p>
      <div class="dc4i-verse">
        <p>„Wśród tysięcy historii, które możemy obejrzeć, najpiękniejszą jest ta, którą piszemy razem.</p>
        <p>I gdybym mógł wybierać raz jeszcze, w każdej historii odnalazłbym Was.</p>
        <p>Bo gdzie Wy jesteście, tam jest mój dom. A gdzie jesteśmy razem, tam jest całe moje szczęście.”</p>
      </div>
      <p class="dc4i-signature">Na zawsze Wasz, Darek.</p>
      <small>Made with love · 2026</small>
    </div>
  </section>'''
assert source.count('<section class="dc4i-about"') == 1
source, count = re.subn(r'<section class="dc4i-about"[^>]*>[\s\S]*?</section>', lambda m: new_about, source, count=1)
assert count == 1
# Remove the accidental empty controls row from the previous design.
source = source.replace('<div class="qrow"></div>\n  <div class="qrow">', '<div class="qrow">', 1)
# Screen off needs the rooted LG helper; do not occupy a whole row on non-root LG.
source = source.replace('<div class="qrow"><span class="tile f" data-q="screenoff">',
                        '<div class="qrow dc4i-root-only"><span class="tile f" data-q="screenoff">', 1)
html_path.write_text(source, encoding="utf-8")

css_path = APP / "dc4i.css"
css = css_path.read_text(encoding="utf-8")
for marker in ("/* DC4I personalized quick-settings about card.", "/* DC4I designer edition 1.2.11:"):
    if marker in css:
        css = css[:css.index(marker)]
        break
css += """
/* DC4I designer edition 1.2.11: native 1920x1080 TV, generous readable quick panel. */
#qpanel {
  width:900px;
  max-width:calc(100vw - 64px);
  top:18px; right:20px; bottom:18px;
  background:linear-gradient(155deg,#122752 0%,#0b1940 53%,#0a1635 100%);
  border:1px solid rgba(123,163,225,.32);
  border-radius:26px;
  box-shadow:0 28px 90px rgba(0,0,0,.72),inset 0 1px rgba(255,255,255,.08);
}
#quick {
  box-sizing:border-box; padding:17px 30px 18px; height:100%;
  display:flex; flex-direction:column;
  overflow-y:auto; overscroll-behavior:contain;
}
#quick>.qrow { flex-shrink:0; margin-bottom:12px; }
#quick>.qhead { margin-bottom:8px; }
#quick #qdate { font-size:23px; color:#bacbec; }
#quick #qtime { font-size:47px; font-weight:650; letter-spacing:-1px; }
#quick .tile { height:68px; border-radius:17px; padding:0 20px; }
#quick .tile svg { width:26px; height:26px; margin-right:13px; }
#quick .tile .tl b { font-size:23px; font-weight:580; }
#quick .tile .tl small { font-size:19px; color:#c7d7f4; }
#quick .tile.focus .tl small { color:#133651; }
#quick .qvol .vbtn { width:78px; font-size:30px; }
#quick .qvol .vlabel { font-size:24px; color:#cfdbf4; }
#quick .qvol .vlabel b { color:#f4f7ff; }
#quick .qrow:empty { display:none; }
#quick .dc4i-root-only { display:none; }
#quick .dc4i-about { margin-top:2px; padding:10px 0 0; border-top:1px solid rgba(141,179,243,.24); flex:0 0 auto; color:#edf5ff; }
#quick .dc4i-about-heading { display:flex; align-items:center; justify-content:space-between; gap:16px; margin-bottom:12px; }
#quick .dc4i-about-brand { display:flex;align-items:center;gap:16px; min-width:0; margin:0; }
#quick .dc4i-about-brand img { width:80px;height:80px;object-fit:contain;border-radius:16px;display:block; }
#quick .dc4i-about-brand b { display:block; font-size:34px; font-weight:700; letter-spacing:-.7px; white-space:nowrap; }
#quick .dc4i-about-brand small { display:block;font-size:20px;color:#c4d4ef;margin-top:3px; }
#quick .dc4i-build-badge {flex:0 0 auto;padding:9px 15px;border-radius:24px;background:rgba(129,180,242,.12);border:1px solid rgba(129,180,242,.28);color:#c8e8ff;font-size:21px;font-weight:600;}
#quick .dc4i-about-data {display:grid;grid-template-columns:1fr 1fr;gap:9px 12px;line-height:1.2;}
#quick .dc4i-about-data>div {min-width:0;display:block;padding:10px 15px;border-radius:12px;background:rgba(32,68,120,.35);margin:0;}
#quick .dc4i-about-data span {display:block;width:auto;color:#acc4e8;font-size:17px;margin-bottom:5px;font-weight:500;}
#quick .dc4i-about-data strong {display:block;text-align:left;color:#f0f6ff;font-size:22px;font-weight:600;overflow-wrap:break-word;white-space:normal;}
#quick .dc4i-about-data .dc4i-about-developer {grid-column:1/-1;display:flex;gap:15px;align-items:baseline;justify-content:space-between;}
#quick .dc4i-about-data .dc4i-about-developer span {font-size:18px;flex:0 0 104px;margin:0;}
#quick .dc4i-about-data .dc4i-about-developer strong {font-size:22px;text-align:right;}
#quick .dc4i-quick-links.qrow {display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:10px 0 10px;}
#quick .dc4i-quick-links>a {min-width:0;display:flex;align-items:center;justify-content:space-between;gap:10px;padding:11px 16px;border-radius:12px;text-decoration:none;color:#a8dcff;background:rgba(32,68,120,.34);border:1px solid rgba(89,151,217,.25);}
#quick .dc4i-quick-links>a span {font-size:18px;color:#c2d3ed;}
#quick .dc4i-quick-links>a b {font-size:22px;font-weight:650;white-space:nowrap;color:#b5e9ff;}
#quick .dc4i-quick-links>a.focus, #quick .dc4i-about-logo.focus {outline:3px solid #b4f34c;background:rgba(180,243,76,.12);border-radius:12px;}
#quick .dc4i-dedication {text-align:left;margin:0;padding:14px 22px 13px;border:1px solid rgba(233,169,214,.28);border-radius:18px;background:linear-gradient(126deg,rgba(77,46,111,.24),rgba(37,25,78,.16) 75%);}
#quick .dc4i-dedication h3 {margin:0 0 10px;font-size:28px;line-height:1.18;letter-spacing:-.2px;font-weight:750;color:#ffe4f1;text-align:left;}
#quick .dc4i-dedication p {margin:7px 0;font-size:22px;line-height:1.34;color:#f1ecf7;font-weight:430;}
#quick .dc4i-dedication .dc4i-verse {border-left:3px solid rgba(242,158,208,.7);padding-left:17px;margin:12px 0 10px;}
#quick .dc4i-dedication .dc4i-verse p {font-style:italic;color:#f8e4f0;margin:7px 0;}
#quick .dc4i-dedication .dc4i-signature {font-weight:750;color:#ffd3e9;font-size:24px;text-align:right;margin-top:13px;}
#quick .dc4i-dedication small {display:block;text-align:right;color:#c2b6d7;font-size:17px;margin-top:4px;}
@media (max-width:1100px), (max-height:790px) {
  #qpanel {width:min(900px,calc(100vw - 35px));right:10px;top:10px;bottom:10px;}
  #quick {padding:17px 21px;}
  #quick .dc4i-dedication p {font-size:21px;}
}
"""
css_path.write_text(css,encoding="utf-8")

app_path = APP/"app.js"
script = app_path.read_text(encoding="utf-8")
old_nav="nav = all('#quick .qrow').map(function (r) { return [].slice.call(r.querySelectorAll('.f')); });"
old_logo="\n      nav.push(all('#quick .dc4i-about-logo.f'));"
new_nav="""nav = all('#quick .qrow, #quick .dc4i-about-logo')
        .filter(function(el){return el.getClientRects().length>0;})
        .map(function(el){
          if(el.classList.contains('qrow'))
            return [].slice.call(el.querySelectorAll('.f')).filter(function(x){return x.getClientRects().length>0;});
          return [el];
        });"""
if new_nav not in script:
    assert script.count(old_nav)==1, 'Quick navigation selector changed'
    script=script.replace(old_nav+old_logo,new_nav) if old_nav+old_logo in script else script.replace(old_nav,new_nav)
# Keyboard focus is in document order, hidden root-only rows are skipped.
if "function refreshLatestQuick()" not in script:
    anchor="  function refreshQuick() {"
    assert script.count(anchor)==1
    script=script.replace(anchor, "  "+"// Public Homebrew catalog is the source of truth for the latest published version.\n  function refreshLatestQuick() {\n    var target=$('dc4i-latest-version');\n    if (!target) return;\n    target.textContent='Sprawdzanie...';\n    fetch('https://lg.darc.dev/api/apps.json', {cache:'no-store'})\n      .then(function(res){if(!res.ok)throw Error('catalog '+res.status);return res.json();})\n      .then(function(data){\n        var catalog=data.packages||[];\n        var found=catalog.filter(function(p){return p.id==='com.dc4i.vodtv';})[0];\n        var manifest=found&&(found.manifest||{});\n        var latest=manifest.version || (found&&found.version);\n        var published=(manifest.published_at||manifest.releaseDate||'');\n        target.textContent=latest ? latest + (published ? ' · '+String(published).slice(0,10) : ' · online') : 'Brak danych';\n      })\n      .catch(function(){target.textContent='Brak połączenia';});\n  }\n  " + anchor, 1)
    qtime="    setText('qtime', $('clock').textContent + (S.clock24 ? '' : d.getHours() < 12 ? ' AM' : ' PM'));"
    assert script.count(qtime)==1
    script=script.replace(qtime, qtime+"\n    refreshLatestQuick();",1)
app_path.write_text(script, encoding="utf-8")

meta=APP/'appinfo.json'
obj=json.loads(meta.read_text(encoding='utf-8'))
obj['version']='1.2.11'
meta.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding='utf-8')
print("DESIGN_V1211_APPLIED",obj['version'])
