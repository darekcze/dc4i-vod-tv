# Instalacja i wydanie na Mac Pro
Kanoniczne źródło: `scripts/install-vodtv.sh`; wdrożona kopia: `/Volumes/AI-Hot/Services/LGWebOSRemote/install-vodtv.sh`. Pełny runbook i historyczne dowody: [wersja angielska](../INSTALLATION-AND-RELEASE.md). Używaj jednej procedury; nie twórz alternatywnych instalatorów.

Domyślnie tylko instalacja, bez wybudzania i uruchamiania. Nie odinstalowuj/resetuj; zachowaj com.dc4i.vodtv, playlisty, profile i historię. `--ipk /pełna/ścieżka.ipk --dry-run` sprawdza ID/wersję i checksum offline bez HOME. `--launch` wymaga osobnej zgody i po uruchomieniu sprawdza running. `--wake-if-needed` tylko przy jawnej zgodzie na wybudzenie.

SHA256 źródła i kopii przy synchronizacji: 74281565434b1365209de86ac2da1c7a7cf08719bb7a4b00bf23d4448766dcba. Kopii hosta nie nadpisano. Testy: `python3 scripts/test_installer_contract.py`; poprawki dry-run i running sprawdzono offline/atrapami, bez potwierdzenia nowego running na sprzęcie. Historyczny sukces instalacji 1.2.20 dotyczy zapisanej wcześniejszej rewizji.

Instalacja nadal wybiera prywatny profil przez HOME. Sesja zabraniająca tej operacji nie może jej wykonywać przez wrapper lub inną sesję. Pełny dostęp nie usuwa instrukcji sesji. Dry-run nie dowodzi instalacji.

Weryfikacja synchronizacji offline: 3 testy PASS (poprawne/błędne ID syntetycznej paczki, granica dry-run, atrapy running/brak/błąd zapytania); składnia Bash i diff-check PASS. Bez prawdziwego CLI, HOME i TV; syntetyczne paczki wyłącznie w tymczasowych katalogach testowych, nigdy do instalacji.
