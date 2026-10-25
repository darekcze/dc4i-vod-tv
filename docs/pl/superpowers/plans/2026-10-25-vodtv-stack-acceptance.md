# Audyt akceptacji #20–27 — tylko oprogramowanie offline

Kanoniczny plan to #17/#18–27 zgodnie z #28. Produkcja pozostaje1.2.19; żaden
PR nie jest tu scalany ani publikowany. Szczegółowe dowody i inwentarz czytników:
[pełny audyt EN](../../../superpowers/plans/2026-10-25-vodtv-stack-acceptance.md).

| Zakres | Wykonane i testowane offline | Niewykonane / bramki |
|---|---|---|
| #20 / PR31 | Syntetyczne XMLTV, mapowanie, pochodzenie, cache,10-dniowa oś, przewodnik/szczegóły/fokus | Prawa EPG.ovh, rzeczywiste pobieranie/dane, przeglądarka/TV |
| #21 / PR32 | Sekcje Home profilu, kolejność/stany/fokus, obsługa błędów zapisu | Rzeczywisty wygląd1920x1080, pilot/wydajność |
| #22 / PR33 | Kontrakt archiwum/transportu, granice i stany niezweryfikowane | Rzeczywiste archiwum, przewijanie/bufor dostawcy |
| #23 / PR34 | Harmonogram/quota/konflikty/odzyskanie/anulowanie w pamięci | Backend, nagranie, restart i odtworzenie; DVR niedostępny |
| #24 / PR35 | Pierwszy plan, cisza/DST/profile/błędy, zgodność danych, ścisły odczyt | Powiadomienia systemowe/tło/budzenie, webOS/fokus |
| #25 / PR36 | Cztery oficjalne linki tygodniowe, wybór/feedback/fokus | Licencjonowane źródło danych i zintegrowane rankingi, realne otwarcie |
| #26 / PR37 | Postęp lokalnego playera, granice sesji/profilu, ranking obu trybów Home | Rzeczywiste zdarzenia/ścieżki, filtr audio, dubbing, historia innych aplikacji |
| #27 / bieżący PR | Kopia ustawień i metadanych historii, bezpieczny diff, dziennik/cofanie po przerwaniu, migracja1→2, audyt/limity | Kopia sekretów/kont, globalna atomowość, migracja produkcji, TV/soak/wydanie |

Audyt obejmuje układ/cache Home, historię otwarć, ulubione/grupę/kanał przewodnika,
przypomnienia, rankingi, obserwacje odtwarzania i ogólne ustawienia profilu.
Brak klucza jest odróżniany od uszkodzenia/błędu odczytu. Błędne dane są chronione
przed automatycznym nadpisaniem; cache może być pominięty. Nie migrujemy kont,
playlist ani profili. Eksport nie zawiera historii, tytułów, kont czy sekretów.

Fixture powstaje z czystego commita, z zapisanym pochodzeniem i osobnym ID offline.
Weryfikacja: wszystkie nieprzeglądarkowe testy Node, Python XMLTV/provenance/Kodi,
struktura/składnia, CLI check i test przypomnień Europe/Warsaw. Dokładne SHA/liczby
w dowodach PR. Upstream8cdea8940355685a82aac127fcdcf113a30684f6,
brand883e38088ace6257d06999d71d22c95c1ce71516.

Cofanie draftów: nowy sprawdzony revert, bez resetowania cudzej pracy/main.
Cofnięcie importu jest sesyjne i wymaga niezmienionego profilu/wartości; skopiowany
tekst jest trwałą kopią dozwolonych ustawień. Rollback wydania musi użyć wcześniej
zweryfikowanego kompletu manifest/IPK, zachowując ID i dane. Nie wykonano go tutaj.

Pozostałe działania: niezależny przegląd; naprawa zaufanego sandboxa Chromium przez
opiekuna środowiska; rzeczywiste testy przeglądarki/pilota/pola tekstowego i soak;
uprawnione produkcyjne wejścia i prawa źródeł; osobne dowody dostawców/DVR. Testy
LG są nadal zabronione. Dostęp do wdrożenia niezweryfikowany, brak płatnych Actions.
Bez publikacji, dopóki odpowiednie bramki i dowody rollbacku nie zostaną spełnione.

Aktualizacja: v2 przywracania ma dozwolony dziennik metadataRestoreJournalV1,
syntetyczne testy przerwań/quota/konfliktów/zmian profilu oraz migrację schematu1→2.
Importowane obserwacje nie są dowodem natywnego odtwarzania. Web Locks wymagane;
bez gwarancji wobec obcych niewspółpracujących zapisów. Nie ma migracji produkcji.
Osobna diagnoza Chromium: SIGABRT i restrykcje sandbox/NoNewPrivs/seccomp. Oficjalny
Playwright1.62/Headless Shell151 rev1234 odmówiony HTTP403 Domain forbidden na
cdn.playwright.dev, bez instalacji i obejścia. Przeglądarka nadal jest bramką.
