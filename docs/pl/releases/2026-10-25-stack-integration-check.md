# Połączenie stosu z PR40

Baza e307dbc, poprawka PR40 e832b39; sprawdzony kod d2121f0.
Oba commity połączono bez konfliktów na osobnej gałęzi. Oś programu korzysta
z już pobranych danych dostawcy, gdy brakuje XMLTV, z limitami i opisem źródła.
Bez nowych wywołań sieciowych.

56 poleceń zaliczonych:50 testów Node,14 przypadków Python, struktura i składnia
42 plików JS, CLI check oraz przypomnienia Europe/Warsaw. Zbudowano fixture
bez sekretów, korzystając z istniejących zależności. Początkowy brak katalogu
wynikowego naprawiono. Późniejszy commit dokumentacji nie zmienia kodu.

Nie wykonano testów przeglądarkowych/TV/dostawcy ani publikacji. QA na Mac mini
jest zatrzymane;14 wcześniejszych testów źródłowych nie oznacza uruchomienia
fixture. Następny krok: istniejący autoryzowany Chrome na Mac mini, odizolowany
checkout, przypięte źródło brand i istniejący CLI, build i testy syntetyczne.
Bez obchodzenia sandboxa, ponawiania zabronionego pobrania i kontaktu z LG.
Produkcja pozostaje1.2.19; szczegółowe SHA i dowody w angielskim odpowiedniku.
