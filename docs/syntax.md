# Składnia Kitlean 0.4 Beta

Gry 2D i nowa składnia: [pełny opis 0.4](version-0.4.md).

Zachowane funkcje: [audio, obrazki, zapisy, klawiatura, timery i matematyka 0.3](version-0.3.md). Poniżej wspólna składnia zgodna z 0.2. W nowych programach używaj `:` do dzielenia; `/` w wyrażeniach jest wyłącznie starszym aliasem zgodności.

Pliki `.kit` są zapisywane w UTF-8. Wielkość liter ma znaczenie. Bloki wymagają wcięć (zalecane cztery spacje). `#` rozpoczyna komentarz poza tekstem. Literały i wyrażenia nie wykonują kodu Pythona.

## Tworzenie obiektów

```kitlean
[create gui/menu="game"]
[create item/button="click"]
click.text/KLIKNIJ!
```

`[]` nadają alias programistyczny. Alias nie jest podpisem. Musi być unikalnym identyfikatorem i nie może kolidować ze zmienną, funkcją lub nazwą zastrzeżoną.

```kitlean
create gui/menu
create item/button/KLIKNIJ!
create item/label/$Witaj w Kitlean!$
run
```

Bez aliasu runtime nadaje wewnętrzną nazwę `_anon_N`. Nowy element należy do bieżącego menu. `counter.parent/game` przenosi element i zmienia kontekst na game. `run` bez argumentu uruchamia bieżące menu. Do zdarzeń i późniejszego wskazywania konkretnego elementu używaj aliasów.

| Typ | Rozmiar domyślny |
|---|---|
| gui/menu | 800×500 px |
| item/button | 160×45 px |
| item/input | 240×40 px |
| item/label, item/checkbox | naturalny, według tekstu |

Układ pionowy zaczyna się od (20,20), odstęp wynosi 12 px. Ukryte elementy nie zajmują miejsca. Wymiary i pozycje są opcjonalne.

## Teksty

```kitlean
click.text/KLIKNIJ!
click.text/$Kliknij mnie!$
game.title/$Moja pierwsza gra$
```

Goły tekst w `.text`, `.title`, `.color`, `.background` i `.parent` jest dosłownym ciągiem bez odstępów. Tekst ze spacjami wymaga `$...$`. Stare cytowane stringi pozostają obsługiwane. W wyrażeniach (np. `print`, deklaracja zmiennej) używaj `$...$` albo dawnych cudzysłowów, aby odróżnić tekst od nazwy zmiennej. Znaki nawiasów i inne znaki składni najlepiej zapisywać wewnątrz `$...$`.

Sekwencje ucieczki wewnątrz `$...$`:

| Zapis | Wynik |
|---|---|
| `\$` | dosłowny `$` |
| `\{` i `\}` | dosłowne nawiasy, bez interpolacji |
| `\\` | jeden ukośnik wsteczny |
| `\n` | nowa linia |
| `\t` | tabulator |
| `\r` | powrót karetki |

```kitlean
counter.text/$Cena: 5\$ | \{dosłowny tekst\} | ścieżka: C:\\gry$
```

Nieznana sekwencja ucieczki jest błędem. `$...$` nie może przekraczać linii źródła; do wielowierszowego napisu służy `\n`. Polskie znaki, emoji, cudzysłowy, `#`, `/`, `[]` i interpunkcja wewnątrz delimitera są zwykłym tekstem.

## Zmienne i interpolacja

```kitlean
var/points = 0
var/name = $Jan Kowalski$
var/active = true
points = points + 1
var/half = points / 2
counter.text/$Gracz: {name} | Punkty: {points}$
```

Typy: liczby int/float, tekst, boolean `true`/`false`, listy, pary i `null`. Interpolacja obsługuje wyłącznie nazwy `{points}`. Brak zmiennej to błąd w linii szablonu. Boolean i null są wyświetlane jako `true`, `false`, `null`.

