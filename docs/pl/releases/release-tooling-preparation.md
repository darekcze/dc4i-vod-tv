# Przygotowanie narzędzi wydania — bez publikacji

Oddzielna gałąź od b8a4c08. Rzeczywiste QA Chrome156:26 kontroli PASS,
1920x1080, podgląd y624–1056, wysokość432, przewinięcie1746/1746;
pilot/PL/EN/transakcje/prywatność/Home/EPG. Bez deklaracji testu LG.
Kod interfejsu pozostaje bez zmian.

Publisher i test dymny odczytują ID/wersję z appinfo.json. Dozwolony wyłącznie
com.dc4i.vodtv i wersja numeryczna X.Y.Z; fixture odrzucony. --release-version
musi zgadzać się z metadanymi. Brak wybranej nowej wersji;1.2.19 bez zmian.
Zmiana wersji aplikacji nadal wymaga osobnego spójnego commita wydania.

--root wybiera izolowane wejście; --output-root pusty katalog obok źródeł.
Jawny output nie może być źródłem, jego rodzicem/potomkiem ani niepustym
katalogiem. Bez parametru zachowane stare zapisy publishera w repozytorium.
Izolowane staging nie uruchamia opcjonalnych starych etapów wzbogacania katalogu.
--offline w smoke pomija tylko rzeczywistą prośbę TMDB; inne walidacje pozostają.
Wyjątki sieciowe wypisują jedynie klasę, bez treści/URL/nagłówków/sekretów.

3 przypadki Python PASS i py_compile. Dane wyłącznie syntetyczne:33 wpisy,
32 niezwiązane zachowane, źródło bez zmian, błędne wersje/ścieżki odrzucone.
Brak prawdziwych kluczy, kandydata IPK, API, merge, wdrożenia i kontaktu z TV.
Szczegółowe komendy i ograniczenia w angielskim odpowiedniku.
