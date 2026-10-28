# Procedura zrzutów z telewizora LG

[English](../LG-TV-CAPTURE.md) | [Metoda dowodowa i natywne identyfikatory](LG-TV-EVIDENCE-METHOD.md)

## Zakres i stan weryfikacji

Narzędzia wykonywalne w `scripts/lg-tv/` służą do sprawdzenia istniejącego sparowania telewizora LG webOS, zbierania zrzutów menu, oceny rzeczywistej zawartości obrazów oraz tworzenia prywatnego atlasu interfejsów. Uruchamia się je na uprawnionym Macu mającym dostęp do sieci lokalnej telewizora.

Ścieżka zrzutów SSAP i identyfikacja aplikacji natywnych zostały sprawdzone na fizycznym LG OLED55G42LW 28.10.2026. Nie potwierdza to pełnego pokrycia sześciu menu w każdej aplikacji. Pakiet publiczny, jego konfiguracja wymagająca jawnego hosta oraz nowy wrapper sesji mają status **NIEZWERYFIKOWANE NA SPRZĘCIE**, dopóki nie przejdą własnego uprawnionego uruchomienia. Testy offline nie zmieniają tego statusu.

Jest to synchroniczny zestaw narzędzi lokalnych. Nie tworzy demona, harmonogramu, osobnej kolejki zadań ani zamiennika istniejących operacji AIOS projektu.

## Pliki utrzymywane w repozytorium

| Plik | Przeznaczenie |
| --- | --- |
| [lg_tv.py](../../scripts/lg-tv/lg_tv.py) | Istniejące parowanie, stan i lista aplikacji, uruchamianie, pilot, zrzuty, oceny wizualne, sesje i sprawdzone przepisy powtórzeń |
| [run_plan.py](../../scripts/lg-tv/run_plan.py) | Krótkie partie nawigacji wybrane na podstawie obserwacji, w już aktywnej sesji |
| [capture_session.py](../../scripts/lg-tv/capture_session.py) | Własna sesja, wykonanie dostarczonych planów i próba przywrócenia stanu w ścieżce sprzątania |
| [build_atlas.py](../../scripts/lg-tv/build_atlas.py) | Atlas HTML/Markdown, osobne strony aplikacji, tabela pokrycia i podsumowanie |
| [targets.json](../../scripts/lg-tv/targets.json) | Niepoufne nazwy aplikacji, stabilne slugi i zaobserwowane natywne ID |
| [tests](../../scripts/lg-tv/tests/) | Testy regresji offline ze sztucznymi urządzeniami i plikami tymczasowymi |

Repozytorium ignoruje `tools/`; utrzymywane źródła znajdują się w `scripts/lg-tv/`. Istniejący katalog `tools/` usługi pozostaje zależnością wykonawczą, a nie kanonicznym źródłem nowego zestawu.

## Wymagania i prywatna konfiguracja

Wymagany jest Python 3.9 lub nowszy na macOS, z bibliotekami standardowymi `zoneinfo` i `fcntl`. Należy użyć komputera już uprawnionego do sieci telewizora. Przez cały audyt steruje jeden kontroler, także wtedy, gdy dostępne są dwa Maki.

Istniejący katalog LGWebOSRemote musi zawierać:

- `.config/lgtv/config.json` z wybranym sparowanym profilem.
- `source/LGTV/payload.py` udostępniający istniejący manifest `hello_data`.
- `tools/lg_ssap_probe.py` udostępniający `WS` i `query`.

Repozytorium zawiera także [scripts/lg-ssap-probe.py](../../scripts/lg-ssap-probe.py). Aktywna usługa korzysta z kopii o nazwie z podkreśleniami. Nowy klient celowo zachowuje tę ustaloną zależność usługi. Sam świeży checkout repozytorium nie jest kompletnie skonfigurowanym kontrolerem telewizora. Nie kopiować danych uwierzytelniających do repozytorium, nie tworzyć automatycznie nowego sparowania i nie zastępować helpera podczas zbierania dowodów.

Skrypty publiczne nie mają domyślnego prywatnego adresu telewizora. Podać `--host` albo ustawić `LGTV_HOST` z prywatnej konfiguracji. Użyć `--device`, gdy istniejący profil różni się od domyślnej wskazówki modelu/profilu. `--root` można pominąć, jeśli istniejący katalog zostanie wykryty; przy kilku kopiach podać go jawnie.

