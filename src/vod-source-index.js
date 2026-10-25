/* Shared local source resolution: canonical TMDB cards link to owner-configured
   Xtream entries without needing any laptop, reverse proxy, or credentials in IPK. */
(function(root){
'use strict';
var TV=root.TV;if(!TV)return;
var records={}, promises={};
function kind(x){return (x.media_type||x.type)==='series'||(x.media_type||x.type)==='tv'?'tv':'movie';}
function key(x){return kind(x)+':'+String(x.id);}
function get(x){return records[key(x)]||[];}
function remember(x,list){if(x&&x.id)records[key(x)]=(list||[]).slice();}
function forTmdb(item) {
 if(!item || !item.id)return Promise.resolve([]);
 var k=key(item);if(records[k])return Promise.resolve(records[k]);
 if(promises[k])return promises[k];
 if(!TV.xtream || !TV.xtream.getAccounts || !TV.xtream.getAccounts().length)
   return Promise.resolve([]);
 var name=String(item.title||item.name||'').trim();
 if(name.length<2)return Promise.resolve([]);
 promises[k]=TV.xtream.searchCatalog(name,{kind:kind(item)==='tv'?'series':'movie',language:'all'})
   .then(function(items){
     var matches=(items||[]).filter(function(s){return root.DC4ITitleMapping.strongMatch(item,s);});
     remember(item,matches);
     delete promises[k];
     return matches;
   },function(){delete promises[k];return [];});
 return promises[k];
}
TV.titleSources={get:get,remember:remember,forTmdb:forTmdb};
})(window);
