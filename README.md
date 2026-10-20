# Kitlean 0.4 Beta

Język programowania `.kit` do prostych aplikacji i gier. Python 3.12+, tkinter, Windows 10/11, licencja MIT. Rozbudowa istniejącego interpretera 0.1–0.3.

## Najprostsze uruchomienie

1. Pobierz i rozpakuj ZIP.
2. Otwórz folder zawierający **START.bat**.
3. Kliknij **START.bat** dwa razy.

Launcher znajduje Python 3.12+, tworzy `.venv`, instaluje Kitlean, pygame i Pillow, a następnie otwiera **Infinite World 0.4: WSAD, kamera i segmenty mapy**. Pierwsza instalacja wymaga internetu. Kolejne uruchomienia używają istniejącego środowiska. Jeżeli brakuje Pythona, pojawia się adres oficjalnego instalatora; BAT nie pobiera ani nie instaluje go automatycznie.

Możesz przeciągnąć własny plik `.kit` na START.bat lub wykonać `START.bat "C:\Moje programy\gra.kit"`. Nie wymaga PowerShell ani zmiany ExecutionPolicy. Błąd pozostawia okno z komunikatem. Brak globalnej modyfikacji PATH.

Alternatywa dla programistów:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\kitlean.exe run examples/infinite_world.kit
```

Dostępny jest również `install.ps1`. CLI zachowuje `run`, `check`, `help`, `--version`.

## Co działa w 0.4

- Sprite’y na Canvas, WSAD/strzałki, grawitacja, skok i kolizje prostokątów.
- Kamera, animacje bounce/rotate/fade oraz zdarzenia myszy i `when`.
- Segmenty mapy zapisywane w SQLite, powrót do odwiedzonych miejsc, niezależne kopie NPC.
- Sekwencje `thene`, zaokrąglone przyciski, wyrównanie i fullscreen.
- [Pełna składnia i ograniczenia 0.4](docs/version-0.4.md).

## Zachowane funkcje

- GUI z domyślnym pionowym układem, przyciski, input, label, checkbox i obrazki PNG/JPEG/WebP.
- Reaktywne teksty `$Punkty: {points}$`, zmienne, listy, warunki, funkcje i pętle.
- Audio MP3/WAV/OGG: głośność, pętla, play/pause/resume/stop, bez nakładania kolejnych kopii tej samej muzyki.
- Zapisy i odczyty JSON, osobne dla każdego programu, zapis atomowy przez plik tymczasowy.
- Klawiatura A–Z, 0–9, SPACE, ENTER, ESCAPE i strzałki; jedno zdarzenie na naciśnięcie, bez skrótów gry w input.
- Timery start/stop oraz `wait` zawieszające wyłącznie bieżący ciąg instrukcji, także w funkcji wywołanej z handlera.
- Dzielenie `:`, operatory `+=`, `-=`, `*=`, `:=`, funkcje math, NWW i NWD.
- Anonimowe obiekty i skróty `gui`, `button`, `label`, `input`, `checkbox`, `image`, `audio`, `timer`.

```kitlean
create gui/menu
gui.title/$Kitlean 0.3$
var/points = 0
load points
create item/label/$Punkty: {points}$
create item/button/KLIKNIJ!
if button.clicked:
    points += 1
    save points
if key/SPACE.pressed:
    points += 1
run gui
```

## Przykłady

| Plik w examples/ | Funkcja |
|---|---|
| clicker_03.kit | Kliknięcia, zapis, odczyt i zapętlona muzyka |
| clicker.kit | Nowa składnia 0.4 i reaktywny licznik |
| movement.kit, gravity.kit, collisions.kit | Ruch, skok, platformy i kontakty |
| animations.kit, camera.kit | Animacje i kamera |
| infinite_world.kit, npc_spawn.kit | Segmenty i szablony NPC |
| gui_styles.kit | Kolory, rounded, align, mysz |
| main_menu.kit | Starsza składnia 0.2 |
| music.kit | Play/pause/resume/stop |
| images.kit | Obrazek bez ręcznego rozmiaru |
| math.kit | Działania i funkcje math |
| nww_nwd.kit | NWW i NWD |
| timers.kit | Timer i wait bez blokowania okna |
| keyboard.kit | SPACE/ESCAPE oraz input bez skrótów |
| save_load.kit | Trwały licznik uruchomień |

Zasoby w `examples/assets` są wygenerowanymi na potrzeby projektu materiałami MIT. Przykłady nie wskazują brakujących plików. Ścieżki względne liczone są od pliku `.kit`, niezależnie od bieżącego katalogu terminala.

## Dokumentacja i testy

[Składnia](docs/syntax.md), [nowe funkcje 0.4](docs/version-0.4.md), [funkcje 0.3](docs/version-0.3.md), [historia](CHANGELOG.md), [raport wykonanych testów](docs/verification.md).

```powershell
python -m pytest -q -m "not gui"
python -m pytest tests/test_gui03.py -q -rs
```

Testy GUI wymagają pulpitu i tkinter. Testy oznaczone audio korzystają z rzeczywistego SDL_mixer; muszą mieć działające urządzenie audio. Testy z atrapami są oddzielne. Raport jasno rozróżnia testy wykonane, pominięte i ograniczenia.

## Zgodność i ograniczenia

- Działają stare polecenia obiektów z kropką, dawne stringi, `var points = ...`, starsze polecenia menu i interpolacja 0.2. Oficjalnym operatorem dzielenia 0.3 jest `:`. `/` i `//` w wyrażeniach pozostały jako wyjątek zgodności 0.1/0.2; nowe przykłady ich nie używają. To świadome rozstrzygnięcie sprzeczności między pełną zgodnością a zakazem dawnego dzielenia.
- Jawny alias ma pierwszeństwo przed skrótem typu. Skróty item wskazują ostatni obiekt typu w bieżącym menu, a gui/audio/timer ostatni obiekt globalnie. Nie przeszukują innych menu. Do trwałego wskazywania konkretnego obiektu używaj aliasu.
- Timer i wait działają kooperacyjnie na jednej pętli Tk. Długa pętla bez wait nadal może blokować okno. Kolejne handlery mogą działać podczas oczekiwania wcześniejszych. Zamknięcie anuluje oczekujące zadania, także kod po run.
- `run` oddaje obsługę okna pętli Tk; instrukcje po run nie są wykonywane po zamknięciu, bo zamknięcie anuluje zadania. `close` tylko ukrywa ekran, a `close.app` zwalnia zasoby.
- Audio ładuje cały plik do pamięci; kodeki zależą od SDL_mixer. Nie ma streamingu, miksowania zaawansowanego ani kontroli urządzeń. Potwierdzono działanie kanałów, nie przeprowadzono subiektywnego odsłuchu na każdym sprzęcie.
- Rozmiar obrazka bez size mieści się w 320×240 i obszarze menu z marginesem 20 px, z zachowaniem proporcji. Pozostały układ nie przewija zawartości. Ręczne pozycje mogą wychodzić poza ekran.
- Zapisy rozdziela pełna ścieżka programu. Przeniesienie `.kit` tworzy nowy zestaw zapisów. Brak synchronizacji między równocześnie uruchomionymi kopiami projektu. Uszkodzony JSON zgłasza błąd i nie jest nadpisywany automatycznie.
- Brak return, klas i importów w języku. Interpreter nie jest piaskownicą zasobów. Nie testowano wszystkich wariantów Windows 10/11 i DPI. BAT wymaga dostępnego instalatora Pythona/pip oraz internetu przy pierwszym uruchomieniu.
