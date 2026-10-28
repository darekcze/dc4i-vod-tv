# Powtarzanie zrzutów wejściowych aplikacji streamingowych

[English](README.md)

Ten wersjonowany zestaw szybko uruchamia wybrane zainstalowane aplikacje i zapisuje po jednym wejściowym punkcie kontrolnym, korzystając z kanonicznego `capture_session.py`. Zawiera 19 dokładnych mapowań aplikacji i osobny plan dla każdej z nich.

**Punkt kontrolny po wejściu nie jest potwierdzonym menu głównym.** Może pokazywać wybór profilu, bramkę logowania, ładowanie, błąd albo przywróconą podstronę. Plan zamawia kategorię `home` jako początkową etykietę; obraz pozostaje `unreviewed`, dopóki nie zostanie obejrzany. Potwierdzona ocena, a w razie potrzeby `--verified-view`, służy do zapisania rzeczywiście widocznej kategorii.

Zestaw nie zbiera automatycznie wszystkich sześciu rodzajów menu. Pełna dokumentacja home/settings/details/recommendations/profiles/search nadal wymaga zainstalowanego skilla, nawigacji opartej na obserwacji i oceny obrazów. Nie zawiera danych uwierzytelniających i nie tworzy sparowania.

## Wymagania i pliki

Użyć istniejącego skonfigurowanego kontrolera TV, Pythona 3.9 lub nowszego oraz zgodnego katalogu kanonicznego zawierającego `capture_session.py`, `lg_tv.py` i `run_plan.py`. Wrapper zachowuje dotychczasowe zależności parowania i helperów.

- `repeat_streaming_entries.py`: cienki launcher bez własnego klienta TV.
- `targets.json`: dokładny rejestr 19 aplikacji z zaobserwowanego inwentarza.
- `plans/<slug>.json`: uruchomienie, 12 sekund oczekiwania i zrzut wejściowego punktu kontrolnego wymagającego oceny.

Wygenerowane dowody przechowywać w ignorowanym `private/` albo innej potwierdzonej prywatnej lokalizacji poza repozytorium. Źródła i niepoufne plany aplikacji mogą być wersjonowane. Sterować TV tylko jednym kontrolerem. Przed powtórzeniem sprawdzić aktualny inwentarz; datowane mapowanie ID nie dowodzi bieżącej dostępności.

## Podgląd bez kontaktu z telewizorem

Domyślne `--tools` to `../scripts/lg-tv` względem tego zestawu. Przy innym układzie podać ścieżkę jawnie. Przykłady wykonywać z katalogu `lg-tv-repeat-kit` albo wywoływać launcher pełną ścieżką. Konfigurację i ocenę opisuje [procedura zrzutów](../docs/pl/LG-TV-CAPTURE.md).

```bash
python3 -B repeat_streaming_entries.py \
  --tools /path/to/dc4i-vod-tv/scripts/lg-tv \
  --output /private/path/entry-check-001 \
  --apps disneyplus,netflix \
  --dry-run
```

Launcher przekazuje `--dry-run` do wrappera, który sprawdza wybrane plany bez odczytu konfiguracji sparowania, kontaktu z TV i tworzenia wyników lub sesji. Dry run nie potwierdza gotowości sprzętu. Pominąć `--apps`, aby sprawdzić wszystkie 19 planów.

## Nowe zbieranie zrzutów

Ustawić lokalnie `LGTV_HOST` z prywatnej konfiguracji albo podać `--host`. Do każdego wykonania użyć nowej ścieżki wyników, także po pomyślnie przywróconej sesji.

```bash
python3 -B repeat_streaming_entries.py \
  --tools /path/to/dc4i-vod-tv/scripts/lg-tv \
  --root /path/to/existing/LGWebOSRemote \
  --device LG_OLED55G42LW \
  --output /private/path/entry-check-001 \
  --apps disneyplus,netflix
```

Pominąć `--root` tylko wtedy, gdy wrapper może wykryć właściwą istniejącą konfigurację. Pominąć `--apps`, aby uruchomić wszystkie aplikacje. Dostępne dokładne slugi:

`disneyplus,netflix,hbomax,appletv,player,stremio,iptvsmartersplayer,smartiptv,primevideo,youtube,viki,pilot,skyshowtime,canalplus,megogo,cda,sweettv,rakutentv,lgchannels`

Launcher odrzuca nieznane i powtórzone slugi oraz istniejące katalogi wyników. Rezerwuje nowy katalog i uruchamia wrapper z nowym `RUN/session.json` oraz powtarzanymi argumentami `--plan`. Nie przejmuje starej sesji i nie ponawia nieudanych mutacji. Wrapper odpowiada za przywracanie oraz zachowuje kontrole tożsamości sesji, aktywnej aplikacji, blokadę lokalną i zasady sprzątania.

## Ocena i ponowienie

Obejrzeć obrazy i podsumowanie wrappera w `session-runs/`. Potwierdzić, że receipt sesji wskazuje przywrócenie. Udany zapis pliku nie dowodzi uzyskania zamierzonego menu, a 12 sekund może nie wystarczyć do załadowania aplikacji.

Jeżeli plan zawiedzie, wrapper przerywa zbieranie i próbuje przywrócić własną sesję. Zachować nieudane uruchomienie i przed ponowieniem sprawdzić rzeczywisty stan TV oraz receipt. Użyć nowego katalogu wyników i `--apps` dla wybranego podzbioru. Nie omijać stanu `needs_restore` ani zmiany tożsamości sesji.

Pierwotny manifest zrzutów pozostaje niezmieniony. Oceny zapisać poleceniem `review` kanonicznego klienta, następnie utworzyć prywatny atlas przez `build_atlas.py`. W razie potrzeby użyć `--language en` albo `--language pl` i notatek w odpowiednim języku.

28.10.2026 uprawnione wykonanie publicznego klienta i `run_plan.py` na fizycznym TV, z jawnym `--host`, zakończyło sześć kroków: trzy osobne partie przycisków przeplatane trzema zrzutami i kontrolami aktywnej aplikacji. Sprawdza to ciągłość wejścia między wywołaniami; nie jest ogólnym benchmarkiem wydajności. W tym uruchomieniu nie mierzono liczby fizycznych połączeń; testy offline sprawdzają ponowne użycie jednego połączenia pilota.

Osobny rzeczywisty transfer obrazu powiódł się również przy drugim GET tego samego URI i zapisał `download_attempts: 2` wraz z prawidłowym obrazem. Potwierdza to zaobserwowaną ścieżkę odzyskania transferu, a nie zamierzoną kategorię menu.

Wrapper własnej sesji `capture_session.py` i launcher zestawu powtórek nadal mają status **NIEZWERYFIKOWANE NA SPRZĘCIE**. Dry run 19 planów wejściowych sprawdził 38 kroków bez kontaktu z TV i tworzenia plików. Zebranie pełnych sześciu widoków nadal wymaga nawigacji opartej na obserwacji i oceny obrazów.
