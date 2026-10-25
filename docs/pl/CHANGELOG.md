# Dziennik zmian - DC4I VOD TV

Identyfikator aplikacji od wersji 1.2.0: `com.dc4i.vodtv`. Starszy `com.dc4i.boringtv` jest archiwalny.

## [1.2.13] - 25.10.2026

### Jednolite wyszukiwanie w zewnętrznych serwisach
- W Szukaj i szczegółach tytułu udostępniono wspólny pasek **Szukaj w:** YouTube, Kodi, Plex, Stremio, Smarters Player.
- Dostępność VOD nadal pochodzi z TMDB, z regionu i serwisów wybranych przez użytkownika. Gdy nie potwierdzono oferty: **Brak w wybranych serwisach**, a niżej pięć opcji wyszukiwania.
- Usunięto pojedynczy przycisk wyszukiwania YouTube i powtarzające się przyciski z listy VOD. Sterowanie pilotem jest obsługiwane w obu widokach.
- W ustawieniach: Website → `https://www.dc4i.com/labs`, App repo → `https://lg.darc.dev/browse/`; logo prowadzi do DC4i Labs.
- Dodatek Kodi Title Handoff 0.1.2 otwiera wyszukiwanie tekstowe w katalogu XCUI/Xtream skonfigurowanym przez użytkownika. Potwierdzono okno wyników na LG.
- Plex Web otwiera wyszukiwanie tytułu. Stremio i Smarters korzystają z najlepszych dostępnych parametrów uruchomienia; brak gwarancji wyszukania w aplikacji zewnętrznej.

### Testy
- Przeszły testy JavaScript, IPK, interakcji pięciu przycisków, otwierania szczegółów VOD i widoku Szukaj w Chrome 1920×1080 oraz lokalne testy nowego wyszukiwania Kodi.

## [1.2.12] - 25.10.2026

### Publikacja i sprawdzanie wersji
- Opublikowano `com.dc4i.vodtv_1.2.12_all.ipk` oraz zaktualizowano manifest Homebrew na `lg.darc.dev`. Publiczny manifest zawiera datę wydania i sumę SHA-256.
- Szybkie ustawienia podczas otwierania odczytują najnowszą wersję z `https://lg.darc.dev/api/apps.json` i porównują ją z zainstalowaną: **Aktualna**, **Aktualizacja dostępna**, **Wersja nowsza niż repo**, **Offline**. Aplikacja nie instaluje aktualizacji bez potwierdzenia.
- Zachowano szerszy, czytelny panel 900 px, zatwierdzone logo neonowe, dedykację dla Ani i rodziny, linki do repozytorium i strony firmy.
- Dodatkowe akcje Kodi, Plex i YouTube nadal wykorzystują wcześniej przygotowane mechanizmy przekazywania tytułów.

### Testy
- Testy pakietu IPK, składni JavaScript, scenariuszy porównywania wersji, integracji Kodi i geometrii panelu 1920x1080 zakończyły się powodzeniem.
- Potwierdzono 33 aplikacje w katalogu, zachowując 32 inne pozycje. Pobranie publicznego IPK i porównanie SHA-256 z manifestem: OK.
- Wersja 1.2.12 została zainstalowana i uruchomiona na fizycznym LG. Telewizor odczytał z publicznego repozytorium wersję 1.2.12, a test w Chromium pokazał stan **Aktualna**. Pełna wizualna kontrola panelu bezpośrednio na ekranie TV pozostaje do wykonania.

## [1.2.2] - 24.10.2026

