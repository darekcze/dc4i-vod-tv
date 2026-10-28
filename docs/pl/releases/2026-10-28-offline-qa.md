# DC4I VOD TV: powtarzalne testy offline (28.10.2026)

Zadanie nadrzędne: #17. Testowany commit aplikacji: daea1ea0c50bca415e2e738df08ee2f491698f98 ze stosu PR #43. Runner nie zmienia kodu telewizyjnego.

## Zweryfikowane wyniki

- Pierwsza próba czystego katalogu: 39 PASS, 17 FAIL. Wszystkie błędy wynikały z braku wygenerowanego build/dc4i-vodtv, nie z potwierdzonej usterki aplikacji.
- Po użyciu istniejącej, syntetycznej i zweryfikowanej wersją Git paczki testowej: **56 PASS, 0 FAIL**.
- Zakres: 50 zestawów Node.js, XMLTV, pochodzenie danych, Kodi, narzędzia wydaniowe, kompilacja offline, przypomnienia w strefie Warszawa.
- Raport: Services/QA-Workspaces/vodtv-audit-20261028-complete.json na AI-Hot Mac mini.
- Bez kontaktu z fizycznym LG, dostawcą IPTV, prawdziwymi kluczami API i bez publikacji.

## Powtarzalny test

Potrzebny jest istniejący zestaw z OFFLINE_FIXTURE_ONLY.txt, fixture-provenance.json i identyfikatorem aplikacji com.dc4i.vodtv.offlinefixture.

    python3 scripts/test_fullstack_offline_qa.py
    python3 scripts/run_fullstack_offline_qa.py \
      --fixture /Volumes/AI-Hot/Services/QA-Workspaces/DC4I-VOD-FIXTURES-20261026/vod-OFFLINE-DO-NOT-PUBLISH-0a21vtw5 \
      --scratch-root /Volumes/AI-Hot/Services/QA-Workspaces \
      --receipt /Volumes/AI-Hot/Services/QA-Workspaces/vodtv-offline-qa-next-unique-run.json

Przy kolejnym uruchomieniu podaj nową nazwę raportu. Narzędzie odmawia testu niezgodnego źródła, rzeczywistego identyfikatora pakietu albo nadpisania raportu. Tworzy izolowaną kopię na AI-Hot, usuwa katalog tymczasowy i zapisuje skrócony dowód wykonania. Po zmianie aplikacji trzeba ponownie utworzyć zestaw offline.

## Otwarta ścieżka wydania

- #4: niepotwierdzone prawa do komercyjnego wykorzystania kodu upstream TheBoringTV.
- #29: użytkownik wcześniej wyraźnie odroczył testy na fizycznym LG.
- Nadal konieczne są: polityka dystrybucji kluczy, finalne numerowanie wersji, kontrola IPK i zachowanie danych przy instalacji.
- Lokalny wynik 56/56 nie oznacza zaliczenia testów produkcyjnych ani publikacji.

English: docs/releases/2026-10-28-offline-qa.md.
