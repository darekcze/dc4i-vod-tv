#!/usr/bin/env python3
"""DC4I VOD TV 1.2.0 identity and user-approved neon branding.
Takes build/dc4i-vodtv from pinned build_vod_tv.py and only modifies generated files.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import hashlib, json, math
ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'build/dc4i-vodtv'
ASSET=ROOT/'assets/brand/DC4I_VOD_TV_Neon_Approved_2026-10-24.png'
WEBP=ROOT/'assets/brand/DC4I_VOD_TV_Neon_Approved_2026-10-24.webp'
EXPECTED='fe7aa367fb1b4f83593a5a647f4dc4a7693ec0888c8e8a046cec02667781f840'
assert hashlib.sha256(WEBP.read_bytes()).hexdigest()==EXPECTED, 'The approved neon image must not be replaced!'
src=Image.open(ASSET).convert('RGB')
assert src.size==(1024,1024),f'unexpected neon image shape: {src.size}'
data=json.loads((APP/'appinfo.json').read_text(encoding='utf-8'))
data.update({'id':'com.dc4i.vodtv','version':'1.2.4','title':'DC4I VOD TV','vendor':'DC4I'})
(APP/'appinfo.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# Preserve the exact neon visual generated earlier in this conversation for icon and installation.
src.resize((80,80),Image.Resampling.LANCZOS).save(APP/'icon.png',optimize=True)
src.resize((130,130),Image.Resampling.LANCZOS).save(APP/'largeIcon.png',optimize=True)
src.save(APP/'neon-app-logo.png',optimize=True)
# TV splash: floating neon graphic, deep navy backdrop and a restrained caption.
W,H=1920,1080
canvas=Image.new('RGB',(W,H))
pixels=canvas.load()
for y in range(H):
    t=y/(H-1)
    rr=int(3+4*(1-t));gg=int(10+12*(1-t));bb=int(30+36*(1-t))
    for x in range(W): pixels[x,y]=(rr,gg,bb)
glow=Image.new('RGBA',(W,H),(0,0,0,0))
g=ImageDraw.Draw(glow)
g.ellipse((420,55,1500,1020),fill=(36,120,238,75))
glow=glow.filter(ImageFilter.GaussianBlur(140))
canvas=Image.alpha_composite(canvas.convert('RGBA'),glow)
logo=src.resize((780,780),Image.Resampling.LANCZOS).convert('RGBA')
canvas.alpha_composite(logo,((W-logo.width)//2,75))
font=None
for path in ['/System/Library/Fonts/Supplemental/Arial Bold.ttf','/System/Library/Fonts/Supplemental/Arial.ttf']:
    if Path(path).exists():font=ImageFont.truetype(path,33);break
if font:
    label='ODKRYWAJ   ·   OCENIAJ   ·   OGLĄDAJ'
    d=ImageDraw.Draw(canvas)
    box=d.textbbox((0,0),label,font=font)
    d.text(((W-(box[2]-box[0]))//2,933),label,font=font,fill=(176,228,246,255))
canvas.convert('RGB').save(APP/'splash.png',optimize=True)
canvas.resize((960,540),Image.Resampling.LANCZOS).save(ROOT/'assets/brand/DC4I_VOD_TV_Neon_Splash_Preview.png',optimize=True)
# Compact neon brand that remains legible at 1080p in the app header.
brand=Image.new('RGBA',(500,140),(7,22,56,255))
mono=src.crop((130,180,923,633)).resize((208,132),Image.Resampling.LANCZOS).convert('RGBA')
brand.alpha_composite(mono,(6,4))
d=ImageDraw.Draw(brand)
for y in range(24,108):
    t=(y-24)/84
    color=(int(226-110*t),int(250-10*t),int(255-26*t),255)
    d.line((222,y,230,y),fill=color,width=3)
f=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf',62) if Path('/System/Library/Fonts/Supplemental/Arial Bold.ttf').exists() else ImageFont.load_default()
d.text((245,31),'VOD TV',font=f,fill=(210,243,255,255))
d.line((242,116,484,116),fill=(57,225,222,255),width=4)
brand.save(APP/'dc4i-wordmark.png',optimize=True)
# Update visible UI references, including boot branding. Avoid a duplicate "VOD TV" label.
index=APP/'index.html'
html=index.read_text(encoding='utf-8')
html=html.replace('<img class="dc4i-bootlogo" src="dc4i-wordmark.png" alt="DC4I"><div class="dc4i-bootname">VOD TV</div>',
                  '<img class="dc4i-neon-boot" src="neon-app-logo.png" alt="DC4I VOD TV">')
html=html.replace('<small>VOD TV</small></div>','</div>')
html=html.replace('DC4I BoringTV','DC4I VOD TV')
index.write_text(html,encoding='utf-8')
css=APP/'dc4i.css'
s=css.read_text(encoding='utf-8')
s+='''\n/* DC4I VOD TV neon product identity (replaces old corporate text wordmark). */
#boot img.dc4i-neon-boot {width:420px;height:420px;margin:0 0 26px;object-fit:contain;border-radius:60px;box-shadow:0 15px 80px rgba(0,120,255,.24);}
#top .dc4i-brand {min-width:180px;width:180px;margin-right:26px;display:flex;align-items:center;justify-content:center;}
#top .dc4i-brand img {width:182px;height:auto;max-height:70px;object-fit:contain;}
#top .dc4i-brand small {display:none;}
'''
css.write_text(s,encoding='utf-8')
# Ensure no executable app file still exposes the previous technical package id.
old='com.dc4i.boringtv'
touched=[]
for file in APP.rglob('*'):
    if not file.is_file() or file.suffix not in {'.js','.json','.html','.css','.md'}:
        continue
    if file.name=='keys.js': continue
    text=file.read_text(encoding='utf-8')
    if old in text:
        file.write_text(text.replace(old,'com.dc4i.vodtv'),encoding='utf-8')
        touched.append(str(file.relative_to(APP)))
print('NEON_BRAND_V120_READY',data['id'],data['version'],'neon_sha256',EXPECTED,'old_id_references_replaced',touched)
print('ICON_BYTES',(APP/'icon.png').stat().st_size,'SPLASH_BYTES',(APP/'splash.png').stat().st_size)
