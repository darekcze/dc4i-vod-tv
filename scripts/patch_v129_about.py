from pathlib import Path
import json,re
root=Path(__file__).resolve().parents[1]/'build/dc4i-vodtv'
html=root/'index.html';s=html.read_text()
for q in ('screensaver','wifi','a11y'):
 s,n=re.subn(r'<span class="tile f" data-q="'+q+r'">.*?</span></span>', '',s,count=1,flags=re.S)
 assert n==1,q
s,n=re.subn(r'<div class="qrow qinputs" id="qinputs"></div>\s*<div class="qfoot">DC4I VOD TV</div>', '''<section class="dc4i-about" aria-label="O aplikacji">
    <div class="dc4i-about-brand"><span class="f dc4i-about-logo" data-q="logo" title="DC4i Labs"><img src="icon.png" alt="DC4i VODTV"></span>
      <div><b>DC4i VODTV</b><small>DC4i Labs · LG webOS</small></div></div>
    <div class="dc4i-about-data">
      <div><span>App Version</span><strong id="dc4i-app-version">1.2.10 · 25.10.2026</strong></div>
      <div><span>Latest Version</span><strong id="dc4i-latest-version">Sprawdzanie...</strong></div>
      <div><span>App repo</span><a class="f" data-q="repo" href="https://lg.darc.dev">lg.darc.dev ↗</a></div>
      <div><span>Developer</span><strong>Dariusz Czechowicz · DC4i Labs</strong></div>
      <div><span>Website</span><a class="f" data-q="website" href="https://www.dc4i.com">dc4i.com ↗</a></div>
    </div>
    <div class="dc4i-dedication">
      <h3>Z dedykacją dla mojej najdroższej Ani i ukochanej rodziny.</h3>
      <p>Mojej miłości, mojemu wsparciu i najpiękniejszej części każdego dnia.</p>
      <p class="dc4i-verse">„Wśród tysięcy historii, które możemy obejrzeć, najpiękniejszą jest ta, którą piszemy razem.</p>
      <p class="dc4i-verse">I gdybym mógł wybierać raz jeszcze, w każdej historii odnalazłbym Was.</p>
      <p class="dc4i-verse">Bo gdzie Wy jesteście, tam jest mój dom. A gdzie jesteśmy razem, tam jest całe moje szczęście.”</p>
      <p class="dc4i-signature">Na zawsze Wasz, Darek.</p>
      <small>Made with love · DC4i Labs · 2026</small>
    </div>
  </section>''',s,count=1)
assert n==1,'about placement'
html.write_text(s)
css=root/'dc4i.css';t=css.read_text()+'''
/* DC4I personalized quick-settings about card. All measurements are webOS 1920x1080 CSS pixels. */
#qpanel {width:690px;}
#quick {display:flex;flex-direction:column;overflow-y:auto;box-sizing:border-box;}
#quick>.qrow {flex-shrink:0;}
.dc4i-about {margin-top:auto;padding:15px 16px 6px;border-top:1px solid rgba(159,183,255,.22);color:#f0f5ff;}
.dc4i-about-brand {display:flex;align-items:center;gap:15px;margin-bottom:12px;}
.dc4i-about-brand img {width:72px;height:72px;object-fit:contain;border-radius:14px;}
.dc4i-about-brand b {font-size:24px;display:block;}
.dc4i-about-brand small {font-size:15px;color:#b8c8ed;}
.dc4i-about-data {font-size:16px;line-height:1.35;}
.dc4i-about-data>div {display:flex;justify-content:space-between;gap:12px;margin:5px 0;}
.dc4i-about-data span {color:#9eb5de;flex:0 0 148px;}
.dc4i-about-data strong {font-weight:500;text-align:right;}
.dc4i-about-data a {color:#a9d9ff;text-decoration:underline;text-underline-offset:3px;text-align:right;}
.dc4i-about-data a.focus,.dc4i-about-logo.focus {color:#071638;background:#b4f34c;outline:3px solid #b4f34c;border-radius:6px;}
.dc4i-dedication {text-align:center;margin-top:14px;padding-top:13px;border-top:1px solid rgba(159,183,255,.22);}
.dc4i-dedication h3 {font-size:22px;color:#f6c8dd;margin:0 0 10px;}
.dc4i-dedication p {font-size:17px;line-height:1.34;margin:8px 0;}
.dc4i-dedication .dc4i-verse {font-style:italic;color:#f6d6e7;}
.dc4i-dedication .dc4i-signature {font-weight:600;color:#f4bed8;}
.dc4i-dedication small {font-size:14px;color:#a9bbd7;}
'''
css.write_text(t)
app=root/'app.js';a=app.read_text()
a=a.replace("setText('qwifi', 'Home Wi-Fi'); ",'')
a=re.sub(r"\s*luna\('com.webos.service.connectionmanager/getStatus'\).*?\}, function \(\) \{ setText\('qwifi', ''\); \}\);",'',a,count=1,flags=re.S)
a=re.sub(r"\s*svc\('getInputs'\).*?\}, function \(\) \{ \$\('qinputs'\).*?\}\);",'',a,count=1,flags=re.S)
a=a.replace("      input: function () { closeQuick(); launch(btn.dataset.id); },",'''      logo: function () { launch('com.webos.app.browser', {target:'https://www.dc4i.com',fullMode:true}); },
      repo: function () { launch('com.webos.app.browser', {target:'https://lg.darc.dev',fullMode:true}); },
      website: function () { launch('com.webos.app.browser', {target:'https://www.dc4i.com',fullMode:true}); },
      input: function () { closeQuick(); launch(btn.dataset.id); },''')
app.write_text(a)
meta=root/'appinfo.json';obj=json.loads(meta.read_text());obj['version']='1.2.10';meta.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
print('ABOUT_PATCH_OK',obj['version'],'dedication + links + logo')
