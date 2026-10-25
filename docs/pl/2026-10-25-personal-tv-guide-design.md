# DC4I VOD TV, plan rozwoju osobistego przewodnika

Data 25.10.2026. Architektura: lokalne playlisty, profile, historia i ranking na telewizorze LG, publiczny cache metadanych EPG bez loginów Xtream. Mac Pro nie jest wymagany.

## Kolejne wydania
| Wersja | Rezultat |
| --- | --- |
| 1.2.18 | Preferencje gatunków, progi ocen, ignorowanie horrorów, wieczorny bonus, historia otwierania i polecane per profil na Home |
| 1.2.19 | Grupy kanałów, logotypy, ulubione, program aktualny/następny, sterowanie pilotem jak w TiViMate |
| 1.2.20 | EPG.ovh + Xtream, identyfikatory kanałów, rok/gatunek/ocena, oś czasu; weryfikacja ścieżek audio i napisów |
| 1.2.21 | Konfigurowana strona główna: obecnie w TV, nadchodzące dzień/tydzień, przegapione, filmy, seriale, gatunki |
| 1.2.22 | CatchUp i Timeshift tylko po pozytywnych testach i zgodności odtwarzacza |
| 1.2.23 | Opcjonalny DVR, nagrywanie, limity pamięci, terminy i konflikty |
| 1.2.24 | Notyfikacje, przypomnienia, test tła i uprawnień LG |
| 1.2.25 | Zweryfikowane Top 10, konfiguracja źródeł i API, jasna atrybucja |
| 1.2.26 | Uczenie gustu z potwierdzonego odtwarzania, pory dnia, języki oraz audio/napisy |
| 1.2.27 | Stabilność, eksport/import preferencji, testy wydajności i wydania |

## Zasady
- Jeden tytuł i wiele rzeczywistych źródeł, osobne oceny TMDB i EPG.
- Samo kliknięcie lub wyszukanie nie jest ukończeniem oglądania, nie znamy automatycznie historii Netflix.
- Próg Sci-Fi 6, horror 9 i opcjonalny zakaz horrorów, plus bonus dla romantycznych/familijnych wieczorem. Progi i reguły dostępne w Ustawieniach.
- Polska jako kraj nie gwarantuje polskiego dubbingu, lektora ani napisów; [PL] jest tylko oznaczeniem dostawcy.
- EPG.ovh nie wysyła CORS umożliwiającego pobranie z aplikacji LG, więc neutralny cache metadanych, bez przekazywania haseł.
- Wersja 1.2.18 zawiera osobną listę polecanych na Home oraz ustawienia per profil. Pełne EPG, nagrania, Top 10 i rzeczywista historia innych aplikacji są w późniejszych wydaniach.
- Każde wydanie przechodzi testy, Release Notes PL/EN, GitHub, lg.darc.dev, LG i ma możliwość cofnięcia. Zachować logo, dedykację i istniejące playlisty.
