# Kitlean 0.3 Beta — nowe możliwości

Wszystkie opisane poniżej instrukcje są zaimplementowane. Przykłady są plikami `.kit`, bez kodu Pythona.

## Matematyka

```kitlean
var/a = 10
var/b = 4
var/result = (a + 5) : 3
if result : 2 > 1:
    print(result)
a += 5
a -= 2
a *= 3
a := 2
```

Parser Pratt rozpoznaje `:` w wyrażeniach, a parser bloków usuwa końcowy `:` nagłówka warunku/pętli/funkcji. `:=` jest instrukcją dzielenia z przypisaniem, nigdy walrus. Kolejność: nawiasy, potęga (prawostronna), mnożenie/dzielenie/modulo, dodawanie/odejmowanie, porównania, not/and/or. `-2 ** 2` daje -4. Dzielenie/modulo przez zero zgłasza KitleanMathError z numerem linii.

| Wywołanie | Wynik/zasady |
|---|---|
| math/random(1,100) | int, oba końce włącznie |
| math/round(3.76) | 4; połówki do parzystej liczby |
| math/sqrt(25) | 5; argument nieujemny |
| math/abs(-10) | 10 |
| math/min(5,10), math/max(5,10) | minimum/maksimum dwóch liczb |
| math/pow(2,3) | 8; wynik rzeczywisty |
| math/nww(12,18), math/nwd(12,18) | 36 oraz 6 |

NWW/NWD i random wymagają int (boolean nie jest liczbą). Ujemne int są obsługiwane; NWW/NWD zwracają nieujemny wynik. NWD(0,0)=0, NWW(0,a)=0. Pierwiastek z liczby ujemnej, zły typ, arność lub zakres zwracają KitleanMathError. Nazwy zmiennych są dozwolone jako argumenty.

Nowe programy używają `:`. Dawne `/` i `//` pozostają obsługiwane wyłącznie ze względu na zgodność wcześniejszych plików, mimo nowej reguły rezerwującej `/` dla poleceń. `math/...` jest własnym elementem gramatyki, nie dzieleniem.

## Odwołania domyślne

`gui`, `audio`, `timer` wskazują ostatnio utworzone menu/audio/timer. `button`, `label`, `input`, `checkbox`, `image` wskazują ostatni element tego typu w bieżącym menu. Tworzenie menu i ustawienie `.parent` zmienia kontekst. Brak elementu w kontekście to błąd, bez szukania podobnego w innym menu. Jawny alias o tej samej nazwie ma pierwszeństwo, aby starsze programy nadal działały.

Cel zdarzenia rozwiązywany jest podczas deklaracji handlera. Polecenia wewnątrz handlera rozwiązywane są podczas wykonania. Jeśli tworzysz kolejne obiekty tego samego typu, do stabilnych odwołań używaj aliasów.

## Audio

```kitlean
[create audio/music="song"]
song.file/assets/music.mp3
song.volume/50
song.loop/true
play song
pause song
resume song
stop song
```

Bez aliasu: `create audio/music`, potem `audio.file/...` i `play audio`. Głośność to liczba 0–100, loop to boolean. MP3/WAV/OGG obsługuje pygame/SDL_mixer. Ponowne play aktywnego utworu nie tworzy kopii. Po stop kolejne play zaczyna od początku. Pause wymaga resume; play na wstrzymanym aktywnym kanale nie restartuje utworu. Zmiana file/loop zatrzymuje dotychczasowy kanał; następne play użyje nowych ustawień. Volume zmienia działający utwór.

Ścieżki są danymi. Względna ścieżka liczona jest od katalogu pliku `.kit`; ścieżka bezwzględna jest używana bez zmiany. Dla file literał `$C:\My Music\background.mp3$` zachowuje ukośniki Windows (nie interpretuje `\n` jako nowej linii). Nadal obsługuje `\$`, `\{`, `\}` i `\\`. Poza właściwością file obowiązują dotychczasowe ucieczki tekstu.

