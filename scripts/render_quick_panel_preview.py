#!/usr/bin/env python3
"""Standalone visual QA preview of current production panel markup and CSS."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
dir=R/'build/dc4i-vodtv'
original=(dir/'index.html').read_text(encoding='utf-8')
start=original.index('<div id="qdim"')
end=original.index('<div id="sdim"',start)
panel=original[start:end].replace('<div id="qdim" hidden>', '<div id="qdim">').replace('<div id="qpanel" hidden>', '<div id="qpanel">')
page='''<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="style.css"><link rel="stylesheet" href="dc4i.css">
<style>
body {background:linear-gradient(145deg,#102346,#060f22);font-family:Arial,sans-serif;overflow:hidden}
.fake-label {position:absolute;left:75px;top:105px;font-size:25px;color:#d4e8ff}
.fake-title {position:absolute;left:75px;top:150px;font-size:70px;color:#fff;font-weight:700}
.fake-text {position:absolute;left:75px;top:255px;font-size:24px;color:#c0d2ed;line-height:1.5;max-width:740px}
#qpanel,#qdim {display:block!important}</style></head><body>
<div class="fake-label">POLECANE DLA CIEBIE</div><div class="fake-title">DC4i VODTV</div>
<div class="fake-text">Przeglądaj filmy, seriale i kanały telewizyjne. Szybkie ustawienia i informacje o aplikacji.</div>
'''+panel+'''
<pre id="metrics" style="display:none"></pre>
<script>
document.querySelector('#qdate').textContent='niedz., 25 paź';
document.querySelector('#qtime').textContent='08:47';
document.querySelector('#qaudio').textContent='HDMI ARC';
document.querySelector('#qbt').textContent='Wyłącz';
document.querySelector('#qvol').textContent='24';
document.querySelector('#qpanel [data-q="audio"]').classList.add('focus');
function metrics(){
 const p=document.querySelector('#qpanel'),q=document.querySelector('#quick');
 let sels=['.qhead','.dc4i-about-heading','.dc4i-about-data','.dc4i-quick-links','.dc4i-dedication','.dc4i-dedication small'];
 let items={};
 sels.forEach(s=>{const e=q.querySelector(s);if(!e)return;const r=e.getBoundingClientRect();items[s]={top:Math.round(r.top),bottom:Math.round(r.bottom),height:Math.round(r.height)}});
 return {pwidth:p.getBoundingClientRect().width,pheight:p.getBoundingClientRect().height,scrollH:q.scrollHeight,clientH:q.clientHeight,scrollNeeded:q.scrollHeight>q.clientHeight,items};
}
window.addEventListener('load',()=>{document.querySelector('#metrics').textContent=JSON.stringify(metrics())});
</script></body></html>'''
output=dir/'preview-quick-panel.html'
output.write_text(page,encoding='utf-8')
print('PREVIEW_SOURCE',output,output.stat().st_size)
