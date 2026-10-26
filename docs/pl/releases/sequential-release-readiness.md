# Kolejne wydania — plan, bez publikacji

Najmniejszy kandydat1.2.20: PR31+PR40, bez późniejszych Home/DVR/backup, z
poprawionymi narzędziami wydania na codex/v1220-release-preparation. Pełne UI
b8a4c08 pozostaje bez zmian. Wynik pełnego stosu nie zastępuje testu podzbioru.

1.2.20: przewodnik/oś EPG i fallback już pobranych danych Xtream; publiczny cache
EPG.ovh wyłączony, prawa źródeł niepotwierdzone. 1.2.21: sekcje Home/profil/fokus.
1.2.22: kontrakt archiwum bez dowodu prawdziwego CatchUp. 1.2.23: model DVR bez
backendu/nagrania/odtworzenia — nie wolno deklarować działającego DVR.
1.2.24: przypomnienia tylko na pierwszym planie. 1.2.25: oficjalne linki tygodniowe,
nie feed rankingów. 1.2.26: uczenie z obserwowanego postępu, brak dowodów rzeczywistych
ścieżek audio i pełnego filtra dubbingu. 1.2.27: backup metadanych/journal/przewijany
podgląd;26 kontroli przeglądarkowych PASS, bez dowodu migracji produkcji/soak.
Szczegółowa tabela i bramki w angielskim odpowiedniku.

TMDB jest czytane z window.KEYS, nie z konfiguracji użytkownika. Builder wymaga
keys.js i kopiuje go do IPK; bez klucza katalog przestaje się ładować. Usunięcie go
nie jest poprawnym gotowym wydaniem. Nie pobrano sekretów i nie zbudowano IPK.

Następny krok po świadomej decyzji o dystrybucji klucza: zaufany lokalny build
minimalnego źródła, osobna spójna zmiana metadanych1.2.20, testy podzbioru/pakietu,
staging i porównanie32 pozostałych aplikacji oraz plików. Lokalny task odpowiada
za autoryzowane TV. Root decyduje o scaleniu/publikacji. Nic nie wdrożono tutaj.
