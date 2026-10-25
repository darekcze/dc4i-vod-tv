#!/usr/bin/env python3
"""Xtream movie/series cover, rating, description, and explicit playback controls."""
from pathlib import Path
A=Path(__file__).resolve().parents[1]/'build/dc4i-vodtv'
p=A/'vod-xtream.js'
s=p.read_text()
def sub(old,new):
 global s
 assert s.count(old)==1,(old[:95],s.count(old))
 s=s.replace(old,new,1)
sub("root.innerHTML=markup;document.body.appendChild(root);","""root.innerHTML=markup;document.body.appendChild(root);
var detailPanel=document.createElement('div');
detailPanel.id='dx-details';
detailPanel.className='dx-details';
detailPanel.hidden=true;
detailPanel.innerHTML='<div class="dx-detail-content">'+
 '<img id="dx-detailposter" alt="" class="dx-detailposter">'+
 '<div class="dx-detailbody"><h2 id="dx-detailtitle"></h2>'+
 '<div id="dx-detailrating" class="dx-detailrating"></div>'+
 '<div id="dx-detailmeta" class="dx-detailmeta"></div>'+
 '<p id="dx-detailplot" class="dx-detailplot"></p>'+
 '<div class="dx-actions"><span class="dx-button f" id="dx-detailplay">▶ Odtwórz</span>'+
 '<span class="dx-button f" id="dx-detailback">Wróć do katalogu</span></div>'+
 '</div></div>';
root.appendChild(detailPanel);
var detailItem=null;""")
sub("function choose(i){","""function showDetails(i) {
 if(!i || i.type==='live')return play(i);
 detailItem=i;
 detailPanel.hidden=false;
 $('detailtitle').textContent=i.title||'';
 $('detailrating').textContent=i.rating?'Ocena Xtream: '+String(i.rating):'Ocena nieznana';
 $('detailmeta').textContent=[i.type==='series'?'Serial':'Film',i.year,i.group].filter(Boolean).join(' · ');
 $('detailplot').textContent=i.plot||'Pobieram opis i informacje o tytule...';
 if(i.icon)$('detailposter').src=i.icon;else $('detailposter').removeAttribute('src');
 var a=account();
 if(a) {
  var action=i.type==='series'?'get_series_info':'get_vod_info';
  var params=i.type==='series'?{series_id:i.id}:{vod_id:i.id};
  request(a,action,params).then(function(d){
   if(detailItem!==i || detailPanel.hidden)return;
   var info=d.info||d;
   $('detailplot').textContent=info.plot||info.description||i.plot||'Opis niedostępny';
   var image=info.movie_image||info.cover_big||info.cover||i.icon;
   if(image)$('detailposter').src=image;
   if(info.rating)$('detailrating').textContent='Ocena Xtream: '+String(info.rating);
   var release=info.releasedate||info.releaseDate||i.year;
   $('detailmeta').textContent=[i.type==='series'?'Serial':'Film',release,info.genre||i.group].filter(Boolean).join(' · ');
   rows();
  },function(){
   if(detailItem===i)$('detailplot').textContent=i.plot||'Opis niedostępny';
  });
 }
 if(i.tmdb && /^\\d+$/.test(String(i.tmdb))) {
  TV.tmdb((i.type==='series'?'tv':'movie')+'/'+i.tmdb).then(function(meta){
   if(detailItem!==i || detailPanel.hidden||!meta)return;
   if(meta.vote_average)$('detailrating').textContent='TMDB: '+Number(meta.vote_average).toFixed(1)+'/10'+
     (i.rating?' · Xtream: '+String(i.rating):'');
   if(meta.overview)$('detailplot').textContent=meta.overview;
   if(!i.icon && meta.poster_path)$('detailposter').src=TV.IMG+'w500'+meta.poster_path;
   rows();
  },function(){});
 }
 rows();
}
function choose(i){""")
sub(" if(i.type==='series')return showEpisodes(i);\n return play(i);",
    " if(i.type==='series'||i.type==='movie')return showDetails(i);\n return play(i);")
sub("function nav(){\n if(playing)return [[$('playerclose')]];",
    "function nav(){\n if(playing)return [[$('playerclose')]];\n if(!detailPanel.hidden)return [[$('detailplay'),$('detailback')]];")
sub("bind('playerclose',stop);","""bind('playerclose',stop);
bind('detailback',function(){detailPanel.hidden=true;detailItem=null;rows();});
bind('detailplay',function(){
 var item=detailItem;
 detailPanel.hidden=true;detailItem=null;
 if(item){if(item.type==='series')showEpisodes(item);else play(item);}
 rows();
});""")
sub(" hide:function(){if(playing)stop();root.hidden=true;},",
    " hide:function(){if(playing)stop();detailPanel.hidden=true;detailItem=null;root.hidden=true;},")
sub(" back:function(){if(playing){stop();return true;}if(!$('form').hidden){form(false);return true;}",
    " back:function(){if(playing){stop();return true;}if(!detailPanel.hidden){detailPanel.hidden=true;detailItem=null;rows();return true;}if(!$('form').hidden){form(false);return true;}")
p.write_text(s)
p=A/'vod-xtream.css'
css=p.read_text()
css+='''\n/* Xtream library poster-led detail card (no early playback). */\n#dc4i-xtream .dx-details{position:fixed;inset:110px 5% 48px;z-index:12;overflow:auto;background:linear-gradient(120deg,#071638,#152952);border:2px solid #4d78ac;border-radius:24px;padding:36px;box-shadow:0 25px 65px #000c;}\n#dc4i-xtream .dx-detail-content{display:flex;gap:38px;align-items:flex-start;}\n#dc4i-xtream .dx-detailposter{width:350px;max-height:620px;object-fit:cover;border-radius:15px;background:#1b315d;flex:0 0 350px;}\n#dc4i-xtream .dx-detailbody{flex:1;}\n#dc4i-xtream .dx-detailbody h2{font-size:42px;line-height:1.1;max-width:960px;margin:10px 0 17px;}\n#dc4i-xtream .dx-detailrating{font-size:26px;color:#ffd17b;margin:12px 0;}\n#dc4i-xtream .dx-detailmeta{font-size:21px;color:#bbd1ee;line-height:1.4;}\n#dc4i-xtream .dx-detailplot{font-size:23px;line-height:1.52;max-width:950px;margin:24px 0 30px;}\n#dc4i-xtream .dx-detailbody .dx-button{font-size:23px;padding:16px 25px;}\n'''
p.write_text(css)
print('XTREAM_DETAIL_VIEW_PATCH_OK')
