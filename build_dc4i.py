#!/usr/bin/env python3
"""Build official-brand DC4I VOD TV fork from locally checked-out upstream.
No credentials in this build script. Its output .ipk embeds the key from ignored keys.js.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import shutil, json, math, re
ROOT = Path(__file__).resolve().parent
SRC = ROOT/'build'/'theboringtv'
APP = ROOT/'build'/'dc4i-vodtv'
ART = ROOT/'branding'/'dc4i-transparent.png'
assert SRC.is_dir() and ART.is_file(), 'Missing source or official branding'
keys = SRC/'keys.js'
assert keys.exists() and re.search(r'[a-f0-9]{32}', keys.read_text(), re.I), 'TMDB key missing'
if APP.exists(): shutil.rmtree(APP)
shutil.copytree(SRC, APP, ignore=shutil.ignore_patterns('.git', '__pycache__','.DS_Store'))
ID='com.dc4i.vodtv'
VER='1.2.2'
def font(size, bold=True):
  paths = ['/System/Library/Fonts/Supplemental/Arial Bold.ttf' if bold else '/System/Library/Fonts/Supplemental/Arial.ttf',
           '/Library/Fonts/Arial Bold.ttf']
  for p in paths:
    if Path(p).exists(): return ImageFont.truetype(p, size)
  return ImageFont.load_default()
def replace(path, old, new, required=True):
  p=APP/path; txt=p.read_text()
  if required and old not in txt: raise RuntimeError('Missing expected pattern in '+str(path)+': '+old[:60])
  p.write_text(txt.replace(old, new), encoding='utf-8')
# Change app identity through dependent files as a standalone install, preserving upstream attribution.
meta=json.loads((APP/'appinfo.json').read_text())
meta.update({'id':ID,'version':VER,'vendor':'DC4I','title':'DC4I VOD TV',
             'appDescription':'Odkrywaj filmy i seriale ze wszystkich serwisów. Spersonalizowane dla Polski.',
             'bgColor':'#071638','iconColor':'#071638'})
(APP/'appinfo.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
for p in APP.rglob('*'):
  if p.is_file() and p.suffix in ('.json','.js','.sh','.md') and p.name not in ('keys.js', 'appinfo.json'):
    try: txt=p.read_text(encoding='utf-8')
    except UnicodeDecodeError: continue
    if 'com.boring.tvhome' in txt: p.write_text(txt.replace('com.boring.tvhome',ID),encoding='utf-8')
# Default Polish services, fall back to regular app launch when native app is unavailable.
cfg=APP/'config.js'; s=cfg.read_text()
s=s.replace("REGION: 'IN'","REGION: 'PL'").replace("LANG: 'en-IN'","LANG: 'pl-PL'").replace("NAME: 'N'","NAME: 'DC4I'")
a=s.index('  SERVICES: ['); b=s.index('  ],',a)+5
services="""  SERVICES: [
    {name: 'Netflix', match: 'netflix', app: 'netflix', jw: 'nfx', on: true},
    {name: 'Prime Video', match: 'amazon prime video', app: 'amazon', jw: 'prv', on: true},
    {name: 'Disney+', match: 'disney plus', app: 'com.disney.disneyplus-prod', jw: 'dnp', on: true},
    {name: 'Max', match: 'max', app: 'com.hbo.hbomax', jw: 'hbm', on: true},
    {name: 'SkyShowtime', match: 'skyshowtime', app: 'com.skyshowtime', jw: 'sst', on: true},
    {name: 'Apple TV+', match: 'apple tv', app: 'com.apple.appletv', jw: 'atp', on: true},
    {name: 'CANAL+', match: 'canal+', app: 'com.canalplus', jw: 'cpl', on: false}
  ],"""
s=s[:a]+services+s[b:]
# Remove duplicate foreign-market apps and keep verified originals where possible.
s='\n'.join(line for line in s.split('\n') if not any(q in line for q in ["id: 'hotstar'","id: 'com.zee5.app'","name: 'JioHotstar'","name: 'ZEE5'"]))
cfg.write_text(s, encoding='utf-8')
# Optional Google credential must not block boot or show broken YouTube feed.
js=APP/'app.js'; s=js.read_text()
s=s.replace("var LANGS = [['hi', 'Hindi']", "var LANGS = [['pl', 'Polski'], ['hi', 'Hindi']")
s=s.replace("var COUNTRIES = [['IN', 'India']", "var COUNTRIES = [['PL', 'Poland'], ['IN', 'India']")
s=s.replace("youtube: true, autoplay: true, clock24: false", "youtube: !!C.YT_KEY, autoplay: true, clock24: true")
s=s.replace("Object.assign(S, store('settings') || {});", "Object.assign(S, store('settings') || {});\n  if (!C.YT_KEY) S.youtube = false;")
s=s.replace("function youtube() {", "function youtube() {\n    if (!C.YT_KEY) return Promise.resolve(null);")
# A key absent is not a boot error; TMDB is preconfigured.
s=s.replace("'Top picks for you'","'Polecane dla Ciebie'")
s=s.replace("'Your apps'","'Twoje aplikacje'")
s=s.replace("'Trending today'","'Trendy dnia'")
s=s.replace("'Popular on '","'Popularne w '")
s=s.replace("'Trending on YouTube'","'Popularne na YouTube'")
s=s.replace("'Waiting for the internet…'","'Łączenie z internetem…'")
s=s.replace("'TV Home'","'DC4I VOD TV'")
# Translate the most visible UI strings, settings and remote-control flows.
app_labels={
 "'Movie' : 'Series'": "'Film' : 'Serial'", "'Clock'": "'Zegar'", "'PL', 'Poland'": "'PL', 'Polska'",
 "'Open in '": "'Otwórz w '",
 "'Where to watch'": "'Gdzie obejrzeć'",
 "'Continue watching'": "'Kontynuuj oglądanie'",
 "'Country'": "'Kraj'",
 "'Where to look up what’s streaming'": "'Dostępność serwisów VOD w wybranym kraju'",
 "'Recommendation languages'": "'Języki rekomendacji'",
 "'Pick any. None = trending in every language'": "'Wybierz języki lub pozostaw puste'",
 "'Your streaming services'": "'Twoje serwisy streamingowe'",
 "'Each gets a “Popular on …” row'": "'Osobny wiersz dla każdego wybranego serwisu'",
 "'Trending on YouTube row'": "'Popularne na YouTube'",
 "'Rotate featured titles'": "'Automatyczna zmiana polecanych filmów'",
 "'Weather city'": "'Miasto pogody'",
 "'Auto finds your city from your internet connection'": "'Automatycznie wykrywaj miasto'",
 "'Hold OK on an app to move or remove it'": "'Przytrzymaj OK, aby przenieść lub ukryć aplikację'",
 "'Show hidden apps'": "'Pokaż ukryte aplikacje'",
 "'Clear history'": "'Wyczyść historię'",
 "'Edit apps'": "'Edytuj aplikacje'",
 "'Done'": "'Gotowe'",
 "'Settings'": "'Ustawienia'",
 "<h2>Settings</h2>": "<h2>Ustawienia</h2>",
 "'Continue watching cleared'": "'Historia oglądania wyczyszczona'",
 "'Could not look up where to watch'": "'Nie udało się sprawdzić dostępności'",
 "'Hidden apps are back'": "'Przywrócono ukryte aplikacje'",
 "'Edit mode: OK on an app to move or remove it'": "'Tryb edycji: OK, aby przenieść lub usunąć'",
 "'On'": "'Włącz'",
 "'Off'": "'Wyłącz'",
 "'12-hour'": "'12 godzin'",
 "'24-hour'": "'24 godziny'",
 "'Open'": "'Otwórz'"
}
for before,after in app_labels.items(): s=s.replace(before,after)
# Polish cities rather than the India-specific weather-city presets.
for oldcity,newcity in [('Mumbai','Warszawa'),('Delhi','Kraków'),('Bengaluru','Wrocław'),
 ('Hyderabad','Gdańsk'),('Chennai','Poznań'),('Kolkata','Łódź'),('Pune','Szczecin'),
 ('Ahmedabad','Lublin'),('Jaipur','Katowice'),('Lucknow','Białystok'),
 ('Chandigarh','Gdynia'),('Kochi','Toruń')]:
 s=s.replace("['"+oldcity+"', '"+oldcity+"']", "['"+newcity+"', '"+newcity+"']")
s=s.replace('  var draft, dirty;', "  if (!C.YT_KEY) SROWS = SROWS.filter(function (row) { return row.key !== 'youtube'; }); var draft, dirty;")
js.write_text(s,encoding='utf-8')
# Strings from the dynamically loaded search and details features.
features_labels={
 'features/search.js': {
  "'Search'": "'Szukaj'",
  "'Search movies & shows'": "'Szukaj filmów i seriali'",
  "'Trending searches'": "'Popularne wyszukiwania'",
  "'Searching…'": "'Wyszukiwanie…'",
  "'Results for “'": "'Wyniki dla „'",
  "'No results for “'": "'Brak wyników dla „'",
  "'Search failed, check the connection'": "'Błąd wyszukiwania, sprawdź internet'",
  "'Checking where to watch…'": "'Sprawdzam dostępność…'",
  "'Not streaming in '": "'Niedostępne w '",
  "'Rent'": "'Wypożycz'",
  "'Buy'": "'Kup'",
  "'Space'": "'Spacja'",
  "'Clear'": "'Wyczyść'",
  "Search YouTube": "Szukaj w YouTube"
 },
 'features/details.js': {
  "'My watchlist'": "'Moja lista'",
  "'Removed from your watchlist'": "'Usunięto z mojej listy'",
  "'Added to your watchlist'": "'Dodano do mojej listy'",
  "'✓ In watchlist'": "'✓ Na liście'",
  "'＋ Watchlist'": "'＋ Do obejrzenia'",
  "'Not on your services'": "'Brak w wybranych serwisach'",
  "'Rent or buy: '": "'Wypożycz lub kup: '",
  "'No streaming info for '": "'Brak informacji o dostępności w '",
  "btn('Trailer',": "btn('Zwiastun',",
  "'More like this'": "'Podobne filmy i seriale'",
  "'Because you viewed '": "'Ponieważ oglądano '",
  "'Could not load details'": "'Nie udało się pobrać szczegółów'",
  "'Cast: '": "'Obsada: '",
  "'▶ Watch on '": "'▶ Oglądaj w '",
  "' season'": "' sezon'",
  "' seasons'": "' sezony'"
 }
}
for file,terms in features_labels.items():
 p=APP/file; t=p.read_text()
 for before,after in terms.items(): t=t.replace(before,after)
 p.write_text(t,encoding='utf-8')
# Official wordmark: use the existing company asset unchanged inside new composition.
logo=Image.open(ART).convert('RGBA')
def background(size):
  w,h=size
  top=(7,22,56); bottom=(3,8,25)
  im=Image.new('RGBA', size); d=ImageDraw.Draw(im)
  for y in range(h):
    t=y/max(1,h-1)
    d.line([(0,y),(w,y)],fill=tuple(int(top[i]*(1-t)+bottom[i]*t) for i in range(3))+(255,))
  light=Image.new('RGBA',size,(0,0,0,0)); g=ImageDraw.Draw(light)
  g.ellipse((int(w*.48),-int(h*.52),int(w*1.17),int(h*.65)),fill=(36,87,230,82))
  g.ellipse((-int(w*.25),int(h*.44),int(w*.47),int(h*1.35)),fill=(20,122,103,67))
  light=light.filter(ImageFilter.GaussianBlur(max(6,int(w*.07))))
  return Image.alpha_composite(im,light)
def logo_paste(im,box):
  x,y,w,h=box
  mark=logo.copy(); mark.thumbnail((w,h),Image.Resampling.LANCZOS)
  im.alpha_composite(mark,(x+(w-mark.width)//2,y+(h-mark.height)//2))
def write_track(draw, text, center, y, f, fill, space=0):
  widths=[draw.textlength(ch,font=f) for ch in text]
  total=sum(widths)+(len(text)-1)*space
  x=center-total/2
  for ch,v in zip(text,widths):
    draw.text((round(x),y),ch,font=f,fill=fill,stroke_width=0)
    x+=v+space
icon=background((512,512)); d=ImageDraw.Draw(icon)
# Light border and accent line
d.rounded_rectangle((8,8,504,504),radius=86,outline=(122,179,255,95),width=3)
logo_paste(icon,(50,150,412,190))
d.line((90,361,422,361), fill=(164,244,74,230),width=3)
write_track(d,'BORING TV',256,388,font(33), (235,245,255,255),4)
icon.convert('RGB').resize((80,80),Image.Resampling.LANCZOS).save(APP/'icon.png',optimize=True)
icon.convert('RGB').resize((130,130),Image.Resampling.LANCZOS).save(APP/'largeIcon.png',optimize=True)
icon.save(ROOT/'branding'/'dc4i-vodtv-icon-preview.png')
splash=background((1920,1080)); d=ImageDraw.Draw(splash)
logo_paste(splash,(460,280,1000,360))
write_track(d,'VOD TV',960,666,font(94), (236,244,255,255),13)
write_track(d,'ODKRYWAJ. OCENIAJ. OGLĄDAJ.',960,797,font(27), (164,191,229,255),4)
d.line((755,865,1165,865),fill=(177,245,72,180),width=4)
splash.convert('RGB').save(APP/'splash.png', optimize=True)
splash.resize((960,540),Image.Resampling.LANCZOS).save(ROOT/'branding'/'dc4i-vodtv-splash-preview.png')
wordmark=logo.copy()
wordmark.thumbnail((480,190),Image.Resampling.LANCZOS)
wordmark.save(APP/'dc4i-wordmark.png',optimize=True)
# Brand navigation and boot.
html=APP/'index.html'; s=html.read_text()
s=s.replace('<title>TV Home</title>','<title>DC4I VOD TV</title>')
s=s.replace('</style>\n</head>','</style>\n<link rel="stylesheet" href="dc4i.css">\n</head>')
s=s.replace('<img src="icon.svg" alt="">','<img class="dc4i-bootlogo" src="dc4i-wordmark.png" alt="DC4I"><div class="dc4i-bootname">VOD TV</div>')
s=s.replace('Getting your shows ready…','Przygotowujemy Twoje rekomendacje…')
s=s.replace('<header id="top">','<header id="top">\n  <div class="dc4i-brand"><img src="dc4i-wordmark.png" alt="DC4I"><small>VOD TV</small></div>')
for old,new in [('For you','Dla Ciebie'),('Live</span>','Na żywo</span>'),('Apps</span>','Aplikacje</span>'),('>Open</span>','>Otwórz</span>'),('Your apps</h2>','Twoje aplikacje</h2>'),('TV Home</div>','DC4I VOD TV</div>'),('Screensaver</b>','Wygaszacz</b>'),('Audio output</b>','Wyjście audio</b>'),('Bluetooth</b>','Bluetooth</b>'),('Brightness <b','Jasność <b'),('Volume <b','Głośność <b')]:
  s=s.replace(old,new)
html.write_text(s,encoding='utf-8')
brand_css="""/* DC4I VOD TV | branded UI | dedicated LG webOS app */
html,body { background:#071638; color:#eaf2ff; }
#boot {background:#071638;}
#boot .sw.s1 {background:radial-gradient(circle,rgba(36,87,230,.9),rgba(36,87,230,0) 65%);}
#boot .sw.s2 {background:radial-gradient(circle,rgba(84,56,200,.7),rgba(84,56,200,0) 65%);}
#boot .sw.s3 {background:radial-gradient(circle,rgba(20,122,103,.7),rgba(20,122,103,0) 65%);}
#boot .sw.s4 {background:radial-gradient(circle,rgba(180,243,76,.22),rgba(180,243,76,0) 65%);}
#boot img.dc4i-bootlogo {width:480px;height:auto;max-height:180px;margin-bottom:10px;object-fit:contain;}
.dc4i-bootname {font:600 64px Roboto,Arial,sans-serif;letter-spacing:14px;margin-bottom:60px;color:#eaf2ff;}
#boot .bar {width:300px;background:rgba(102,145,226,.24);}
#boot .bar i {background:#b4f34c;}
#bootmsg {color:#aebfdb;}
#shade {background:linear-gradient(90deg,rgba(7,22,56,.97) 0%,rgba(7,22,56,.79) 34%,rgba(7,22,56,0) 72%),
  linear-gradient(0deg,#071638 18%,rgba(7,22,56,.65) 55%,rgba(7,22,56,0) 80%);}
.scrolled #shade {background:rgba(7,22,56,.91);}
.dc4i-brand {width:182px;min-width:182px;margin-right:28px;display:flex;flex-direction:column;align-items:center;justify-content:center;}
.dc4i-brand img {width:164px;height:55px;object-fit:contain;}
.dc4i-brand small {display:block;margin-top:-4px;letter-spacing:4px;font-size:13px;font-weight:700;color:#b4f34c;}
#top {top:35px;}
.pill {background:rgba(7,22,56,.74);border:1px solid rgba(122,173,255,.18);}
.tab.cur {background:rgba(36,87,230,.57);}
.avatar {background:#2457E6;color:white;}
.card .pic {background:#101e42;}
.card .chip {background:rgba(7,22,56,.85);color:#dbf4ff;}
.card .cap {color:#b4c9e5;}
.focus .pic,.focus .disc {box-shadow:0 0 0 5px #b4f34c,0 15px 40px rgba(0,0,0,.75);}
.tab.focus,.ico.focus,#heroBtn.focus {background:#b4f34c;color:#071638;}
#heroBtn {background:#2457E6;color:white;}
#heroBtn.focus {background:#b4f34c;color:#071638;}
#dots i.on {background:#b4f34c;}
#spanel,#qpanel {background:#0b1c40;}
.chip {background:#1b3260;}
.chip.sel,.chip.focus {background:#b4f34c;color:#071638;}
.tile {background:#18305b;}
.tile.focus,.qbtn.focus,.tip.focus {background:#b4f34c;color:#071638;}
#toast {background:#172d57;color:#fff;border:1px solid rgba(180,243,76,.4);}
.qfoot {color:#b4f34c;font-size:23px;}
"""
(APP/'dc4i.css').write_text(brand_css,encoding='utf-8')
(APP/'DC4I-FORK-NOTES.md').write_text(
  "# DC4I VOD TV v1.0.0\n\nCustomized from theboringhumane/theboringtv-lgwebos (source attribution retained).\n"
  "Official DC4I wordmark from darekcze/dcai-website (public/brand/dc4i-transparent.png).\n"
  "Region Poland, Polish-first UI, TMDB included in packaged keys.js.\n"
  "YouTube Data API is optional and disabled if key missing.\n"
  "Built .ipk embeds TMDB client key; redistributing reveals that key.\n",encoding='utf-8')
print('DC4I_SOURCE_READY',ID,VER)
print('ARTWORK',[(x.name,x.stat().st_size) for x in [APP/'icon.png',APP/'largeIcon.png',APP/'splash.png',APP/'dc4i-wordmark.png']])
print('TMDB_PRESENT',True, 'YOUTUBE_OPTIONAL', True)