Polecenia wykonywać z głównego katalogu repozytorium. Przygotować nowy prywatny katalog wyników:

```bash
CAPTURE_TOOLS="$PWD/scripts/lg-tv"
CAPTURE_ROOT='/path/to/existing/LGWebOSRemote'
CAPTURE_RUN="$PWD/private/lg-tv-captures/manual-001"
CAPTURE_SESSION="$CAPTURE_RUN/session.json"
: "${LGTV_HOST:?Ustaw LGTV_HOST lokalnie na podstawie prywatnej konfiguracji TV}"
python3 -B "$CAPTURE_TOOLS/lg_tv.py" --help
python3 -B "$CAPTURE_TOOLS/capture_session.py" --help
```

Katalog `CAPTURE_RUN` musi znajdować się w ignorowanym `private/` lub w innej potwierdzonej prywatnej lokalizacji poza publicznym checkoutem. Nie zapisywać go obok publicznych źródeł. Nie zmieniać przeznaczenia `HOME` ani `CODEX_HOME`.

## Wstępny odczyt stanu i lista aplikacji

```bash
python3 -B "$CAPTURE_TOOLS/lg_tv.py" --root "$CAPTURE_ROOT" --output "$CAPTURE_RUN" status
python3 -B "$CAPTURE_TOOLS/lg_tv.py" --root "$CAPTURE_ROOT" --output "$CAPTURE_RUN" apps
```

Te polecenia sprawdzają istniejące połączenie i odczytują aktualny stan oraz listę aplikacji, bez ich uruchamiania. Inwentarz jest zapisywany prywatnie w `installed-apps.json`. Przed uruchamianiem porównać z nim żądane aplikacje. Zapisany w repozytorium rejestr celów to datowana pomoc w rozpoznawaniu ID, a nie obietnica, że aplikacja nadal jest zainstalowana, ma te same menu albo przyjmuje deep link.

Sparowane połączenie TLS korzysta z istniejącej konfiguracji lokalnej. Przy błędach transportu zestawienie połączenia jest ponawiane najwyżej trzy razy. Jawne odrzucenie sparowania natychmiast kończy próbę. Błąd transportu po wysłaniu komendy zamyka socket bez ponownego wysłania komendy, ponieważ TV mógł już ją wykonać. Brak połączenia nie dowodzi uśpienia telewizora.

## Ręczna nawigacja oparta na obserwacji

Ten tryb służy do pracy, w której człowiek lub asystent ogląda zrzuty między krótkimi partiami. Rozpocząć sesję przed włączeniem obrazu lub zmianą aplikacji na pierwszym planie:

```bash
python3 -B "$CAPTURE_TOOLS/lg_tv.py" --root "$CAPTURE_ROOT" --output "$CAPTURE_RUN" begin --session "$CAPTURE_SESSION"
```

Potwierdzenie sesji zapisuje początkową aplikację i stan ekranu. `Screen Off` i `Screen Saver` mogą wymagać czasowego włączenia obrazu. Sam identyfikator aktywnej aplikacji nie dowodzi, że zrzut pokazuje jej interfejs.

Plan zawiera dokładne ID zainstalowanej aplikacji i od jednego do czterdziestu kroków wybranych na podstawie obserwacji:

```json
{
  "schema_version": 1,
  "app_slug": "disneyplus",
  "app_id": "com.disney.disneyplus-prod",
  "steps": [
    {"launch": "com.disney.disneyplus-prod", "wait": 12},
    {"capture": "home", "note": "Ekran wejściowy, oczekuje na ocenę wizualną."}
  ]
}
```

Zapisać JSON prywatnie jako `entry-plan.json`, następnie wykonać:

```bash
python3 -B "$CAPTURE_TOOLS/run_plan.py" --root "$CAPTURE_ROOT" --output "$CAPTURE_RUN" --session "$CAPTURE_SESSION" --plan "$CAPTURE_RUN/entry-plan.json"
```

Dozwolone kroki to `launch`, `keys`, `capture` albo samodzielny `wait`. Uruchomienie i klawisze mogą mieć ograniczone oczekiwanie `wait`; klawisze mogą ustawiać `interval`. Oczekiwanie jest ograniczone do 30 sekund. Nieznane pola, inny cel uruchomienia i nieobsługiwane przyciski są odrzucane. `--plan-json` jest alternatywą dla małych planów przekazywanych jako tekst JSON.

