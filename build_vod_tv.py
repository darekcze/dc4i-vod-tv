#!/usr/bin/env python3
"""DC4I VOD TV branded release layer, based on pinned local TheBoringTV fork."""
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw,ImageFont,ImageFilter
import json,subprocess,sys,shutil,re
R=Path(__file__).resolve().parent
ART=R/'assets/brand/DC4I_Official_Circuit_Profile_2026-10-24.png'
assert ART.exists(),'Missing canonical approved logo. See DC4I-BRAND-001 in Notion.'
assert __import__('hashlib').sha256(ART.read_bytes()).hexdigest()=='3f8624833ca1eb1609bb42013bfc703d185b59207778afab6802a0723a5e8771'
subprocess.run([sys.executable,str(R/'build_dc4i.py')],check=True)
APP=R/'build/dc4i-vodtv'; SRC=R/'src'
VERSION='1.2.4'; TITLE='DC4I VOD TV'
def patch(path,before,after,required=True):
    p=APP/path;s=p.read_text(encoding='utf-8')
    if required and before not in s:raise ValueError('Pattern missing '+str(path)+' => '+before[:70])
    p.write_text(s.replace(before,after),encoding='utf-8')
# Breaking rebrand authorized by owner: new com.dc4i.vodtv installs separately, replacing the old app manually.
appinfo=json.loads((APP/'appinfo.json').read_text())
appinfo.update({'title':TITLE,'version':VERSION,'vendor':'DC4I','bgColor':'#071638'})
(APP/'appinfo.json').write_text(json.dumps(appinfo,indent=2,ensure_ascii=False)+'\n')
# Settings - genuine UI language is independent of recommendations language.
js=APP/'app.js';s=js.read_text()
s=s.replace("var S = {region: C.REGION, langs: []", "var S = {region: C.REGION, uiLang: 'pl', weatherCity: 'Warsaw', langs: []")
s=s.replace("Object.assign(S, store('settings') || {});","Object.assign(S, store('settings') || {});\n  C.LANG = (S.uiLang === 'en' ? 'en-US' : 'pl-PL');")
s=s.replace("var draft, dirty;", "SROWS.unshift({key: 'uiLang', title: 'Język interfejsu', hint: 'Wybierz język ekranów i opisów TMDB', opts: [['pl','Polski'],['en','English']]});\n  var draft, dirty;")
# Replace original Asia weather presets with European capitals, US capital and large US cities.
cities=[
 ('auto','Automatycznie'),('Warsaw','Warszawa'),('Krakow','Kraków'),('Gdansk','Gdańsk'),
 ('Berlin','Berlin'),('Paris','Paryż'),('London','Londyn'),('Rome','Rzym'),
 ('Madrid','Madryt'),('Lisbon','Lizbona'),('Prague','Praga'),('Vienna','Wiedeń'),
 ('Budapest','Budapeszt'),('Amsterdam','Amsterdam'),('Brussels','Bruksela'),
 ('Copenhagen','Kopenhaga'),('Oslo','Oslo'),('Stockholm','Sztokholm'),
 ('Helsinki','Helsinki'),('Dublin','Dublin'),('Athens','Ateny'),
 ('Bucharest','Bukareszt'),('Sofia','Sofia'),('Bratislava','Bratysława'),
 ('Ljubljana','Lublana'),('Zagreb','Zagrzeb'),('Vilnius','Wilno'),
 ('Riga','Ryga'),('Tallinn','Tallin'),('Bern','Berno'),
 ('Washington','Waszyngton DC'),('New York','Nowy Jork'),
 ('Los Angeles','Los Angeles'),('San Francisco','San Francisco'),
 ('Chicago','Chicago'),('Boston','Boston'),('Seattle','Seattle'),
 ('Miami','Miami'),('Austin','Austin'),('Denver','Denver'),('Sacramento','Sacramento'),
 ('off','Wyłącz')
]
first=s.index("    {key: 'weatherCity',")
last=s.index("    {key: 'unhide',",first)
opts=', '.join('['+json.dumps(v,ensure_ascii=False)+','+json.dumps(label,ensure_ascii=False)+']' for v,label in cities)
new="    {key: 'weatherCity', title: 'Miasto pogody', hint: 'Stolice Europy, Polska i miasta USA', opts: ["+opts+"]},\n"
s=s[:first]+new+s[last:]
# Language-dependent calendar formatting and Polish weather.
s=s.replace("d.toLocaleDateString('en-US'", "d.toLocaleDateString(S.uiLang === 'en' ? 'en-US' : 'pl-PL'")
s=s.replace("new Date(d.time[j] + 'T12:00').toLocaleDateString('en-US'", "new Date(d.time[j] + 'T12:00').toLocaleDateString(S.uiLang === 'en' ? 'en-US' : 'pl-PL'")
# The location label returned by geocoding is in English, while source city names are preserved for API accuracy.
js.write_text(s.replace('DC4I BoringTV','DC4I VOD TV'),encoding='utf-8')
# White/navy/cyan corporate identity. Use the EXACT supplied glyph: normal resized derivatives only.
official=Image.open(ART).convert('RGB')
mask=ImageOps.invert(official.convert('L')).point(lambda v:255 if v>45 else 0)
bounds=mask.getbbox()
assert bounds and bounds[2]-bounds[0]>250,'Unexpected canonical logo geometry'
glyph=official.crop((max(0,bounds[0]-9),max(0,bounds[1]-9),min(official.width,bounds[2]+9),min(official.height,bounds[3]+9)))
def fnt(n,bold=True):
    for p in (['/System/Library/Fonts/Supplemental/Arial Bold.ttf',
               '/System/Library/Fonts/Supplemental/Arial.ttf'] if bold
            else ['/System/Library/Fonts/Supplemental/Arial.ttf']):
        if Path(p).exists():return ImageFont.truetype(p,n)
    return ImageFont.load_default()
