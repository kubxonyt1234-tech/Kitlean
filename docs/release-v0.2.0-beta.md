# Kitlean v0.2.0-beta

Aktualizacja istniejącego Kitlean 0.1 Beta.

## Co nowego

- Składnia `/`: `[create gui/menu="game"]`, `var/points = 0`, `run game`, `open game`, `close game`.
- Tworzenie bez aliasów: `create gui/menu`, `create item/button/KLIKNIJ!`.
- Tekst `$...$` z polskimi znakami, interpunkcją, ucieczkami i interpolacją `{points}`.
- Automatyczne odświeżanie tekstu po zmianie zmiennych, bez tworzenia okna i widgetów od nowa.
- Deduplikacja tej samej deklaracji zdarzenia; jedno kliknięcie Clickera daje jeden punkt.
- Gra `examples/clicker.kit`, napisana w całości w Kitlean.

## Uruchomienie

Wymagany Python 3.12+ z tkinter. Pobierz kod, uruchom `install.ps1`, następnie:

```powershell
.\.venv\Scripts\kitlean.exe run examples/clicker.kit
```

Istniejącą instalację aktualizuje ponowne `pip install -e .` w używanym środowisku.

## Weryfikacja

62 testy języka/CLI i 6 testów prawdziwego GUI zaliczone. Testy GUI uruchomiono w osobnych procesach z powodu problemów wielokrotnej inicjalizacji lokalnego Tcl/Tk. Clicker: 100 kliknięć → 100 punktów, po przełączeniu ekranów następne kliknięcie → 101; te same widgety i jedna rejestracja zdarzenia. Pełny raport: `docs/verification.md`.

## Zgodność i ograniczenia

Starsze polecenia 0.1 są obsługiwane. Nowe `create item/button/tekst` tworzy element; stare `create item.button/"tekst"` zmienia tekst ostatniego elementu. Goły tekst jest literalny; wartość zmiennej pokazuje `{name}` wewnątrz `$...$`. Zwykłe przypisanie z funkcji aktualizuje najbliższy istniejący zakres; `var/` deklaruje lokalnie.

To wersja Beta: interpolacja przyjmuje nazwy, bez wyrażeń; reaktywne są bezpośrednie szablony właściwości GUI. Brak przewijania układu, instalatora EXE, globalnego PATH i testów na wszystkich wariantach Windows/DPI. Długie pętle mogą blokować Tk. Szczegóły w README i docs/syntax.md.
