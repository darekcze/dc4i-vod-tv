/* DC4I VOD TV Polish/English localization, compatible with webOS Chromium. */
(function(){
'use strict';
var TV=window.TV;if(!TV)return;
var lang=TV.S.uiLang==='en'?'en':'pl';document.documentElement.lang=lang;
var pairs=[
['For you','Dla Ciebie'],['Live','Na żywo'],['Apps','Aplikacje'],['Search','Szukaj'],
['Settings','Ustawienia'],['Interface language','Język interfejsu'],['Your apps','Twoje aplikacje'],
['Country','Kraj'],['Recommendation languages','Języki rekomendacji'],
['Your streaming services','Twoje serwisy streamingowe'],['Weather city','Miasto pogody'],
['Clock','Zegar'],['Trending on YouTube row','Popularne na YouTube'],
['Trending on YouTube','Popularne na YouTube'],['Rotate featured titles','Automatyczna zmiana polecanych filmów'],
['Continue watching','Kontynuuj oglądanie'],['Top picks for you','Polecane dla Ciebie'],
['Trending today','Trendy dnia'],['My watchlist','Moja lista'],
['Watchlist','Lista do obejrzenia'],['In watchlist','Na liście'],
['Trailer','Zwiastun'],['Cast','Obsada'],['More like this','Podobne filmy i seriale'],
['Where to watch','Gdzie obejrzeć'],['Not on your services','Brak w wybranych serwisach'],
['Added to your watchlist','Dodano do listy'],['Removed from your watchlist','Usunięto z listy'],
['Edit apps','Edytuj aplikacje'],['Done','Gotowe'],['Close','Zamknij'],
['Clear history','Wyczyść historię'],['Show hidden apps','Pokaż ukryte aplikacje'],
['On','Włącz'],['Off','Wyłącz'],['Auto','Automatycznie'],
['Movie','Film'],['Series','Serial'],['Open','Otwórz'],
['Search movies & shows','Szukaj filmów i seriali'],['Search YouTube','Szukaj w YouTube'],
['Trending searches','Popularne wyszukiwania'],['Searching…','Wyszukiwanie…'],
['Search failed, check the connection','Błąd wyszukiwania, sprawdź połączenie'],
['Checking where to watch…','Sprawdzanie dostępności…'],
['Rent','Wypożycz'],['Buy','Kup'],['Space','Spacja'],
['Loading weather…','Wczytywanie pogody…'],['Change city','Zmień miasto'],
['Now','Teraz'],['Today','Dziś'],['Feels like','Odczuwalna'],
['Humidity','Wilgotność'],['Wind','Wiatr'],['Sunrise','Wschód słońca'],
['Sunset','Zachód słońca'],['Next 12 hours','Kolejne 12 godzin'],
['TV speaker','Głośniki TV'],['Bluetooth soundbar','Soundbar Bluetooth'],
['Headphones','Słuchawki'],['Optical','Optyczne'],['Line out','Wyjście liniowe'],
['Home Wi-Fi','Domowe Wi-Fi'],['Connected','Połączono'],['Not connected','Brak połączenia'],
['Muted','Wyciszono'],['Screen off','Wyłącz ekran'],['Screensaver','Wygaszacz'],
['Accessibility','Dostępność'],['Audio output','Wyjście audio'],
['Sound mode','Tryb dźwięku'],['Volume','Głośność'],
['Brightness','Jasność'],['Inputs','Wejścia'],
['Kids profile','Profil dziecięcy'],['Profiles','Profile'],['Profile','Profil'],
['Refresh','Odśwież'],['Retry','Ponów próbę'],
['Could not load details','Nie udało się pobrać szczegółów'],
['Poland','Polska'],['United Kingdom','Wielka Brytania'],
['United States','Stany Zjednoczone'],['Germany','Niemcy'],['France','Francja'],
['Spain','Hiszpania'],['Italy','Włochy'],
['Weather','Pogoda'],['Clear sky','Bezchmurnie'],['Partly cloudy','Częściowe zachmurzenie'],
['Cloudy','Pochmurno'],['Fog','Mgła'],['Light rain','Słaby deszcz'],
['Rain','Deszcz'],['Snow','Śnieg'],['Thunderstorm','Burza']
];
var en2pl=Object.create(null),pl2en=Object.create(null);
pairs.forEach(function(p){en2pl[p[0]]=p[1];if(!pl2en[p[1]])pl2en[p[1]]=p[0];});
var pref=[['Popular on ','Popularne w '],['Open in ','Otwórz w '],
 ['▶ Watch on ','▶ Oglądaj w '],['Because you viewed ','Ponieważ oglądano '],
 ['Results for ','Wyniki dla '],['No results for ','Brak wyników dla '],
 ['Next ','Kolejne '],['Not streaming in ','Niedostępne w '],
 ['Rent or buy: ','Wypożycz lub kup: ']];
function adapt(value){
 if(typeof value!=='string')return value;
 var pre=/^\s*/.exec(value)[0],post=/\s*$/.exec(value)[0],body=value.trim();
 if(!body)return value;
 var dictionary=lang==='pl'?en2pl:pl2en;
 var after=dictionary[body]||body;
 if(after===body)pref.forEach(function(p){
  var from=lang==='pl'?p[0]:p[1],to=lang==='pl'?p[1]:p[0];
  if(body.indexOf(from)===0)after=to+body.slice(from.length);
 });
 return pre+after+post;
}
function translate(n){
 if(!n)return;
 if(n.nodeType===3){var v=n.nodeValue,after=adapt(v);if(v!==after)n.nodeValue=after;return;}
 if(n.nodeType!==1||/^(SCRIPT|STYLE|TEXTAREA|INPUT|NOSCRIPT)$/.test(n.nodeName))return;
 var title=n.getAttribute('title');if(title){var t=adapt(title);if(title!==t)n.setAttribute('title',t);}
 for(var c=n.firstChild;c;c=c.nextSibling)translate(c);
}
translate(document.body);
var ob=new MutationObserver(function(list){list.forEach(function(rec){
 if(rec.type==='characterData')translate(rec.target);
 else rec.addedNodes.forEach(translate);
});});
ob.observe(document.body,{subtree:true,childList:true,characterData:true});
window.DC4I_I18N={language:lang,translate:translate};
})();
