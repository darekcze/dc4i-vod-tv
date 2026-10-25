/* Official outbound weekly-chart links only. No feed ingestion or rankings. */
(function(){'use strict';
 var urls=['https://www.netflix.com/tudum/top10','https://www.netflix.com/tudum/top10/tv','https://www.netflix.com/tudum/top10/poland','https://www.netflix.com/tudum/top10/poland/tv'];
 function resolve(v){if(!v||['global','poland'].indexOf(v.region)<0||['film','tv'].indexOf(v.category)<0)return null;return urls[(v.region==='poland'?2:0)+(v.category==='tv'?1:0)];}
 window.DC4IChartLinks={resolve:resolve,allowed:function(url){return typeof url==='string'&&urls.indexOf(url)>=0;},feedEnabled:false,rightsStatus:'unverified'};
})();