Brak pliku, niepoprawny format i brak urządzenia zgłaszają KitleanError. Audio nie korzysta z pętli ani wątku GUI do dekodowania kolejnych próbek; duże pliki ładowane są w całości i początkowe wczytanie może chwilowo potrwać. `close.app` zatrzymuje kanały i zwalnia mixer.

## Obrazki

```kitlean
create gui/menu
[create item/image="logo"]
logo.file/assets/logo.png
logo.size/(200,200)
logo.position/(50,50)
logo.visible/true
run gui
```

size/position są opcjonalne. PNG, JPG/JPEG i WebP odczytuje Pillow. Proporcje pozostają zachowane; size wyznacza ramkę docelową. Bez size miniatura mieści się w 320×240 i granicach menu z marginesem. Runtime utrzymuje referencję PhotoImage, aby obraz nie znikał. Przykład images.kit ma dołączony zasób MIT.

## Dane trwałe

```kitlean
var/points = 0
load points
points += 1
save points
```

Obsługiwane są skończone liczby, tekst, boolean, null i zagnieżdżone listy. Zmienna musi istnieć przed load/save. Brak zapisu pozostawia domyślną wartość. Wczytanie odświeża zależne napisy.

Windows: `%LOCALAPPDATA%\Kitlean\saves\<hash pełnej ścieżki programu>\variables.json`. Na systemie bez LOCALAPPDATA używany jest katalog `.local/share` użytkownika. Zapis jest JSON, bez pickle, z flush/fsync i atomowym os.replace pliku tymczasowego w tym samym katalogu. Uszkodzony plik jest zgłaszany, nie kasowany. Kopie tego samego programu pod różnymi ścieżkami mają oddzielne dane. Nie ma blokady między równoległymi procesami.

## Klawiatura

```kitlean
if key/SPACE.pressed:
    points += 1
if key/ESCAPE.pressed:
    close.app
```

A–Z, 0–9, SPACE, ENTER, ESCAPE, UP, DOWN, LEFT, RIGHT. Wielkość liter nazwy klawisza nie ma znaczenia. Zdarzenie oznacza przejście do stanu naciśniętego. Powtórzenia KeyPress są ignorowane do KeyRelease. Odroczone zwolnienie eliminuje również typową sekwencję autorepeat release/press. Utrata fokusu okna czyści stan. W Entry/Text/Spinbox skróty gry są ignorowane; nie ma w tej wersji opcji wymuszenia skrótów w polu tekstowym.

## wait i timery

```kitlean
[create timer="clock"]
clock.interval/1
clock.loop/true
if clock.tick:
    print($Minęła sekunda$)
start clock
stop clock
wait/2
```

interval to dodatnia skończona liczba sekund. Domyślnie interval=1, loop=false. Start aktywnego timera nie tworzy drugiej kopii. Stop anuluje następny tick. Zmiana interval dotyczy kolejnego planowanego tyknięcia (już zaplanowane zachowuje dotychczasowy termin).

Wait przyjmuje nieujemne sekundy i zawiesza bieżącą sekwencję poleceń. Działa również w repeat, if i funkcjach; inne zdarzenia i timery nadal pracują. Implementacja używa awaitowalnych instrukcji i Tk.after, bez time.sleep w wątku GUI. W pliku `.kit` nie używa się async/await. Czasy są przybliżone, a nie do zastosowań czasu rzeczywistego.

Zamknięcie aplikacji anuluje oczekujące kontynuacje i wszystkie timery, zamyka kanały audio i niszczy okno. Blok kodu po wait nie wykona się po close.app. Kod po run również jest anulowany przy zamknięciu. Stop timera nie cofa handlera, który już został uruchomiony.

## START.bat

Podwójne kliknięcie tworzy lokalną `.venv`, instaluje pakiet przez pip i otwiera clicker_03.kit. Skrypt działa względem własnego folderu, również ze spacjami. Obsługuje podany plik jako pierwszy argument/przeciągnięty plik. Wykrywa py -3.12, py -3 lub python i sprawdza wersję >=3.12. Nie zmienia globalnego PATH i nie używa administracyjnych uprawnień.
