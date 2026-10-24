# Dziennik zmian - DC4I VOD TV

Identyfikator aplikacji `com.dc4i.boringtv` pozostaje bez zmian, aby aktualizacje zastępowały wcześniejsze wersje.

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
