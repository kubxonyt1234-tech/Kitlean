# Kitlean 0.1 Beta

Działający interpreter plików `.kit`, napisany w Pythonie 3.12+, z interfejsem tkinter dla Windows 10/11. Licencja MIT. Nie wymaga dodatkowych bibliotek do uruchamiania programów.

## Instalacja

Zainstaluj Python 3.12+ z komponentem Tcl/Tk. W PowerShell, w katalogu projektu:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\kitlean.exe --version
.\.venv\Scripts\kitlean.exe check examples/main_menu.kit
.\.venv\Scripts\kitlean.exe run examples/main_menu.kit
```

Możesz także uruchomić `./install.ps1`. Po aktywacji środowiska działa krótkie polecenie `kitlean`. Bez instalacji, z katalogu projektu: `python -m kitlean run examples/main_menu.kit`.

## Pierwszy program

```kitlean
[create gui.menu="menu"]
[create item.button="przycisk"]
przycisk.parent/"menu"
create item.button/"Kliknij Mnie"
if przycisk.clicked:
    print("Hello Kitlean!")
run gui.menu="menu"
```

Elementy otrzymują domyślne rozmiary i pionowy układ. Demonstracja ma ekran ustawień z powrotem do menu głównego. Szczegóły: [składnia](docs/syntax.md).

## Testy

```powershell
python -m pytest -q
python -m pytest -q -m gui
```

Testy oznaczone `gui` tworzą rzeczywiste okna i widgety Tk, wywołują zdarzenia, a następnie zamykają okna. Bez dostępnego pulpitu/Tk są oznaczane jako pominięte. Wynik wykonania w środowisku tworzenia: [raport](docs/verification.md).

## Architektura

Lexer oparty na tokenizacji, parser budujący AST instrukcji, ograniczony AST wyrażeń i własny interpreter. Nie używa `eval` ani `exec`. Runtime zarządza obiektami, kontekstem, właściwościami i zdarzeniami. GUI korzysta z jednego `Tk` i jednej głównej pętli; menu są przełączanymi ramkami.

## Ograniczenia wersji Beta

- `check` sprawdza składnię i dopuszczalne formy AST; błędy nazw, typów i właściwości wykrywane są podczas wykonania.
- Funkcje zwracają `null`; brak `return`, importów, klas, dostępu do plików i sieci oraz wykonywania kodu Pythona. Zmienne przypisane w funkcji są lokalne; odczyt korzysta z zakresu otaczającego.
- Zdarzenia rejestruje tylko samodzielny warunek `if nazwa.clicked:` lub `if nazwa.hovered:`; brak `else` dla zdarzeń.
- Obsługiwane elementy to menu, button, input, label i checkbox. Wartość input/checkbox odczytuje się przez `.value`. Treść input ustawia `.text` lub `.value`; aktualną zawartość odczytuje `.value`.
- Układ pionowy nie przewija zawartości; przy dużej liczbie elementów trzeba zwiększyć okno lub ustawić pozycje. Ręczne pozycje mogą się nakładać. Style zależą od systemu i DPI.
- Menu są ekranami jednego okna. `close.gui.menu` ukrywa aktywny ekran i okno; `open.gui.menu` pokazuje wybrany ekran; `close.app` zamyka GUI. Program kończy się po wykonaniu pozostałych instrukcji.
- Interpreter nie jest piaskownicą zasobów: długie pętle i duże wyrażenia mogą blokować aplikację. Handlery wykonują się w wątku Tk.
- Brak instalatora EXE i skojarzenia rozszerzenia `.kit`. Nie przeprowadzono osobnych testów na każdej wersji Windows 10/11.
