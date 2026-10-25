/* DC4I VOD TV: independent, on-device Xtream IPTV integration.
   Account records remain in this TV app's user storage, never in the IPK.
   No DC4I cloud, Mac Pro or private LAN dependency.
*/
(function(){
'use strict';
var TV=window.TV;if(!TV)return;
var tr=function(pl,en){return TV.S.uiLang==='en'?en:pl;};
var KEY='dc4iXtreamPlaylistsV1';
var saved=TV.store(KEY)||[];
if(!Array.isArray(saved))saved=[];
var library={}, selected='', records=[], categories=[], query='', filter='all', category='', page=0, LIMIT=60, isLoading=false;
var playing=false, playerFocus=null, lastSearch=0;
var root=document.createElement('main');root.id='dc4i-xtream';root.hidden=true;
var markup=[
'<div class="dx-head"><div><h2>IPTV <strong>Xtream</strong></h2><p>Twoje playlisty, bez serwera pośredniczącego</p></div>',
'<span class="dx-button f" id="dx-config">＋ Dodaj playlistę</span><span class="dx-button f" id="dx-refresh">⟳ Odśwież</span>',
'<span class="dx-button f" id="dx-close">✕ Wróć</span></div>',
'<div id="dx-accounts" class="dx-accounts"></div>',
'<div id="dx-form" class="dx-form" hidden>',
'<h3 id="dx-formtitle">Dodaj Xtream Codes</h3>',
'<label>Nazwa playlisty<input id="dx-name" placeholder="Moja TV" autocomplete="off"></label>',
'<label>Adres serwera<input id="dx-url" placeholder="https://provider.example:8080" autocomplete="off" spellcheck="false"></label>',
'<label>Użytkownik<input id="dx-user" autocomplete="off" spellcheck="false"></label>',
'<label>Hasło<input id="dx-pass" type="password" autocomplete="off" spellcheck="false"></label>',
'<div class="dx-actions"><span class="dx-button f" id="dx-save">Zapisz</span><span class="dx-button f" id="dx-test">Sprawdź połączenie</span>',
'<span class="dx-button f" id="dx-cancel">Anuluj</span></div>',
'<p class="dx-warning">Połączenie HTTP przesyła login i hasło bez szyfrowania. Konfiguracja jest zapisywana lokalnie w pamięci tej aplikacji na telewizorze. Aktualizacja aplikacji może usunąć te dane.</p>',
'</div>',
'<div id="dx-searchbar" class="dx-searchbar"><label>Szukaj w Xtream',
'<input id="dx-query" placeholder="Kanał, grupa, film lub serial" autocomplete="off" /></label>',
'<span class="dx-button f" id="dx-search">Szukaj</span>',
'<label>Rodzaj<select id="dx-type"><option value="all">Wszystko</option><option value="live">Kanały TV</option><option value="group">Grupy TV</option><option value="movie">Filmy</option><option value="series">Seriale</option></select></label>',
'<label>Grupa<select id="dx-category"><option value="">Wszystkie</option></select></label></div>',
'<p id="dx-status" class="dx-status">Dodaj playlistę, aby rozpocząć.</p>',
'<div id="dx-results" class="dx-results"></div><div class="dx-pagination">',
'<span class="dx-button f" id="dx-prev">◀ Poprzednie</span><span id="dx-pagecount"></span><span class="dx-button f" id="dx-next">Następne ▶</span></div>',
'<div id="dx-episodes" class="dx-episodes" hidden><h3 id="dx-episodetitle">Odcinki</h3><div id="dx-episodelist" class="dx-episode-list"></div><span class="dx-button f" id="dx-episodesclose">Wróć do katalogu</span></div>',
'<div id="dx-player" class="dx-player" hidden><video id="dx-video" playsinline preload="none" controls></video>',
'<span class="dx-button f dx-playerclose" id="dx-playerclose">✕ Zamknij odtwarzacz</span><p id="dx-playmsg"></p></div>'
].join('');
root.innerHTML=markup;document.body.appendChild(root);
var $=function(id){return document.getElementById('dx-'+id);};
function msg(pl,en){$('status').textContent=tr(pl,en||pl);}
function norm(v){return String(v||'').toLocaleLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'');}
function hasOwn(o,key){return Object.prototype.hasOwnProperty.call(o,key);}
function saveAccounts(){
 try{TV.store(KEY,saved);return true;}
 catch(e){msg('Nie można zapisać ustawień na telewizorze','Cannot save TV settings');return false;}
}
function cleanUrl(url){
 url=String(url||'').trim().replace(/\/+$/,'');
 if(!/^https?:\/\/[^/\s?#]+$/i.test(url))throw new Error(tr('Wpisz pełny adres http(s)://host:port bez ścieżki.','Enter http(s)://host:port with no path.'));
 return url;
}
function account(){return saved.filter(function(a){return a.id===selected;})[0]||null;}
function clear(el){while(el.firstChild)el.removeChild(el.firstChild);}
function button(label,fn,cls){var e=document.createElement('span');e.className='dx-button f'+(cls?' '+cls:'');e.textContent=label;e.onok=fn;return e;}
function itemRow(item,fn){
 var e=button('',fn,'dx-item'),b=document.createElement('b'),d=document.createElement('small');
 b.textContent=item.title||'Bez nazwy';d.textContent=[{live:'Kanał TV',movie:'Film',series:'Serial',group:'Grupa TV',episode:'Odcinek'}[item.type]||item.type,item.group||''].filter(Boolean).join(' · ');
 e.append(b,d);return e;
}
function rows(){
 if(TV.view()!=='xtream')return;
 TV.rebuild();
}
function redrawAccounts(){
 var host=$('accounts');clear(host);
 saved.forEach(function(a){
  var box=document.createElement('div');box.className='dx-account'+(a.id===selected?' active':'');
  box.appendChild(button((a.id===selected?'✓ ':'')+(a.label||a.host),function(){selected=a.id;redrawAccounts();displayCategories();if(library[selected]){records=library[selected].records;categories=library[selected].categories;runSearch(true);}else sync(false);}));
  box.appendChild(button('Edytuj',function(){editAccount(a);},'dx-small'));
  box.appendChild(button('Usuń',function(){removeAccount(a);},'dx-small dx-delete'));
  host.appendChild(box);
 });
 rows();
}
function form(show){
 $('form').hidden=!show;
 $('searchbar').hidden=show;
 $('results').hidden=show;
 $('episodes').hidden=true;
 $('prev').parentNode.hidden=show;
 rows();
}
var editingId=null;
function editAccount(a){
 editingId=a?a.id:null;
 $('formtitle').textContent=a?'Edytuj playlistę Xtream':'Dodaj playlistę Xtream';
 $('name').value=a?a.label:'';
 $('url').value=a?a.host:'';
 $('user').value=a?a.username:'';
 $('pass').value=a?a.password:'';
 form(true);$('name').focus();
}
function removeAccount(a){
 if(!window.confirm(tr('Usunąć playlistę '+a.label+' z tego telewizora?','Remove playlist '+a.label+' from this TV?')))return;
 saved=saved.filter(function(x){return x.id!==a.id;});
 delete library[a.id];
 if(selected===a.id){selected=saved.length?saved[0].id:'';records=selected&&library[selected]?library[selected].records:[];categories=[];}
 saveAccounts();redrawAccounts();displayCategories();runSearch(true);
}
function fromForm(){
 var label=$('name').value.trim(),host=cleanUrl($('url').value),username=$('user').value.trim(),password=$('pass').value;
 if(!username||!password)throw new Error(tr('Login i hasło są wymagane.','Username and password required.'));
 return {id:editingId||'xt'+Date.now().toString(36),label:label||host.replace(/^https?:\/\//,''),
         host:host,username:username,password:password};
}
function persist(){
 var entry;
 try{entry=fromForm();}catch(e){msg(e.message);return;}
 var old=saved.filter(function(a){return a.id===entry.id;})[0];
 if(old){saved=saved.map(function(a){return a.id===entry.id?entry:a;});delete library[entry.id];}
 else saved.push(entry);
 if(!saveAccounts())return;
 selected=entry.id;records=[];categories=[];
 form(false);redrawAccounts();displayCategories();msg('Playlista zapisana na telewizorze. Wczytuję katalog.','Playlist saved on TV. Loading catalog.');
 sync(false);
}
function request(a,action,extra){
 var qs=new URLSearchParams({username:a.username,password:a.password});
 if(action)qs.set('action',action);
 Object.keys(extra||{}).forEach(function(k){qs.set(k,extra[k]);});
 // Credentials are necessarily sent to the owner's Xtream provider, never to DC4I.
 var url=a.host+'/player_api.php?'+qs.toString();
 var controller=typeof AbortController!=='undefined'?new AbortController():null;
 var timer=controller?setTimeout(function(){controller.abort();},22000):null;
 return fetch(url,{method:'GET',mode:'cors',cache:'no-store',signal:controller?controller.signal:undefined})
 .then(function(response){if(!response.ok)throw new Error('HTTP '+response.status);return response.json();})
 .then(function(json){if(timer)clearTimeout(timer);return json;},function(error){if(timer)clearTimeout(timer);throw error;});
}
function errorMsg(e){
 if(e&&e.name==='AbortError')return tr('Przekroczono czas odpowiedzi serwera Xtream.','Xtream server timeout.');
 if(e&&e.message&&e.message.indexOf('HTTP ')===0)return e.message;
 return tr('Połączenie nieudane. Sprawdź adres, dostępność serwera i CORS w webOS.','Connection failed. Verify provider address, availability and CORS.');
}
function test(){
 var a;try{a=fromForm();}catch(e){msg(e.message);return;}
 msg('Sprawdzam konto Xtream...','Testing Xtream account...');
 return request(a,null).then(function(data){
  var info=data&&data.user_info||{};
  if(info.auth===1||info.auth==='1')msg('Połączenie działa. Konto: '+(info.status||'aktywne'),'Connected. Account: '+(info.status||'Active'));
  else msg('Serwer odpowiedział, ale nie potwierdził autoryzacji.','Provider did not confirm authorization.');
 },function(e){msg(errorMsg(e));});
}
function maybeAdult(i){return String(i.is_adult||0)==='1';}
function add(kind,list,catmap,into,seen){
 (Array.isArray(list)?list:[]).forEach(function(i){
  if(maybeAdult(i))return;
  var id=(kind==='live'?i.stream_id:kind==='movie'?i.stream_id:i.series_id),name=i.name||i.title;
  if(!id||!name||seen[kind+':'+id])return;
  seen[kind+':'+id]=true;
  into.push({type:kind,id:String(id),title:name,group:(catmap[String(i.category_id)]||''),
             category:String(i.category_id||''),ext:kind==='movie'?(i.container_extension||'mp4'):'',
             icon:kind==='live'?(i.stream_icon||''):(i.cover||i.stream_icon||'')});
 });
}
function sync(force){
 var a=account();
 if(!a){msg('Najpierw dodaj playlistę.','Add a playlist first.');return Promise.resolve(false);}
 if(isLoading)return Promise.resolve(false);
 if(!force&&library[selected]){records=library[selected].records;categories=library[selected].categories;displayCategories();runSearch(true);return Promise.resolve(true);}
 isLoading=true;records=[];categories=[];library[selected]=null;
 var catmap={},found=[],seen={};var jobs=[
  ['get_live_categories','live'],['get_vod_categories','movie'],['get_series_categories','series'],
  ['get_live_streams','live'],['get_vod_streams','movie'],['get_series','series']
 ];
 // Serial processing is deliberate; providers can impose a single-connection limit.
 return request(a,null).then(function(info){
  var u=info&&info.user_info||{};
  if(u.auth!==1&&u.auth!=='1')throw new Error('Xtream: authentication rejected');
  return jobs.reduce(function(chain,job,index){
   return chain.then(function(){
    msg(tr('Synchronizacja katalogu: ','Syncing catalog: ')+(index+1)+'/'+jobs.length+' ('+job[0]+')');
    return request(a,job[0]).then(function(data){
     if(index<3){
      (Array.isArray(data)?data:[]).forEach(function(c){
       var entry={id:String(c.category_id),title:String(c.category_name||'') ,type:job[1]};
       categories.push(entry);catmap[entry.type+':'+entry.id]=entry.title;
      });
     }else{
      var c={};Object.keys(catmap).forEach(function(k){if(k.indexOf(job[1]+':')===0)c[k.substring(job[1].length+1)]=catmap[k];});
      add(job[1],data,c,found,seen);
     }
    });
   });
  },Promise.resolve());
 }).then(function(){
  library[selected]={records:found,categories:categories,loadedAt:Date.now()};
  records=found;
  isLoading=false;displayCategories();runSearch(true);
  msg(tr('Katalog gotowy: ','Catalog ready: ')+found.length.toLocaleString('pl-PL')+' pozycji.');
  return true;
 },function(e){
  isLoading=false;msg(errorMsg(e));return false;
 });
}
function displayCategories(){
 var s=$('category');while(s.options.length>1)s.remove(1);
 categories.filter(function(c){return filter==='all'||c.type===filter;}).forEach(function(c){
  var o=document.createElement('option');o.value=c.type+':'+c.id;o.textContent=c.title;s.appendChild(o);
 });
 category='';s.value='';
}
function runSearch(reset){
 if(reset)page=0;
 query=$('query').value.trim();filter=$('type').value;category=$('category').value;
 // No random sample without a query: show first 60 without expensive DOM work.
 var text=norm(query),found=[],seen={};
 records.forEach(function(i){
  if(filter!=='all'&&i.type!==filter)return;
  if(category&&i.type+':'+i.category!==category)return;
  if(text&&norm(i.title).indexOf(text)<0)return;
  if(!seen[i.type+':'+i.id]){seen[i.type+':'+i.id]=1;found.push(i);}
 });
 var groupEntries=[];
 if(!category&&(filter==='group'||(filter==='all'&&!!text))){
  categories.filter(function(c){return !text||norm(c.title).indexOf(text)>=0;}).forEach(function(c){
   groupEntries.push({type:'group',id:c.id,title:c.title,group:c.type,category:c.type+':'+c.id});
  });
 }
 var items=groupEntries.concat(found);
 var max=Math.max(0,Math.ceil(items.length/LIMIT)-1);page=Math.min(page,max);
 var paged=items.slice(page*LIMIT,(page+1)*LIMIT);clear($('results'));
 paged.forEach(function(i){$('results').appendChild(itemRow(i,function(){choose(i);}));});
 $('pagecount').textContent=items.length?((page+1)+' / '+(max+1)):'0 / 0';
 $('prev').style.opacity=page===0?'.4':'1';$('next').style.opacity=page===max?'.4':'1';
 if(!isLoading)msg(items.length?('Wyniki: '+items.length.toLocaleString('pl-PL')):'Brak wyników. Dodaj playlistę lub zmień filtr.','Results: '+items.length);
 rows();
}
function choose(i){
 if(i.type==='group'){
  $('type').value=i.group;$('query').value='';filter=i.group;displayCategories();
  $('category').value=i.category;return runSearch(true);
 }
 if(i.type==='series')return showEpisodes(i);
 return play(i);
}
function showEpisodes(i){
 var a=account();if(!a)return;
 $('episodes').hidden=false;msg('Pobieram odcinki: '+i.title);
 request(a,'get_series_info',{series_id:i.id}).then(function(d){
  clear($('episodelist'));var list=[];
  Object.keys(d.episodes||{}).forEach(function(season){
   (d.episodes[season]||[]).forEach(function(e){
    var ext=e.container_extension||'mp4';
    list.push({id:String(e.id),type:'episode',title:e.title||('Odcinek '+e.episode_num),
               group:'Sezon '+season,ext:ext});
   });
  });
  list.slice(0,300).forEach(function(e){$('episodelist').appendChild(itemRow(e,function(){play(e);}));});
  $('episodetitle').textContent=i.title+' · '+list.length+' odcinków';
  msg(list.length?'Wybierz odcinek':'Brak odcinków');
  rows();
 }).catch(function(e){msg(errorMsg(e));});
}
function streamUrl(a,i){
 var ext=i.ext|| (i.type==='live'?'m3u8':'mp4');
 var path=i.type==='live'?'live':i.type==='movie'?'movie':'series';
 if(!/^[a-z0-9]{1,8}$/i.test(ext)||!/^[0-9]+$/.test(i.id))throw Error('invalid media item');
 return a.host+'/'+path+'/'+encodeURIComponent(a.username)+'/'+encodeURIComponent(a.password)+'/'+encodeURIComponent(i.id)+'.'+ext;
}
function play(i){
 var a=account();if(!a)return;
 var video=$('video'),src;
 try{src=streamUrl(a,i);}catch(e){msg('Nieprawidłowy adres strumienia.');return;}
 playing=true;playerFocus=document.querySelector('.focus');$('player').hidden=false;
 $('playmsg').textContent='Odtwarzanie: '+i.title;
 video.src=src;video.load();
 var p=video.play();if(p&&p.catch)p.catch(function(){ $('playmsg').textContent='Nie można uruchomić strumienia. Sprawdź zgodność kodeka i adres dostawcy.';});
 rows();
}
function stop(){
 var video=$('video');video.pause();video.removeAttribute('src');video.load();
 playing=false;$('player').hidden=true;
 rows();
}
function nav(){
 if(playing)return [[$('playerclose')]];
 var rows=[[$('config'),$('refresh'),$('close')]];
 var acc=Array.prototype.slice.call($('accounts').querySelectorAll('.f'));if(acc.length)rows.push(acc);
 if(!$('form').hidden){rows.push([$('name'),$('url')],[$('user'),$('pass')],[$('save'),$('test'),$('cancel')]);}
 else{
  rows.push([$('query'),$('search'),$('type'),$('category')]);
  var results=Array.prototype.slice.call($('results').querySelectorAll('.dx-item'));
  for(var x=0;x<results.length;x+=6)rows.push(results.slice(x,x+6));
  rows.push([$('prev'),$('next')]);
  if(!$('episodes').hidden){
   var eps=Array.prototype.slice.call($('episodelist').querySelectorAll('.dx-item'));
   for(var y=0;y<eps.length;y+=5)rows.push(eps.slice(y,y+5));
   rows.push([$('episodesclose')]);
  }
 }
 return rows;
}
function bind(id,fn){$(id).onok=fn;}
['name','url','user','pass','query','type','category'].forEach(function(id){
 var el=$(id);el.classList.add('f');el.onok=function(){el.focus();};
});
bind('config',function(){editAccount(null);});
bind('refresh',function(){sync(true);});
bind('close',function(){TV.closeView();});
bind('save',persist);
bind('test',test);
bind('cancel',function(){form(false);});
bind('search',function(){runSearch(true);});
bind('prev',function(){if(page>0){page--;runSearch(false);}});
bind('next',function(){page++;runSearch(false);});
bind('episodesclose',function(){$('episodes').hidden=true;rows();});
bind('playerclose',stop);
$('query').addEventListener('keydown',function(e){if(e.key==='Enter'){e.stopPropagation();e.preventDefault();$('query').blur();runSearch(true);}});
$('type').addEventListener('change',function(){filter=$('type').value;displayCategories();runSearch(true);});
$('category').addEventListener('change',function(){runSearch(true);});
$('video').addEventListener('error',function(){if(playing)$('playmsg').textContent='Nie udało się odtworzyć tego formatu/strumienia na webOS.';});
$('video').addEventListener('playing',function(){if(playing)$('playmsg').textContent='Odtwarzanie';});
root.addEventListener('click',function(e){
 var b=e.target.closest('.f');if(b&&b.onok){e.stopImmediatePropagation();b.onok();}
},true);
document.addEventListener('keydown',function(e){
 if(TV.view()!=='xtream')return;
 var t=e.target;
 if(playing)return;
 if(t&&(t.tagName==='INPUT'||t.tagName==='SELECT')){
  if(e.keyCode===461||e.keyCode===27){t.blur();e.stopImmediatePropagation();e.preventDefault();return;}
  if(e.keyCode===13){t.blur();e.stopImmediatePropagation();e.preventDefault();if(t.id==='dx-query')runSearch(true);return;}
  e.stopImmediatePropagation();
 }
},true);
TV.addView('xtream',{
 nav:nav,
 show:function(){root.hidden=false;redrawAccounts();if(!selected&&saved.length)selected=saved[0].id;
  redrawAccounts();if(library[selected]){records=library[selected].records;categories=library[selected].categories;displayCategories();runSearch(true);}
  else if(selected)sync(false);else msg('Dodaj playlistę Xtream.');TV.rebuild(0,0);},
 hide:function(){if(playing)stop();root.hidden=true;},
 back:function(){if(playing){stop();return true;}if(!$('form').hidden){form(false);return true;}
  if(!$('episodes').hidden){$('episodes').hidden=true;rows();return true;}TV.closeView();return true;},
 keydown:function(e){if(!playing)return false;
  if(e.keyCode===461||e.keyCode===27||e.keyCode===8){stop();return true;}
  if(e.keyCode===32||e.keyCode===415){var v=$('video');if(v.paused)v.play();else v.pause();return true;}
  return false;},
 onFocus:function(el){if(el&&el.scrollIntoView)el.scrollIntoView({block:'nearest',inline:'nearest'});}
});
TV.addTab(tr('IPTV','IPTV'),'xtream');
TV.xtream={getAccounts:function(){return saved.map(function(a){return {id:a.id,label:a.label,host:a.host.replace(/:\/\/[^/]+/,'://[provider]')};});},
 sync:sync,search:runSearch,select:choose,open:function(){TV.openView('xtream');},
 // Only used by the user's own paired TV provisioning script, never exposed remotely.
 putAccount:function(a){editingId=null;$('name').value=a.label||'Xtream';$('url').value=a.host;$('user').value=a.username;$('pass').value=a.password;persist();}
};
})();