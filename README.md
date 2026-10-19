# Kitlean 0.2 Beta

Prosty język programowania z własną składnią i prawdziwym GUI tkinter. Aktualizacja istniejącego Kitlean 0.1 Beta. Python 3.12+, Windows 10/11, licencja MIT.

## Pobranie i uruchomienie

Pobierz ZIP z repozytorium, rozpakuj i otwórz PowerShell w folderze zawierającym `install.ps1`. Wymagany Python 3.12 z Tcl/Tk.

```powershell
./install.ps1
.\.venv\Scripts\kitlean.exe --version
.\.venv\Scripts\kitlean.exe run examples/clicker.kit
```

Jeżeli korzystasz z istniejącego środowiska, po pobraniu nowego kodu uruchom ponownie `install.ps1` albo `.\.venv\Scripts\python.exe -m pip install -e .`.

Instalacja ręczna:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
```

Po aktywacji środowiska przez `.\.venv\Scripts\Activate.ps1` działa polecenie `kitlean`. Bez instalacji, z folderu projektu: `python -m kitlean run examples/clicker.kit`. Nie zmieniamy systemowego PATH.

## Pierwsza gra: Clicker

```kitlean
[create gui/menu="game"]
game.title/$Kitlean Clicker$
var/points = 0
[create item/label="counter"]
counter.text/$Punkty: {points}$
[create item/button="click"]
click.text/KLIKNIJ!
if click.clicked:
    points = points + 1
run game
```

Otwiera okno 800×500 z licznikiem i przyciskiem. Każde kliknięcie dodaje jeden punkt. Napis automatycznie śledzi zmienną, a jego szablon pozostaje zapisany w runtime. Nie ma sklepu, ulepszeń ani zaprogramowanego limitu punktów.

Wersja bez aliasów:

```kitlean
create gui/menu
create item/button/$Kliknij mnie!$
run
```

Każde `create item/button/tekst` tworzy nowy przycisk. Alias jest nazwą w kodzie, nie podpisem elementu. Pełna [składnia](docs/syntax.md), [historia zmian](CHANGELOG.md) i [raport testów](docs/verification.md).

## CLI

```powershell
kitlean --version
kitlean run examples/clicker.kit
kitlean check examples/clicker.kit
kitlean help
```

Wersja CLI:

```text
Kitlean 0.2 Beta
Python-powered programming language
```

`check` sprawdza składnię bez uruchamiania programu. Błędy nazw, wartości i brakujących zmiennych w interpolacji są wykrywane podczas wykonania.

## Zgodność z 0.1

Działają `[create gui.menu="menu"]`, `[create item.button="b"]`, `b.text/"Kliknij"`, `var points = 0`, `run gui.menu="menu"`, `open.gui.menu("menu")`, `close.gui.menu("menu")`. Stare `create item.button/"tekst"` ustawia tekst ostatniego przycisku; nowe `create item/button/tekst` tworzy kolejny element.

Tekst bez delimitera oznacza dosłowny napis. Aby pokazać wartość zmiennej, użyj `$Wartość: {name}$`. Stare cytowane literały i wyrażenia zaczynające się od literału lub wywołania funkcji pozostają obsługiwane.

## Testowanie

```powershell
python -m pytest -q
```

Testy `gui` wymagają tkinter i pulpitu. Tworzą rzeczywiste widgety i sprawdzają zdarzenia oraz pętlę aplikacji. Bez dostępnego Tk są pomijane. W środowisku tworzenia testy GUI uruchomiono osobno w świeżych procesach — szczegóły w raporcie.

## Architektura i ograniczenia Beta

Lexer rozpoznaje literały `$...$`, parser tworzy AST, a interpreter wykonuje dozwolone węzły. Nie korzysta z `eval()` ani `exec()`. Rejestr zależności `(zakres, nazwa zmiennej)` aktualizuje tylko powiązane napisy. Aktualizacja tekstu używa istniejącego widgetu i przelicza układ jego rodzica, bez ponownego tworzenia GUI i callbacków.

- Interpolacja przyjmuje nazwy `{points}`, bez wyrażeń `{points + 1}`. Reaktywny szablon musi być bezpośrednią wartością `.text`, `.title` lub tekstowego `.value`. Tekst obliczony w zmiennej lub `print` jest jednorazowym wynikiem.
- Teksty `$...$` mieszczą się w jednej linii źródła; znak nowej linii zapisuje `\n`. Tekst z odstępami wymaga `$...$` (stare cudzysłowy są obsługiwane dla zgodności).
- Funkcje zwracają `null`; brak `return`, importów, klas i API plików/sieci. `var/` deklaruje lokalnie; zwykłe przypisanie zmienia najbliższą istniejącą zmienną, a jeśli jej nie ma, tworzy lokalną.
- Jedno okno i przełączane ekrany, bez przewijania automatycznego układu. Ręczne pozycje mogą się nakładać. Właściwości position/visible/disabled menu pozostają metadanymi — ekranami sterują open/close.
- Zdarzenia obsługuje samodzielne `if obiekt.clicked:` / `if obiekt.hovered:`, bez `else`. Osobne bloki zdarzeń są osobnymi handlerami; ponowne wykonanie tej samej deklaracji w tym samym zakresie jej nie powiela.
- Handlery działają w wątku Tk; długie pętle mogą blokować okno. Interpreter nie izoluje zużycia zasobów przez niezaufany program.
- Brak instalatora EXE, automatycznej globalnej instalacji i skojarzenia `.kit`. Nie testowano osobno wszystkich wersji Windows i DPI.