Bezpośredni szablon `.text/$...$`, `.title/$...$` i tekstowego `.value/$...$` pozostaje związany ze zmiennymi znalezionymi w zakresie podczas przypisania. Zmiana którejkolwiek odświeża wszystkie zależne napisy; wartości z innych zakresów nie wywołują aktualizacji. Ponowne przypisanie właściwości zastępuje stare powiązanie. Ustawienie zwykłego tekstu usuwa powiązanie.

`var/message = $Punkty: {points}$` oblicza zwykły tekst w momencie przypisania, podobnie jak `print($Punkty: {points}$)`. Taki wynik nie staje się reaktywną zmienną. Łączenie szablonu z innym wyrażeniem również oblicza jednorazową wartość.

`var/` deklaruje w bieżącym zakresie. Przypisanie bez `var/` aktualizuje najbliższą istniejącą nazwę, także globalną z funkcji. Gdy nazwa nie istnieje, tworzy lokalną. Stare `var points = 0` pozostaje równoważną deklaracją.

## Warunki, pętle i funkcje

```kitlean
if points >= 10:
    print($Wygrana!$)
else:
    print($Klikaj dalej!$)
repeat 5:
    points = points + 1
function welcome(name):
    print($Cześć {name}$)
welcome($Kitlean$)
```

Operatory: `+ - * / // % **`, porównania, `in`, `not in`, `and`, `or`, `not`, indeksowanie list/tekstu. `/` jest dzieleniem w wyrażeniu, a separatorem po nazwie właściwości i w poleceniu `create`. `repeat` przyjmuje nieujemny int. Funkcje wbudowane: `print`, `len`, `str`, `number`. Limit rekurencji: 100. Brak `return`; wynikiem funkcji użytkownika jest null.

## Właściwości

```kitlean
game.size/(1000, 700)
click.size/(250, 60)
click.position/(300, 200)
click.disabled/true
click.visible/false
click.background/$#FF6600$
click.color/$#FFFFFF$
```

Menu: title, background, size; item: text, color, background, parent, size, position, visible, disabled. input.value jest tekstem, checkbox.value boolean. Input można wypełnić przez `.text/$...$` lub `.value/$...$`; aktualną treść użytkownika odczytuje `.value`.

Widoczność i disabled można odczytywać w warunkach. Wymiary muszą być parą dodatnich int; pozycje parą nieujemnych int. Kolory muszą być poprawnymi kolorami Tk (ostateczna kontrola przy wyświetlaniu). `#` w kolorze otocz `$...$` lub cudzysłowami, aby nie rozpoczynał komentarza.

## Zdarzenia i ekrany

```kitlean
if click.clicked:
    points = points + 1
if click.hovered:
    print($Najechano na przycisk$)
open game
close game
run game
close.app
```

Zdarzenia rejestrują blok do późniejszego wywołania. Ponowne wykonanie tej samej deklaracji AST w tym samym zakresie nie dodaje kolejnego handlera. Różne deklaracje nadal mogą obsługiwać to samo zdarzenie. `clicked` i `hovered` nie są flagami do odczytu.

`run` uruchamia jedną pętlę Tk, `open` przełącza menu, `close` ukrywa aktywny ekran i okno. Stan zmiennych i istniejących widgetów pozostaje zachowany. `close.app` zamyka okno; kończą się pozostałe instrukcje programu.

## Zgodność ze starszą składnią i CLI

Obsługiwane są `[create gui.menu="m"]`, `[create item.button="b"]`, `.text/"Tekst"`, `var x = 1`, `run gui.menu="m"`, `open.gui.menu("m")` i `close.gui.menu("m")`.

Uwaga: stare `create item.button/"Tekst"` ustawia tekst ostatniego przycisku w kontekście. Nowe `create item/button/Tekst` tworzy nowy przycisk. Gołe wartości tekstowe są teraz literalne; dynamiczną wartość zmiennej pokazuje `$...{name}...$`.

CLI: `kitlean run program.kit`, `kitlean check program.kit`, `kitlean help`, `kitlean --version`. `check` nie wykonuje programu; nazwy i typy sprawdzane są w runtime. Błędy mają postać `KitleanError [Line N]` i kończą CLI kodem 1.
