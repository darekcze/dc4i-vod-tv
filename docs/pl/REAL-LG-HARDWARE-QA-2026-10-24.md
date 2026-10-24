# DC4I VOD TV | Testy na fizycznym LG | 24.10.2026

**Telewizor:** LG OLED55G42LW, `192.168.1.60`. **Aplikacja:** `com.dc4i.vodtv` 1.2.4. **Stan:** zainstalowana i przetestowana na fizycznym LG. Dowody pochodzą z LGWebOSRemote oraz webOS DevTools Inspector działającego na telewizorze.

## Testy zakończone powodzeniem

- Strzałki **lewo, prawo, góra, dół**: prawidłowo zmieniają fokus na ekranie głównym oraz przełączają film w sekcji głównej.
- **OK:** otwiera wyszukiwarkę. Pobrano rzeczywiste wyniki TMDB z telewizora.
- Wyszukano **Matrix**, 1999: 16 wyników, przełączanie fokusu między pierwszymi dwoma wynikami, OK otwiera szczegóły.
- Szczegóły Matrix: okładka, polski opis, ocena, Prime Video, przyciski Stremio (natywne), Stremio Web i Smarters Player.
- **Back:** szczegóły -> wyszukiwarka -> ekran główny; żaden overlay nie zasłania treści.
- Menu **Aplikacje:** 18 kafelków, w tym IPTV Smarters Player, zmiana fokusu strzałkami i Back.
- Szybkie ustawienia: otwarcie, wybór następnego elementu, powrót.
- Pogoda: otwarcie panelu, polski komunikat wczytywania, powrót.
- **Stremio:** uruchomienie przyciskiem z poziomu szczegółów *Matrix* potwierdzone przez LG — aktywna aplikacja `io.strem.tv`.
- **IPTVSmartersPlayer:** przycisk w szczegółach Matrix uruchamia `com.smarterstvplayers.net` (właściwy program, NIE Smarters Pro `com.iptvsmarters.app`).

## Ważne ograniczenie metodologii

Cały scenariusz klawiszy przeszedł przez **syntetyczne zdarzenia `keydown` wstrzyknięte przez inspektor webOS do aplikacji działającej na prawdziwym LG**. Wykonał się ten sam kod nawigacji, którego używa pilot. Osobna emulacja fizycznego pilota przez gniazdo LGWebOSRemote często powodowała jedynie `keyup`, bez `keydown`; dlatego **nie ma jeszcze certyfikacji wszystkich rzeczywistych klawiszy pilota Magic Remote**. Jedna próba RIGHT zdalnym pilotem zmieniła tytuł, ale działanie nie było stabilne. W trakcie testów Netflix chwilowo przejął pierwszy plan i wtedy DC4I nie otrzymywała zdarzeń.

## Niepotwierdzone

- **Natywne Stremio:** telewizor uruchamia aplikację, lecz nie dało się potwierdzić przejścia bezpośrednio do filmu *Matrix*. LG może ignorować `contentTarget`.
- **Natywne IPTV Smarters Player:** właściwa aplikacja uruchamia się z DC4I, lecz nie zweryfikowano, że odbiera parametry wyszukiwania i otwiera konkretny film. Producent nie udostępnia znanej nam dokumentacji deep-link dla LG.
- **Stremio Web:** użytkownik wcześniej potwierdził, że otwiera konkretny film prawidłowo. To inne rozwiązanie niż Stremio natywne.
- Inspektor `ares-inspect` nie udostępnia wnętrza obu zewnętrznych aplikacji; zrzuty ekranu uprzywilejowaną usługą LG są zabronione (odmowa dostępu). Nie próbować obchodzić uprawnień.
- Pełna aktualna prognoza pogody nie była w tym teście weryfikowana po wczytaniu danych (tylko polski komunikat i nawigacja).

**Werdykt:** nawigacja w DC4I na prawdziwym LG oraz uruchamianie obu właściwych aplikacji przez przyciski w szczegółach filmu są potwierdzone. **Nie** jest potwierdzone automatyczne otwieranie samego filmu wewnątrz obu aplikacji ani niezawodność każdego fizycznego klawisza pilota. Zadania #2 i #3 pozostają otwarte.

**Dowody prywatne na Mac Pro:**
`/Volumes/AI-Hot/Services/LGWebOSRemote/results/real-lg-cdp-home.png`, `real-lg-cdp-search.png`, `real-lg-cdp-details.png`, `real-lg-cdp-apps.png`, `real-lg-cdp-end_home.png`; skrypt `test_dc4i_keyhandler_real_tv.mjs` (wynik `REAL_LG_NATIVE_WEBOS_KEYHANDLER_ALL_TESTS_PASS`).

Nie było potrzeby wprowadzania nowych zmian kodu ani publikowania kolejnej wersji. Nadal obowiązuje **1.2.4**.
