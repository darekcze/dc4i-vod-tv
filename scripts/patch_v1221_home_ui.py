#!/usr/bin/env python3
"""Home draft wiring; preserves profile storage and production version."""
from pathlib import Path
import shutil
R=Path(__file__).resolve().parents[1];A=R/'build/dc4i-vodtv'
for name in ('vod-home-rails.js','vod-home-ui.js'):
    shutil.copy2(R/'src'/name,A/name)
p=A/'index.html';s=p.read_text();anchor='<script src="vod-personalization-ui.js"></script>'
assert s.count(anchor)==1
p.write_text(s.replace(anchor,anchor+'\n<script src="vod-home-rails.js"></script>\n<script src="vod-home-ui.js"></script>'))
p=A/'app.js';s=p.read_text()
def replace(old,new):
    global s
    assert s.count(old)==1,('Home anchor changed',old[:70],s.count(old))
    s=s.replace(old,new,1)
replace('var rowsData = [], heroItems = [], base = [], rowProviders = [];', 'var rowsData = [], heroItems = [], base = [], rowProviders = [], homeFetchedAt=0;')
replace('heroItems = cached.hero; base = cached.base;', 'heroItems = cached.hero; base = cached.base;homeFetchedAt=Number.isSafeInteger(cached.fetchedAt)?cached.fetchedAt:0;')
replace('  function buildRows() {','  function buildRows() {\n    var homeFocus=window.TV&&TV.homeRails&&TV.view()==="home"?TV.homeRails.captureFocus():null;\n    var home=window.TV && TV.homeRails?TV.homeRails.rows():[];')
replace('rowsData = personalized.concat(', 'rowsData = home.concat(personalized,')
replace('    if (base.length) render();',"    if(base.length||home.length){$('hero').hidden=!heroItems.length;render();if(homeFocus)TV.homeRails.restoreFocus(homeFocus);if(home.length)booted();}")
replace('    refresh: function () { buildRows(); },', '    refresh: function () { buildRows(); },\n    focusHomeCard:focusEl,')
replace('  function card(it) {','  function card(it) {\n    if(it.homeRail && TV.homeRails)return TV.homeRails.card(it);')
replace("    if (row.key === 'recoClearHistory') {", "    if(row.key==='homeRailsLayout'){if(TV.homeRails)TV.homeRails.openSettings();return;}\n    if (row.key === 'recoClearHistory') {")
replace("    homeCandidates: function() {", "    homeCandidatesStamp:function(){return homeFetchedAt;},\n    homeCandidates: function() {")
replace("store('homeCache', {hero: heroItems, base: base});", "homeFetchedAt=Date.now();store('homeCache', {hero: heroItems, base: base,fetchedAt:homeFetchedAt});")
replace("nav = [top, [$('heroBtn')]].concat", "nav = [top].concat(heroItems.length?[[$('heroBtn')]]:[]).concat")
replace("onHero = view === 'home' && pos.r === 1", "onHero = view === 'home' && heroItems.length>0 && pos.r === 1")
replace("if (view === 'home' && pos.r === 1) stepHero", "if (view === 'home' && heroItems.length>0 && pos.r === 1) stepHero")
replace('function stepHero(d) { heroIdx', 'function stepHero(d) { if(!heroItems.length)return; heroIdx')
p.write_text(s)
p=A/'dc4i.css';p.write_text(p.read_text()+'''
/* Existing Home card rhythm; metadata cache has no invented artwork. */
.home-rail-card .pic{background:#132d52;position:relative;min-height:160px;}
.home-rail-card .ttl{z-index:1;}
.home-layout{position:fixed;inset:110px 0 0;padding:32px 60px;background:#071638;z-index:30;overflow:auto;color:#eef5ff;}
.home-layout[hidden]{display:none!important;}
.home-layout-row{padding:14px;margin:5px 0;background:#152d50;font-size:23px;border-radius:9px;}
.home-layout-row.focus{outline:4px solid #b4f34c;background:#245180;}
''')
print('HOME_RAILS_UI_READY production version unchanged')
