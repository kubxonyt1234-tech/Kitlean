# Składnia Kitlean 0.1 Beta

Pliki UTF-8, rozszerzenie `.kit`. Bloki wyznaczają wcięcia (zalecane cztery spacje). Komentarze zaczynają się od `#`. Nazwy są rozróżniane wielkością liter.

## Obiekty

`[create gui.menu="MainMenu"]` tworzy ekran 800 × 500 px i ustawia bieżący kontekst. Dostępne są `item.button` (160 × 45), `item.input` (240 × 40), `item.label` i `item.checkbox` (rozmiar naturalny). Element otrzymuje rodzica z bieżącego kontekstu. Nazwy muszą być unikalnymi identyfikatorami.

`start.parent/"MainMenu"` przenosi element i ustawia kontekst na MainMenu. `start.text/"START"` ustawia podpis. `create item.button/"START"` ustawia podpis ostatniego przycisku w bieżącym kontekście, uwzględniając przeniesienie przez `.parent`.

## Właściwości

Operator `/` po `nazwa.właściwość` przypisuje wartość. W wyrażeniach `/` oznacza dzielenie. Własności można odczytywać w wyrażeniach, np. `if start.visible and not start.disabled:`.

| Właściwość | Wartość | Elementy |
|---|---|---|
| title | string | menu |
| text, color | string | item |
| background | kolor Tk, np. `"#FF6600"` | wszystkie |
| parent | nazwa menu | item |
| size | para dodatnich int, px | wszystkie |
| position | para nieujemnych int, px | item; dla menu metadane |
| visible, disabled | boolean | wszystkie; dla menu metadane |
| value | string / boolean | input / checkbox |

Elementy widoczne bez ręcznej pozycji układają się pionowo od (20,20), z odstępem 12 px. Ukryte elementy nie zajmują miejsca. `disabled` blokuje obsługę zdarzeń. Kolory i pozostałe parametry Tk są ostatecznie weryfikowane przy budowaniu GUI.

## Wartości i sterowanie

```kitlean
var points = 10
points = points + 5
var values = [1, 2, null, true, "tekst"]
if points >= 10:
    print("Wygrana!")
else:
    print("Spróbuj ponownie")
repeat 5:
    print(values[0])
function welcome(name):
    print("Cześć " + name)
welcome("Kitlean")
```

Typy: string, int/float, boolean (`true`, `false`), list, para i `null`. Operatory: `+ - * / // % **`, porównania, `in`, `not in`, `and`, `or`, `not`. Indeksowanie list i tekstu. Funkcje wbudowane: `print`, `len`, `str`, `number`. Warunki używają prawdziwości wartości. Pętla repeat wymaga nieujemnego int. Rekurencja jest ograniczona do 100 wywołań.

## Zdarzenia i ekrany

```kitlean
if start.clicked:
    print("Kliknięto!")
if start.hovered:
    start.text/"Najechano"
open.gui.menu("Settings")
close.gui.menu("Settings")
run gui.menu="MainMenu"
```

`clicked` i `hovered` rejestrują bloki, nie są odczytywalnymi flagami. `run` uruchamia jedną pętlę Tk. `open` zmienia ekran, a `close` ukrywa aktywny ekran. `close.app` niszczy okno. Błędy w callbackach zatrzymują GUI i wracają do CLI jako KitleanError.

## CLI i błędy

`kitlean --version`, `kitlean help`, `kitlean check program.kit`, `kitlean run program.kit`. Błąd kończy CLI kodem 1 i podaje numer linii. `check` nie wykonuje programu ani nie otwiera okna.