def gradient(size):
    w,h=size;im=Image.new('RGBA',(w,h));d=ImageDraw.Draw(im)
    for y in range(h):
        q=y/max(1,h-1)
        d.line((0,y,w,y),fill=(int(7-4*q),int(22-12*q),int(56-32*q),255))
    a=Image.new('RGBA',(w,h),(0,0,0,0));g=ImageDraw.Draw(a)
    g.ellipse((int(w*.48),-int(h*.45),int(w*1.15),int(h*.7)), fill=(36,87,230,110))
    g.ellipse((-int(w*.36),int(h*.57),int(w*.52),int(h*1.4)),fill=(20,122,103,65))
    return Image.alpha_composite(im,a.filter(ImageFilter.GaussianBlur(max(10,w//17))))
def paste_glyph(im,rect):
    x,y,w,h=rect;v=glyph.copy();scale=min(w/v.width,h/v.height);v=v.resize((int(v.width*scale),int(v.height*scale)),Image.Resampling.LANCZOS)
    im.alpha_composite(v.convert('RGBA'),(x+(w-v.width)//2,y+(h-v.height)//2))
def text_center(d,label,mid,y,size,color):
    font=fnt(size);b=d.textbbox((0,0),label,font=font)
    d.text((int(mid-(b[2]-b[0])/2),y),label,font=font,fill=color)
icon=gradient((1024,1024)); d=ImageDraw.Draw(icon)
d.rounded_rectangle((55,45,969,760),radius=130,fill=(251,253,255,255),outline=(92,161,250,255),width=8)
paste_glyph(icon,(105,160,814,465))
d.rounded_rectangle((55,790,969,972),radius=65,fill=(20,39,88,255),outline=(109,199,249,255),width=5)
text_center(d,'VOD TV',512,806,124,(239,250,255,255))
d.line((270,963,754,963),fill=(123,214,205,255),width=5)
icon.convert('RGB').resize((80,80),Image.Resampling.LANCZOS).save(APP/'icon.png')
icon.convert('RGB').resize((130,130),Image.Resampling.LANCZOS).save(APP/'largeIcon.png')
icon.save(R/'assets/brand/dc4i-vod-tv-icon-1024.png',optimize=True)
splash=gradient((1920,1080));d=ImageDraw.Draw(splash)
d.rounded_rectangle((420,115,1500,730),radius=128,fill=(251,253,255,255),outline=(98,161,255,255),width=5)
paste_glyph(splash,(510,190,900,465))
text_center(d,'DC4I VOD TV',960,790,106,(237,246,255,255))
text_center(d,'ODKRYWAJ  •  OCENIAJ  •  OGLĄDAJ',960,935,33,(123,219,209,255))
splash.convert('RGB').save(APP/'splash.png',optimize=True)
splash.resize((960,540),Image.Resampling.LANCZOS).save(R/'assets/brand/dc4i-vod-tv-splash-preview.png')
# Header wordmark: preserve the geometry, change only ink navy->white for contrast.
white=Image.new('RGBA',glyph.size,(255,255,255,0))
opacity=ImageOps.invert(glyph.convert('L')).point(lambda v:max(0,min(255,int(v*1.35))))
white.putalpha(opacity)
white.thumbnail((300,135),Image.Resampling.LANCZOS)
brand=Image.new('RGBA',(480,160),(0,0,0,0))
brand.alpha_composite(white,((480-white.width)//2,0))
d=ImageDraw.Draw(brand)
text_center(d,'VOD TV',240,120,31,(125,239,215,255))
brand.save(APP/'dc4i-wordmark.png')
# Presentation and UI behavior
for name in ['index.html','dc4i.css','features/profiles.js','features/ambient.js']:
    p=APP/name
    if p.exists():
        p.write_text(p.read_text(encoding='utf-8').replace('DC4I BoringTV',TITLE).replace('BORINGTV','VOD TV'),encoding='utf-8')
html=(APP/'index.html').read_text()
html=html.replace('<script src="features/ambient.js"></script>',
 '''<script src="features/ambient.js"></script>
<script src="vod-root.js"></script>
<script src="vod-i18n.js"></script>''')
html=html.replace('<link rel="stylesheet" href="dc4i.css">',
 '''<link rel="stylesheet" href="dc4i.css">
<link rel="stylesheet" href="vod-root.css">''')
html=html.replace('<div class="qrow qvol"><span class="tile f vbtn" data-q="bldown">',
                  '<div class="qrow qvol dc4i-root-only"><span class="tile f vbtn" data-q="bldown">')
html=html.replace('<div class="qrow"><span class="tile f" data-q="picture">',
                  '<div class="qrow dc4i-root-only"><span class="tile f" data-q="picture">')
(APP/'index.html').write_text(html.replace('TV Home',TITLE),encoding='utf-8')
for f in ['vod-root.js','vod-i18n.js','vod-root.css']:shutil.copy2(SRC/f,APP/f)
# Replace root-related error text in developer-only code with safe fallbacks. UI remains hidden on non-root.
(APP/'DC4I-FORK-NOTES.md').write_text(
 '# DC4I VOD TV '+VERSION+'\nCorporate source: assets/brand/DC4I_Official_Circuit_Profile_2026-10-24.png\n'
 'Upstream: theboringhumane/theboringtv-lgwebos pinned at 8cdea8940355685a82aac127fcdcf113a30684f6.\n'
 'App ID com.dc4i.vodtv; uninstall legacy com.dc4i.boringtv before installing new app.\nUI languages PL/EN. Default PL. Root-only controls hidden for unrooted TVs.\n'
 'YouTube Trending requires a verified Google API integration; without one it remains optional.\n',encoding='utf-8')
print('DC4I_VOD_TV_BUILD_READY',TITLE,VERSION,appinfo['id'],'LOGO_SHA256_OK',True)
print('WEATHER_CITIES',len(cities)-2,'LANG_CHOICES','PL EN')

# DC4I VOD TV patch layer for regional availability, weather and app launchers.
subprocess.run([sys.executable, str(R/'scripts/patch_v111.py')], check=True)

# Final user-approved neon graphics and technical app identity for the 1.2.0 release.
subprocess.run([sys.executable,str(R/'scripts/neon_brand_v120.py')],check=True)

# Improve Smarters detection and selected-title handoff without changing the webOS package ID.
subprocess.run([sys.executable,str(R/'scripts/patch_v122.py')],check=True)