### Smarters Player
- Dodałem numer **1231221** z przekazanego linku do [LG Store](https://us.lgappstv.com/main/tvapp/detail?appId=1231221). To identyfikator katalogu sklepu, niepotwierdzony jako techniczny ID uruchomienia webOS.
- **Smarters Player jest zawsze widoczny** w menu *Aplikacje*. Gdy telewizor nie potwierdził ID, kafelek otrzymuje dopisek `sprawdź`, zamiast znikać.
- Po kliknięciu kafelka lub przycisku przy filmie aplikacja próbuje odnaleźć poprawny identyfikator i uruchomić program, włącznie z testem `1231221`. Zapisuje działający identyfikator w pamięci TV. Niepowodzenia rejestruje lokalnie bez ujawniania kluczy API.
- Nie potrzeba roota ani ręcznego wpisywania identyfikatorów na pilocie.

### Stremio i otwieranie tytułów
- Przycisk **Stremio - aplikacja** nadal wysyła link do filmu/serialu z numerem IMDb. Wersja LG może ten link ignorować, nawet jeśli sama aplikacja się uruchomi.
- Nowy przycisk **Stremio Web (otwórz tytuł)** otwiera odpowiednią stronę filmu/serialu w oficjalnym Stremio Web za pomocą przeglądarki LG. To osobna alternatywa od natywnego Stremio; wymaga zgodności webOS i ewentualnego zalogowania.
- Smarters Player nie dokumentuje interfejsu wyszukiwania filmów poprzez parametry webOS. Przekazujemy nazwę tytułu, ale program może ją zignorować. Nie da się zagwarantować bezpośredniego odtworzenia.

### Testy
- Testy automatyczne Node: kafelek bez potwierdzonego ID, uruchomienie po numerze 1231221 (symulacja), błędy i diagnostyka, przekazanie IMDb do Stremio, URL filmu w Stremio Web.
- Test Chrome: oba warianty Stremio i Smarters przy wyszukanym tytule, działający interfejs, filtry VOD i pogoda po polsku.
- Zachowano 32 aplikacje w katalogu i pakiety 1.2.1/1.2.0 jako archiwum. **Test na fizycznym LG nadal otwarty**, issues #2 i #3.

## [1.2.1] - 24.10.2026

### Wykrywanie aplikacji LG i otwieranie tytułów
- Dodano identyfikator `com.iptvsmarters.app` z dokumentacji integratorów sterowania LG (Snap One i RTI). Wcześniejsza wersja go nie sprawdzała. Wykrycie konkretnej instalacji przez telewizor nadal wymaga odbioru.
- Poprawiono sprawdzanie aplikacji: system korzysta z pierwszego poprawnego ID i nie czeka na błędne lub zawieszone zapytania. Wspiera także dopasowanie po nazwie na liście zainstalowanych aplikacji, jeśli webOS na to pozwala.
- Przyciski **Otwórz Stremio** oraz **Otwórz IPTV Smarters Player** są w szczegółach każdego filmu lub serialu z wyszukiwarki, także tytułów dostępnych już w polskim Netflix.
- Stremio: pobieranie identyfikatora IMDb z TMDB i generowanie oficjalnych linków do szczegółów filmu/serialu; bez IMDb próba przekazania frazy wyszukiwania.
- Smarters Player: eksperymentalne przekazanie nazwy tytułu do natywnej aplikacji. Producent nie udostępnił dokumentacji deep-link dla webOS, dlatego nie ma gwarancji automatycznej wyszukiwarki.
- Zostaje identyfikator aplikacji `com.dc4i.vodtv`. Wersja 1.2.1 aktualizuje zainstalowaną 1.2.0 bez ponownej instalacji.

### Testy i ograniczenia
- Testy Node i Chrome potwierdzają wykrywanie ID w symulacji, format parametrów, przyciski dostępnych i pozostałych filmów.
- Bez rootowania, bez zmian neonowego logo. Pozostałe 31 aplikacji pozostaje w katalogu.
- Test natywnego uruchamiania na fizycznym LG nadal do wykonania, issues #2 i #3.
- Dokumentacja: [integracja odtwarzaczy LG](NATIVE-PLAYER-INTEGRATION.md).

## [1.2.0] - 24.10.2026

### Nowa tożsamość aplikacji
- Wersja **DC4I VOD TV 1.2.0** używa identyfikatora `com.dc4i.vodtv` zamiast starego `com.dc4i.boringtv`.
- Zmiana jest celowo niekompatybilna ze zwykłą aktualizacją, zgodnie ze zgodą właściciela. **Odinstaluj aplikację 1.1.1 lub wcześniejszą, potem zainstaluj 1.2.0** z `https://lg.darc.dev/`.
- Pakiet nosi nazwę `com.dc4i.vodtv_1.2.0_all.ipk`, manifest: `dc4i-vodtv.manifest.json`; stare pakiety pozostają archiwalne.

### Oficjalna neonowa grafika produktu
- Ikona w menu telewizora i ekran startowy wykorzystują piękną grafikę **Neon DC4I VOD TV**, stworzoną wcześniej w naszej rozmowie i zatwierdzoną przez użytkownika.
- Zachowano źródłową wersję w `assets/brand/DC4I_VOD_TV_Neon_Approved_2026-10-24.png`, wersję WebP z SHA-256 `fe7aa367fb1b4f83593a5a647f4dc4a7693ec0888c8e8a046cec02667781f840`, ikony 80/130px i nowy pasek firmowy.
- Logo korporacyjne DC4I pozostaje odrębnym wzorcem marki.

### Testy
- Nazwa, identyfikator i wersja w appinfo oraz całym IPK; poprawne logo, składnia JavaScript, API TMDB, interfejs pilota w Chrome i dostępność pliku z manifestu.
- Zachowane funkcje polskiego VOD, polskiej pogody i Stremio/IPTV. Test na fizycznym LG nadal otwarty.

## [1.1.1] - 24.10.2026

### Nowe funkcje
- Wyszukiwanie TMDB domyślnie pokazuje tytuły z ofertą streamingu w Polsce, rozpoznawaną na podstawie providerów `flatrate`, `free` i `ads`. Dodano filtry **Dostępne w kraju / Pozostałe / Wszystkie**, limit równoległych zapytań i cache.
- W szczegółach niedostępnych tytułów dodano przyciski otwierania natywnych aplikacji **Stremio** oraz **IPTV Smarters Player**. To otwieranie aplikacji, a nie gwarancja automatycznego znalezienia/odtworzenia filmu.
- Oficjalny identyfikator Stremio na LG: `io.strem.tv`. Identyfikator IPTV Smarters wymaga testu na urządzeniu; kafelek jest pokazywany na niezrootowanym TV tylko po potwierdzeniu aplikacji.
- Domyślna pogoda dla Warszawy i stabilne współrzędne także dla Londynu, Paryża, Berlina, Rzymu, Madrytu, Nowego Jorku, San Francisco i Los Angeles. Pozostałe miasta ze wcześniejszej listy pozostają.
- Testy E2E Chrome: filtr Polska, dostępne/niedostępne, przyciski Stremio/IPTV, polska pogoda, ukryte elementy wymagające roota.

### Poprawki
- Pełniejsze polskie warunki pogodowe, prognoza i etykiety, przy zachowaniu angielskiego przy wybranym EN.
- Jednorazowa migracja zapisanego `Auto` na Warszawę, ponieważ geolokalizacja IP wskazywała Tomaszów Mazowiecki. Użytkownik nadal może później ręcznie wybrać Auto.
- Dokładniejszy wybór miast o niejednoznacznych nazwach, m.in. Nowego Jorku.
- Skrócenie automatycznego sprawdzania ID aplikacji przy starcie.
- Zabezpieczenie przed usunięciem pozostałych aplikacji z repo podczas publikacji nowej wersji DC4I VOD TV.

### Pozostałe zadania
- [Issue #2](https://github.com/darekcze/dc4i-vod-tv/issues/2): identyfikator IPTV Smarters na konkretnym telewizorze.
- [Issue #3](https://github.com/darekcze/dc4i-vod-tv/issues/3): test głębokiego linkowania Stremio.
- [Issue #4](https://github.com/darekcze/dc4i-vod-tv/issues/4): wyjaśnienie licencji oryginalnego TheBoringTV.
- YouTube Data API v3: klucz jest prywatnie zapisany, integracja z serwerem jeszcze niedokończona.
- Dostępność VOD według TMDB może być opóźniona względem rzeczywistego katalogu operatora.
- Brak niezależnego testu na fizycznym LG TV.

## [1.1.0] - 24.10.2026
- Nowa nazwa DC4I VOD TV, zatwierdzony firmowy monogram D z obwodami i C z profilem twarzy, firmowa ikona oraz ekran startowy.
- Wersja polska i angielska, lokalizacja PL, lista 40 miast Europy i USA, opcje root ukryte w trybie Developer Mode.
- TMDB skonfigurowane. Katalog Homebrew: `https://lg.darc.dev/`.

## [1.0.1] - 24.10.2026
- Poprzednia nazwa DC4I BoringTV, pierwsza kompilacja dla Polski, YouTube jako opcjonalny bez blokowania uruchomienia.

## [1.2.4] - 24.10.2026

### Prawdziwy identyfikator IPTVSmartersPlayer z telewizora
- Sparowałem LG OLED55G42LW przez [LGWebOSRemote](https://github.com/klattimer/LGWebOSRemote). Telewizor zwrócił **67 aplikacji** w `listLaunchPoints`.
- **IPTVSmartersPlayer** ma ID `com.smarterstvplayers.net`. Osobna aplikacja **IPTVSmartersPro** ma ID `com.iptvsmarters.app`. Stremio ma ID `io.strem.tv`. Numer sklepu 1231221 nie jest właściwym ID uruchomienia.
- Poprawiłem kafelek, wykrywanie i uruchamianie, usunąłem wcześniejsze błędne identyfikatory Smarters, usunąłem zapisane nieprawidłowe ID i zabezpieczyłem przed otwieraniem wersji Pro.
- Pełną listę 67 aplikacji zapisałem prywatnie w AI-Hot jako JSON i CSV. LGWebOSRemote działa na komputerze, nie jest aplikacją IPK do instalacji na telewizorze.
- Wersja 1.2.4 aktualizuje 1.2.3 bez odinstalowywania. Bezpośrednie wyszukiwanie tytułu w natywnej IPTVSmartersPlayer nie zostało potwierdzone, ponieważ producent nie udokumentował interfejsu deep-link.

## [1.2.3] - 24.10.2026
- Poprawiono otwieranie tytułów z wyników wyszukiwania. Pełnoekranowa wyszukiwarka nie zasłania już szczegółów filmu, a po powrocie znów się pokazuje.
- Usunięto uruchamianie niewłaściwego Smarters Player Pro (LG Store 950615). Docelowy IPTV Smarters Player ma numer sklepu 1231221. Testujemy wyłącznie ten niepotwierdzony identyfikator, dopóki nie ustalimy właściwego ID webOS.
- Stremio Web pozostaje działającą opcją otwierania wybranego tytułu. Deep-linki do natywnych aplikacji Stremio i IPTV Smarters nie są potwierdzone.

## Aktualizacja katalogu - 25.10.2026

- Dodano oficjalne Kodi 21.0 Omega dla LG webOS (org.xbmc.kodi, ARM, bez root).
- Pakiet IPK pobierany z oficjalnego mirrora Kodi, a nie z Cloudflare Pages (limit rozmiaru pliku).
- SHA-256: b8ac326df8ad7cf0b52e4f816ab7c39c95410254b1bc3b9b3d024035ecec58ff.
- Kodi zainstalowano i uruchomiono na LG OLED55G42LW; Kodi 21.3 DMG dla macOS nie jest zgodne z webOS.
- Obsługa deeplink przez natywne Stremio na LG nadal niepotwierdzona.

## [1.2.5] - 25.10.2026

- Dodano kafelek Kodi oraz przycisk Kodi (otwórz aplikację) w szczegółach filmu.
- Dodano przycisk Plex (otwórz aplikację), tylko jeśli Plex jest wykryty na telewizorze.
- Zachowano YouTube (zwiastuny), Stremio, Stremio Web i IPTVSmartersPlayer.
- Kodi i Plex: uruchomienie aplikacji, nie automatyczne otwarcie filmu. Pełne deep linki wymagają odpowiednich API i identyfikatorów biblioteki.
