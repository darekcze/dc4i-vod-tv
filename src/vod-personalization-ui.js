/* DC4I VOD TV personalization: TV-local, per-profile settings and activity. */
(function () {
  'use strict';
  var TV=window.TV, engine=window.DC4IRecommender;
  if(!TV||!engine)return;
  var historyKey='recommendationOpensV1';
  var genres=[
    ['scifi','Sci-Fi'],['auto','Automatycznie'],['family','Familijne'],
    ['romance','Romantyczne'],['reality','Reality Show'],
    ['comedy','Komedia'],['drama','Dramat'],['action','Akcja'],
    ['documentary','Dokument'],['horror','Horror']
  ];
  [
    {key:'recoEnabled',title:'Polecane: personalizacja',hint:'Włącz wiersz z oceną dopasowania na ekranie VOD',opts:[[true,'Włącz'],[false,'Wyłącz']],def:true},
    {key:'recoFavouriteGenre',title:'Polecane: ulubiony gatunek',hint:'Priorytet w rankingu, bez ograniczania katalogu',opts:genres,def:'scifi'},
    {key:'recoSciFiMin',title:'Polecane: Sci-Fi od oceny TMDB',hint:'Dopiero filmy i seriale osiągające wybrany próg',opts:[[0,'Wszystkie'],[5,'5/10'],[6,'6/10'],[7,'7/10'],[8,'8/10'],[9,'9/10']],def:6},
    {key:'recoHorrorMode',title:'Polecane: horrory',hint:'Wybierz ukrywanie albo tylko wyjątkowo wysoko oceniane',opts:[['high','Tylko wysoko oceniane'],['hide','Nie pokazuj horrorów']],def:'high'},
    {key:'recoHorrorMin',title:'Polecane: horror od oceny TMDB',hint:'Stosowane, jeśli horrory nie są ukryte',opts:[[6,'6/10'],[7,'7/10'],[8,'8/10'],[9,'9/10'],[10,'10/10']],def:9},
    {key:'recoOtherMin',title:'Polecane: pozostałe od oceny TMDB',hint:'Wartości ocen nie są sztucznie uzupełniane',opts:[[0,'Wszystkie ocenione'],[5,'5/10'],[6,'6/10'],[7,'7/10'],[8,'8/10'],[9,'9/10']],def:7},
    {key:'recoEveningBoost',title:'Polecane: filmy familijne / romantyczne wieczorem',hint:'Dodatkowe punkty między 18:00 a 23:59',opts:[[true,'Premiuj wieczorem'],[false,'Bez bonusu']],def:true},
    {key:'recoLearnHistory',title:'Polecane: uwzględnij lokalne wybory',hint:'Historia kliknięć tylko w tej aplikacji, nie historia Netflixa',opts:[[true,'Tak'],[false,'Nie']],def:true},
    {key:'recoHideOpened',title:'Polecane: wcześniej otwarte tytuły',hint:'Otworzenie nie oznacza obejrzenia filmu',opts:[[false,'Mogą się powtarzać'],[true,'Nie proponuj ponownie']],def:false},
    {key:'recoClearHistory',title:'Polecane: historia wyborów profilu',hint:'Usuwa tylko zapisane otwarcia w bieżącym profilu',opts:[['clear','Wyczyść wybory']],def:''}
  ].forEach(function(cfg){
    TV.addSetting({key:cfg.key,title:cfg.title,hint:cfg.hint,opts:cfg.opts},cfg.def);
  });
  function settings(){
    return engine.settings({
      enabled:TV.S.recoEnabled!==false,
      favouriteGenre:TV.S.recoFavouriteGenre||'scifi',
      sciFiMin:TV.S.recoSciFiMin==null?6:TV.S.recoSciFiMin,
      horrorMin:TV.S.recoHorrorMin==null?9:TV.S.recoHorrorMin,
      otherMin:TV.S.recoOtherMin==null?7:TV.S.recoOtherMin,
      hideHorror:TV.S.recoHorrorMode==='hide'||!!(TV.P&&TV.P.extraQ),
      eveningBoost:TV.S.recoEveningBoost!==false,
      learnHistory:TV.S.recoLearnHistory!==false,
      hideOpened:TV.S.recoHideOpened===true
    });
  }
  function history(){
    var h=TV.store(historyKey);
    return Array.isArray(h)?h:[];
  }
  function clear(){
    TV.store(historyKey,[]);
    TV.toast('Wyczyszczono wybory bieżącego profilu');
    TV.refresh();
  }
  function record(item){
    if(!item || !item.tmdb || !item.tmdb.id)return;
    TV.store(historyKey,engine.record(history(),item,'opened',Date.now()));
  }
  TV.personalized={settings:settings,history:history,clear:clear};
  // Only user actions inside DC4I VODTV are observed. Never mark as watched.
  var originalItemOk=TV.itemOk;
  TV.itemOk=function(item){record(item);return originalItemOk(item);};
  var originalOpenItem=TV.openItem;
  TV.openItem=function(item){record(item);return originalOpenItem(item);};
  TV.addRow(function(){
    var pref=settings();
    if(!pref.enabled || typeof TV.homeCandidates!=='function')return null;
    var source=TV.homeCandidates();
    if(!source || !source.length)return null;
    var suggestions=engine.rank(source,pref,history(),Date.now()).slice(0,14);
    if(!suggestions.length)return null;
    var cards=suggestions.map(function(entry){
      return Object.assign({},entry.item,{recoScore:entry.score,recoReason:entry.reason});
    });
    return {title:'Dopasowane do profilu',items:cards};
  });
})();
