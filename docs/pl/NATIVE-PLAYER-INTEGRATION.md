# DC4I VOD TV 1.2.1: integracja z aplikacjami LG

Użytkownik potwierdził, że **Stremio** już pojawia się w katalogu aplikacji DC4I, a zainstalowany **IPTV Smarters Player** nie jest widoczny.

## Wykrywanie aplikacji
- Identyfikator Stremio: `io.strem.tv`.
- Identyfikator IPTV Smarters Player: `com.iptvsmarters.app` z dokumentacji integratorów LG [Snap One](https://help.snapone.com/sb-v4-ig/Content/Topics/IP%20Control%20Guide.htm) i [RTI](https://driverstore.uat.rticontrol.com/driver/lg-ip). Jest wiarygodnym kandydatem, ale trzeba go potwierdzić na naszym konkretnym telewizorze.
- Oficjalne webOS Application Manager `getAppLoadStatus` sprawdza, czy program o danym ID jest zainstalowany. Od teraz system kończy sprawdzanie natychmiast po pierwszym pozytywnym wyniku, nie czeka na niewłaściwe identyfikatory. Jeśli platforma pozwala, sprawdza też listę aplikacji po nazwie.
- Kafelek nie będzie widoczny, jeżeli telewizor nie potwierdzi instalacji. Nie ma potrzeby rootowania ani wpisywania ID pilotem.

## Otwieranie wyszukanych tytułów
- Przyciski **Otwórz Stremio** i **Otwórz IPTV Smarters Player** są wyświetlane w szczegółach każdego tytułu, także dostępnego przez Netflix lub inne polskie serwisy.
- Stremio: TMDB dostarcza identyfikator IMDb. Generowany jest oficjalny deep link Stremio do szczegółów filmu albo serialu. Bez IMDb następuje próba przekazania tytułu wyszukiwania. Obsługa tych parametrów przez natywną wersję na LG wymaga jeszcze testu.
- IPTV Smarters Player: wysyłamy nazwę tytułu w parametrach `search`, `searchQuery` i `title`. Producent **nie publikuje interfejsu deep-link dla LG**, zatem aplikacja może je zignorować i jedynie się uruchomić. Wtedy trzeba wyszukać tytuł w jej katalogu ręcznie.
- Smarters Player nie udostępnia filmów sam z siebie. Obsługuje wyłącznie własne, legalne listy i konta VOD.

## Testy i dalsze zadania
Testy automatyczne symulujące LG potwierdzają rozpoznawanie ID, brak blokowania przez niesprawdzone ID i poprawny format przekazywanych parametrów. Testy Chrome sprawdzają przyciski dla dostępnych i niedostępnych filmów. Fizyczny telewizor: weryfikacja w issues [#2](https://github.com/darekcze/dc4i-vod-tv/issues/2) i [#3](https://github.com/darekcze/dc4i-vod-tv/issues/3).

Aplikacja działa nadal bez roota i bez ręcznego podawania kluczy API na telewizorze.

## Uzupełnienie 1.2.2, numer LG Store i ograniczenia webOS
- Numer **1231221** z linku użytkownika to identyfikator wpisu w sklepie LG, a nie potwierdzony identyfikator uruchomienia. Sprawdzamy go jako jeden z kandydatów.
- LG wymaga rzeczywistego ID aplikacji do jej uruchomienia, ale zwykłe aplikacje webOS mogą nie mieć dostępu do listy wszystkich zainstalowanych programów.
- Smarters Player pozostaje widoczny na kafelku, przy braku potwierdzenia dodajemy `sprawdź`. Przy uruchamianiu automatycznie testujemy ID i zapisujemy wynik w diagnostyce lokalnej `vodNativeDiagnostics122` (bez kluczy, haseł i list).
- Natywne Stremio może ignorować linki. Dodano alternatywny przycisk Stremio Web, który otwiera stronę wybranego tytułu w przeglądarce LG, bez udawania natywnego odtworzenia.

## Wiarygodna identyfikacja z LG OLED55G42LW (1.2.4)
Odczytałem 67 aplikacji z `listLaunchPoints` przez połączenie LGWebOSRemote: `IPTVSmartersPlayer = com.smarterstvplayers.net`, `IPTVSmartersPro = com.iptvsmarters.app`, `Stremio = io.strem.tv`, `DC4I VOD TV = com.dc4i.vodtv`. Numer LG Store `1231221` nie jest identyfikatorem aplikacji. Poprawny identyfikator jest już w kodzie. Pełna lista aplikacji i klucz parowania są przechowywane wyłącznie w prywatnym AI-Hot. LGWebOSRemote jest narzędziem terminalowym Python na Mac mini/Mac Pro, nie plikiem IPK instalowanym na telewizorze.
