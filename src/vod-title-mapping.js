/* Deterministic, conservative media identity mapping.
   Metadata-only; NO provider passwords or playback URIs in this module. */
(function(root){
'use strict';
function normalize(text){
 return String(text||'').normalize('NFKD').replace(/[\u0300-\u036f]/g,'')
 .toLowerCase().replace(/\[(?:pl|pol|en|eng|uk|us|au)\]/gi,'')
 .replace(/^(?:(?:pl|pol|en|eng|uk|us|au|nf|netflix)\s*[-:]+\s*)+/i,'')
 .replace(/\b(?:19|20)\d{2}\b/g,'').replace(/[^a-z0-9]+/g,' ').trim();
}
function year(item){
 var y=String(item.year||item.release_date||item.first_air_date||'').match(/(?:19|20)\d{2}/);
 return y ? y[0] : '';
}
function mediaType(item){return (item.type||item.media_type)==='series'||(item.type||item.media_type)==='tv'?'tv':(item.type||item.media_type)==='live'?'live':'movie';}
function strongMatch(a,b){
 if(mediaType(a)!==mediaType(b))return false;
 if(mediaType(a)==='live')return false;
 var aid=String(a.id||'');
 var rawId=String(b.tmdb||b.tmdb_id||'').trim();
 var xid=/^[1-9][0-9]*$/.test(rawId)?rawId:'';
 if(xid && aid) return xid===aid;
 var name=normalize(a.title||a.name);
 var candidate=normalize(b.title||b.name);
 var ay=year(a),by=year(b);
 return !!(name&&candidate&&name===candidate&&ay&&by&&ay===by);
}
function merge(tmdb,xtream){
 var entries=(tmdb||[]).map(function(t){return {tmdb:t,sources:[]};});
 (xtream||[]).forEach(function(s){
  var matches=entries.filter(function(e){return e.tmdb && strongMatch(e.tmdb,s);});
  if(matches.length===1){matches[0].sources.push(s);}
  else entries.push({tmdb:null,sources:[s]});
 });
 return entries;
}
root.DC4ITitleMapping={normalize:normalize,year:year,strongMatch:strongMatch,merge:merge};
})(window);
