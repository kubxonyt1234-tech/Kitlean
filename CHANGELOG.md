# Historia zmian

## 0.2.0b1 — 2026-10-19

- Nowe typy `gui/menu`, `item/button`, opcjonalne aliasy i tworzenie anonimowych elementów.
- Literały `$...$`, sekwencje ucieczki i interpolacja `{name}` jako osobne węzły AST.
- Reaktywne napisy z zależnościami od zakresu i zmiennej, bez przebudowy widgetów.
- `var/`, `run alias`, `open alias`, `close alias` i `run` dla bieżącego menu.
- Ochrona przed wielokrotną rejestracją tej samej deklaracji zdarzenia.
- Clicker napisany w `.kit`, zintegrowany test 101 kliknięć i przełączania ekranów.
- Zachowana starsza składnia; gołe wartości tekstowe są literalne. Zwykłe przypisanie w funkcji aktualizuje najbliższą istniejącą zmienną, a deklaracja `var/` pozostaje lokalna.
- Zaktualizowane przykłady, wersja CLI, dokumentacja i testy.

## 0.1.0b1 — 2026-10-19

Pierwsza wersja Beta: lexer, AST, parser i interpreter; zmienne, wyrażenia, warunki, pętle i funkcje; pięć typów obiektów GUI, automatyczny układ, właściwości i zdarzenia; jeden root Tk i przełączanie ekranów; CLI, przykłady, testy oraz polska dokumentacja.
