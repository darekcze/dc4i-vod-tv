# Dostawa i testy | DC4I VOD TV

Źródło repozytorium TV: https://lg.darc.dev/. Projekt Git: https://github.com/darekcze/dc4i-vod-tv.

Potwierdzone: poprawne oryginalne logo i SHA256, nazwa DC4I VOD TV, zgodne pakowanie IPK, region Polska, zmiana PL/EN, ukryte kontrolki root, test składni JavaScript i odpowiedź TMDB 200.

Niepotwierdzone: instalacja i sterowanie na fizycznym LG TV; YouTube Data API poprzez chroniony backend; kompletność deep linków do platform VOD; licencja źródłowego TheBoringTV. Nie uznawaj tych elementów za zakończone.

Rollback: przywróć całe poprzednie wdrożenie Cloudflare Pages (binarium i manifest razem). Poprzednie wersje trzymamy prywatnie w AI-Hot/private.

## Testy i zmiany wydania 1.1.1, 24.10.2026
- Wyszukiwanie: Polska, przełączniki Dostępne/Pozostałe/Wszystkie, rozpoznawanie flatrate/free/ads i przyciski Stremio/IPTV w szczegółach.
- Pogoda: pełniejsze polskie komunikaty, Warszawa jako domyślne miasto także po migracji Auto, niejednoznaczne miasta mają ustalone współrzędne.
- Aplikacje: Stremio `io.strem.tv`, IPTV Smarters tylko po potwierdzeniu identyfikatora przez system.
- Testy Chrome w rozdzielczości TV: PASS dla pogody, weryfikacji ofert, przycisków i ukrywania kontrolek roota. Test na fizycznym LG pozostaje otwarty.
- Źródło zmian: `CHANGELOG.md` i `docs/pl/CHANGELOG.md`. Ograniczenia: issues #2, #3, #4 w repozytorium.

## Wydanie 1.2.0 i nowe logo Neon DC4I VOD TV
- Właściciel zatwierdził zmianę ID na `com.dc4i.vodtv`. Wymaga odinstalowania starej aplikacji `com.dc4i.boringtv` i nowej instalacji.
- Neonowe logo pochodzi z wcześniejszego obrazu wygenerowanego w tym czacie, zapisane w `assets/brand/DC4I_VOD_TV_Neon_Approved_2026-10-24.png`.
- Ikona 80/130px, splash 1920x1080, menu aplikacji oraz manifest Homebrew używają neonowej identyfikacji.
- Stare pliki IPK pozostają jako archiwalne, w katalogu Homebrew wyświetlana jest nowa aplikacja.
- Test na prawdziwym telewizorze LG jeszcze nie wykonany.
