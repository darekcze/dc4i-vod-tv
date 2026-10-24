# Dziennik zmian - DC4I VOD TV

Identyfikator aplikacji `com.dc4i.boringtv` pozostaje bez zmian, aby aktualizacje zastępowały wcześniejsze wersje.

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

## [1.2.3] - 24.10.2026
- Poprawiono otwieranie tytułów z wyników wyszukiwania. Pełnoekranowa wyszukiwarka nie zasłania już szczegółów filmu, a po powrocie znów się pokazuje.
- Usunięto uruchamianie niewłaściwego Smarters Player Pro (LG Store 950615). Docelowy IPTV Smarters Player ma numer sklepu 1231221. Testujemy wyłącznie ten niepotwierdzony identyfikator, dopóki nie ustalimy właściwego ID webOS.
- Stremio Web pozostaje działającą opcją otwierania wybranego tytułu. Deep-linki do natywnych aplikacji Stremio i IPTV Smarters nie są potwierdzone.