Runner wymaga tej samej aktywnej sesji i sprawdza aplikację przed wejściem z pilota. Dzieli partie po `HOME`, `BACK` i `ENTER`, po czym ponownie sprawdza aplikację przed dalszymi klawiszami. Chroni to wybór aplikacji, ale nie dowodzi położenia fokusu ani znaczenia zaznaczonej kontrolki. Przed wybraniem `ENTER` obejrzeć obraz. Nie stosować zgadywanych sekwencji w pobliżu odtwarzania, zakupów, subskrypcji, wylogowania, edycji profilu ani przełączników ustawień.

Uruchomienie może przywrócić poprzednią podstronę. Stałe opóźnienie nie dowodzi załadowania ekranu głównego. Nowe zrzuty mają status `unreviewed`, niezależnie od zamówionej nazwy pliku lub widoku.

Runner pozostawia odpowiedzialność za sesję kontrolerowi audytu. Zakończyć ją również po błędzie kroku:

```bash
python3 -B "$CAPTURE_TOOLS/lg_tv.py" --root "$CAPTURE_ROOT" --output "$CAPTURE_RUN" end --session "$CAPTURE_SESSION"
```

Sprawdzić status `restored` oraz końcowy stan ekranu i aplikacji. Przywracanie obejmuje pierwotną aplikację i zamiar włączenia lub wyłączenia obrazu. Nie odtwarza podmenu, fokusu, historii ani pozycji odtwarzania.

## Powtarzanie znanych planów z własnym sprzątaniem sesji

Dla wcześniej zaobserwowanego zestawu planów używać wrappera sesji. Sprawdza wszystkie plany przed operacjami na TV, rozpoczyna własną nową sesję i podejmuje próbę przywrócenia stanu w ścieżce sprzątania. Nie może przejmować istniejącej aktywnej sesji.

```bash
CAPTURE_PLAN="$CAPTURE_RUN/entry-plan.json"
CAPTURE_RUN="$PWD/private/lg-tv-captures/repeat-001"
CAPTURE_SESSION="$CAPTURE_RUN/session.json"
python3 -B "$CAPTURE_TOOLS/capture_session.py" --root "$CAPTURE_ROOT" --output "$CAPTURE_RUN" --session "$CAPTURE_SESSION" --plan "$CAPTURE_PLAN" --dry-run
python3 -B "$CAPTURE_TOOLS/capture_session.py" --root "$CAPTURE_ROOT" --output "$CAPTURE_RUN" --session "$CAPTURE_SESSION" --plan "$CAPTURE_PLAN"
```

Do każdego wykonania użyć nowego katalogu wyników i nowej ścieżki sesji. Istniejące potwierdzenie jest odrzucane także przy statusie `restored`. Powtórzyć `--plan` dla kolejnych planów. Dry run to wyłącznie lokalna walidacja, bez potwierdzenia połączenia i zachowania sprzętu. Plany są powtarzalnymi instrukcjami, a nie gwarancją deterministycznego UI: rekomendacje, aktualizacje aplikacji, ładowanie i zapamiętany fokus mogą zmienić wynik.

Osobny format `lg_tv.py flow` przyjmuje wyłącznie sprawdzone przepisy schema 1. Jego `--resume` odtwarza nawigację od początkowego uruchomienia i pomija tylko zapis istniejących zrzutów o zgodnych hashach. Nie wznawia pracy od dowolnego przycisku i nie potwierdza zawartości obrazu. Przed powtórzeniem komendy po timeout obejrzeć rzeczywisty stan UI.

## Ocena, zmiana klasyfikacji i atlas

Każdemu obrazowi towarzyszy JSON oraz dopisany rekord w `manifest.jsonl`. Zachować faktyczne ID aplikacji, zamówiony widok, czas ze strefą, wymiary, SHA-256, stan ekranu i jawny status wykonania zrzutu.

Stosować sześć kategorii oceny: `home`, `settings`, `details`, `recommendations`, `profiles` i `search`. Potwierdzać piksele, nie zamierzoną nawigację. Ekran ładowania lub bramka logowania nie są menu głównym. Aplikacja może łączyć kategorie; opisać relację faktycznie widoczną na obrazie.

