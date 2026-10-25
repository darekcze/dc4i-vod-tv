/* Candidates from the already-loaded TMDB catalogue; never a verified airing link. */
(function(root){
 'use strict';
 function title(s){return typeof s==='string'?s.normalize('NFKC').trim().toLocaleLowerCase().replace(/\s+/g,' '):'';}
 function match(event,items){
  if(!event||!title(event.title)||!/^\d{4}$/.test(event.year||''))return {status:'unmatched',verified:false};
  var found=Object.create(null);
  (Array.isArray(items)?items:[]).slice(0,2000).forEach(function(item){
   if(!item||!item.tmdb||!Number.isSafeInteger(item.tmdb.id)||item.tmdb.id<=0||
      ['movie','tv'].indexOf(item.tmdb.type)<0)return;
   var year=String(item.release_date||item.first_air_date||'').slice(0,4);
   if(year!==event.year||title(item.title)!==title(event.title))return;
   var rating=Number.isFinite(item.vote_average)&&item.vote_average>0&&item.vote_average<=10&&
     Number.isSafeInteger(item.vote_count)&&item.vote_count>0?
     {value:item.vote_average,votes:item.vote_count,source:'TMDB'}:null;
   found[item.tmdb.type+':'+item.tmdb.id]={id:item.tmdb.id,type:item.tmdb.type,title:item.title.slice(0,500),year:year,rating:rating};
  });
  var keys=Object.keys(found);
  return {status:keys.length===1?'candidate':keys.length?'ambiguous':'unmatched',verified:false,
   candidate:keys.length===1?found[keys[0]]:null};
 }
 root.DC4IEpgIdentity={match:match};
})(window);
