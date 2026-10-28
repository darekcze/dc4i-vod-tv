# Metoda dokumentowania menu telewizora LG

[English](../LG-TV-EVIDENCE-METHOD.md) | [Wykonywalna procedura zrzutów](LG-TV-CAPTURE.md)

## Co potwierdzają zebrane dowody

28.10.2026 istniejące sparowane połączenie SSAP z fizycznym LG OLED55G42LW zwróciło zrzut menu przez `ssap://tv/executeOneShot`. Zaobserwowany obraz miał format JPEG i wymiary 960 × 540 pikseli. Odczytano także listę zainstalowanych aplikacji i ustalono poniższe 19 natywnych ID z zakresu żądania. Te obserwacje potwierdzają dostępność ścieżki zrzutów i identyfikatorów na tym urządzeniu w danym momencie. Nie potwierdzają pełnego pokrycia menu, deep linków, odtwarzania ani bezpieczeństwa ponownego wykonania zapamiętanej sekwencji przycisków.

Oryginalne obrazy, inwentarz, czasy i potwierdzenia zrzutów są prywatnymi dowodami projektu. Ten publiczny dokument zapisuje metodę i niepoufne mapowanie aplikacji. Nie zawiera końcowej deklaracji liczby potwierdzonych menu w trwającym audycie. Nowe skrypty publiczne i wrapper własnej sesji mają status **NIEZWERYFIKOWANE NA SPRZĘCIE**, dopóki nie przejdą własnego uprawnionego uruchomienia.

## Zaobserwowane natywne identyfikatory

Przed uruchomieniem ponownie sprawdzić aktualny inwentarz TV. Nazwy mogą się zmieniać, a ID zainstalowanej aplikacji nie gwarantuje jego dostępności na innym urządzeniu. Wersjonowany [rejestr celów](../../scripts/lg-tv/targets.json) używa takich samych slugów jak rekordy zrzutów.

| Slug | Zaobserwowana nazwa | Natywne ID |
| --- | --- | --- |
| `disneyplus` | Disney+ | `com.disney.disneyplus-prod` |
| `netflix` | Netflix | `netflix` |
| `hbomax` | HBO Max | `com.wbd.stream` |
| `appletv` | Apple TV | `com.apple.appletv` |
| `player` | Player | `com.accedo.videa.tvn` |
| `stremio` | Stremio | `io.strem.tv` |
| `iptvsmartersplayer` | IPTV Smarters Player | `com.smarterstvplayers.net` |
| `smartiptv` | Smart IPTV | `siptv` |
| `primevideo` | Prime Video | `amazon` |
| `youtube` | YouTube AdFree | `youtube.leanback.v4` |
| `viki` | Rakuten Viki | `com.viki.lg` |
| `pilot` | WP Pilot | `pl.wp.pilot` |
| `skyshowtime` | SkyShowtime | `com.skyshowtime.tv` |
| `canalplus` | CANAL+ | `canalplus` |
| `megogo` | MEGOGO | `megogo.hd` |
| `cda` | CDA | `pl.cda` |
| `sweettv` | SWEET.TV | `sweet.tv` |
| `rakutentv` | Rakuten TV | `ui30` |
| `lgchannels` | LG Channels | `com.webos.app.lgchannels` |

Zaobserwowana nazwa YouTube to **YouTube AdFree**. Jest to zapis wyświetlanej etykiety i ID; nie potwierdza wydawcy, oficjalnego statusu, zasad subskrypcji ani funkcji odtwarzania.

## Sześć widoków na każdą żądaną aplikację

| Widok | Potrzebny dowód |
| --- | --- |
| `home` | Faktyczna główna strona wejściowa lub nawigacyjna |
| `settings` | Widoczne menu ustawień aplikacji, bez zmiany ustawienia |
| `details` | Szczegóły jednego określonego tytułu, bez uruchamiania odtwarzania ani zakupu |
| `recommendations` | Strona rekomendacji lub jednoznacznie rozpoznawalna sekcja rekomendacji |
| `profiles` | Wybór profilu lub menu profilu, bez jego edycji |
| `search` | Ekran wejściowy wyszukiwania albo interfejs wyszukiwania |

Bramka logowania, ładowanie, błąd i nakładka systemowa są dowodem danego stanu. Nie zastępują żądanego menu. Jeżeli ekran widocznie łączy kategorie, opisać relację i jawnie wskazać ten sam dowód; nie kopiować pliku, aby sugerować większą liczbę niezależnych zrzutów.

## Procedura zbierania i oceny

1. Odczytać aktualną aplikację i stan ekranu oraz utworzyć potwierdzenie własnej sesji przed zmianą TV.
2. Ustalić dokładne ID aplikacji z aktualnego inwentarza. Uruchomić wyłącznie żądaną aplikację i obejrzeć obraz wejściowy. Aplikacja może przywrócić wcześniejszą podstronę.
3. Wybierać krótkie kroki nawigacji na podstawie widocznego fokusu. Runner sprawdza tożsamość sesji i aktywną aplikację przed wejściem. Dzieli partie po `HOME`, `BACK` lub `ENTER` i sprawdza ponownie przed dalszymi przyciskami. Kontrole te nie ustalają znaczenia naciśnięcia `ENTER`.
4. Wymagać `returnValue: true` i adresu obrazu w odpowiedzi zrzutu. Pobierać wyłącznie ze skonfigurowanego lokalnego hosta TV, sprawdzać przekierowania, limity, sygnaturę i wymiary obrazu.
5. Zapisywać zamówiony widok, rzeczywiste ID aplikacji, stan ekranu, czas ze strefą, SHA-256, wymiary i kroki nawigacji. Pierwotny manifest uzupełniać bez zmiany wcześniejszych wpisów.
6. Obejrzeć rzeczywisty obraz. Zapisać `verified`, `incorrect` lub `blocked` w osobnym dzienniku ocen. Potwierdzona korekta `verified_view` może nadać zaobserwowaną kategorię, zachowując surowe żądanie.
7. Zapisywać niedostępne i nierozstrzygnięte widoki jako `not-installed`, `login-required`, `not-available`, `not-observed` lub `error`, z konkretną obserwacją. Nieudane szukanie menu oznacza jedynie `not-observed`.
8. Przywrócić pierwotną aplikację i zamiar dotyczący obrazu w ścieżce sprzątania kontrolera będącego właścicielem sesji. Błąd przywracania zapisać osobno od sukcesu zrzutu.

Pierwsze próby ujawniły istotne rozróżnienie: poprawne ID aktywnej aplikacji mogło współistnieć z nakładką wyłączonego obrazu lub wygaszacza. Czasowe włączenie panelu dało obraz aplikacji, po czym odtworzono wcześniejszy zamiar wyłączenia ekranu. Zawsze sprawdzać piksele i stan aplikacji. Sam czarny obraz nie wskazuje DRM jako przyczyny.

## Co można publikować

Dane uwierzytelniające, prywatne adresy, stabilne ID komputerów, dane profili i kont, screenshoty, oryginalne inwentarze, surowe manifesty, logi akcji i sesji oraz atlasy z osadzonymi obrazami pozostają poza tym publicznym repozytorium. Ignorowany katalog `private/` może przechowywać lokalne dowody robocze; nie jest kopią zapasową ani mechanizmem kontroli dostępu.

Wersjonować kod do powtórnego użytku, te instrukcje w obu językach, niepoufne ID aplikacji oraz odpowiednio oczyszczone wnioski. Pokrycie menu podawać wyłącznie na podstawie ocenionych obrazów w datowanym prywatnym raporcie. Oddzielać obserwacje od rekomendacji projektowych dla DC4I VOD TV.
