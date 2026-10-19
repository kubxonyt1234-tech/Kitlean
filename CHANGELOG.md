# Historia zmian

## 0.3.0b1 — 2026-10-19

- Własny parser Pratt: dzielenie `:`, skrócone przypisania, funkcje math, NWW i NWD oraz KitleanMathError.
- Audio pygame: MP3/WAV/OGG, kanały bez nakładania, pause/resume/stop, volume i loop.
- Obrazki Pillow: PNG/JPEG/WebP, miniatury z zachowaniem proporcji.
- Trwałe dane JSON oddzielone ścieżką projektu, zapis atomowy i aktualizacja interpolacji po load.
- Planista kontynuacji na Tk.after: wait w blokach i funkcjach, timery z anulowaniem po zamknięciu.
- Klawiatura z ochroną przed autorepeat i skrótami w input.
- Odwołania domyślne według typu i kontekstu, z pierwszeństwem jawnych aliasów.
- START.bat instaluje lokalne środowisko i uruchamia Clickera 0.3; dołączone własne zasoby MIT i przykłady każdej funkcji.
- Zachowana starsza składnia, w tym / jako wyjątek zgodności. Zamknięcie anuluje zadania (także instrukcje po run).

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