Oceny wizualne to `verified`, `incorrect` i `blocked`. Rekord oceny może zawierać `verified_view`, aby po obejrzeniu poprawić pierwotnie zamówioną kategorię. Atlas stosuje tę korektę tylko przy ocenie verified i wartości należącej do sześciu dozwolonych widoków. Pierwotny manifest zrzutów pozostaje niezmieniony.

Statusy dostępności to `not-installed`, `login-required`, `not-available`, `not-observed` i `error`. Niepewność zapisać jako `not-observed`; nie uznawać menu za nieistniejące wyłącznie dlatego, że nie zostało odnalezione.

```bash
python3 -B "$CAPTURE_TOOLS/lg_tv.py" --output "$CAPTURE_RUN" review --capture-id CAPTURE_ID --status verified --verified-view profiles --note 'Obraz wejściowy pokazuje wybór profilu, a nie zamówiony widok home.'
python3 -B "$CAPTURE_TOOLS/lg_tv.py" --output "$CAPTURE_RUN" mark-status --app-slug example --view all --status login-required --note 'Zaobserwowana bramka logowania; pozostałe menu niedostępne.'
python3 -B "$CAPTURE_TOOLS/build_atlas.py" --input "$CAPTURE_RUN" --output "$CAPTURE_RUN/atlas" --apps "$CAPTURE_TOOLS/targets.json" --language pl
```

Użyć `--language en` albo `--language pl`, aby wybrać nagłówki atlasu, nazwy widoków i domyślne objaśnienia statusów. Obserwacje źródłowe zachowują oryginalną treść. Do pełnych raportów dwujęzycznych utrzymywać osobne prywatne pliki notatek i podawać `--notes "$CAPTURE_RUN/app-notes.en.json"` albo `--notes "$CAPTURE_RUN/app-notes.pl.json"`, z oddzielnymi katalogami wyników. CSV pokrycia zachowuje stabilne maszynowe kody statusów.

Dla mniejszego żądania podać odfiltrowaną listę celów konkretnego uruchomienia. Opcjonalny prywatny `app-notes.json` dodaje opisy, obserwacje i ograniczenia osobno dla każdej aplikacji. Publiczne podsumowania nie mogą zawierać identyfikatorów osób.

Atlas zawiera HTML, Markdown, osobne strony aplikacji, CSV pokrycia i podsumowanie maszynowe. Przed zgłoszeniem ukończenia otworzyć HTML i sprawdzić macierz. Liczba plików lub udanych uruchomień nie jest liczbą potwierdzonych widoków. Końcowe pokrycie menu należy do prywatnego raportu audytu; ta instrukcja nie deklaruje ukończenia audytu.

## Błędy, rollback i testy

Zatrzymać się przy niespodziewanej aplikacji, odrzuceniu sparowania, nieprawidłowej odpowiedzi zrzutu albo zmianie tożsamości sesji. Zapisać zaobserwowany błąd i sprawdzić stan. Nie resetować, nie parować ponownie, nie restartować ani nie budzić nieosiągalnego TV w ramach automatycznej naprawy.

Częściowe rozpoczęcie sesji podejmuje próbę przywrócenia stanu z własnego potwierdzenia. Nieudane przywrócenie pozostawia `needs_restore`; zachować plik i ponowić `end` dopiero po sprawdzeniu połączenia. Nie usuwać potwierdzenia, aby nowe uruchomienie pozornie wyglądało na czyste. Kończyć wyłącznie procesy należące do tego zadania.

Dodanie tych źródeł nie zmienia pakietu aplikacji ani usługi produkcyjnej. Rollback narzędzi polega na usunięciu lub cofnięciu nowych plików źródłowych. Sprzątanie operacyjne oznacza przywrócenie własnej sesji, a nie kasowanie dowodów.

```bash
python3 -B -m unittest discover -s scripts/lg-tv/tests -v
```

Testy korzystają ze sztucznych urządzeń i plików tymczasowych. Publiczny kod, plany bez prywatnych danych, instrukcje i ID aplikacji mogą być wersjonowane. Screenshoty, dane kont i profili, oryginalne inwentarze, pliki sparowania, manifesty uruchomień, logi akcji/sesji i atlasy z osadzonymi obrazami pozostają prywatne.
