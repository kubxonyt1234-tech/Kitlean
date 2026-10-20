# Raport Kitlean 0.4 Beta — 20 października 2026

## Wynik

Rozbudowano istniejący interpreter 0.3, zachowując starsze moduły i składnię. Dodano tworzenie obiektów z nowymi tekstami i aliasami, parametry =, when, action, thene, sprite’y, animacje, ruch, prostą fizykę, kamerę, mysz, segmenty SQLite, szablony NPC, copy/del i stylowanie GUI. Dziewięć przykładów jest wykonywalnych, a trzy nowe grafiki są dołączone na licencji MIT. START.bat domyślnie otwiera Infinite World.

## Wykonane kontrole

Środowisko: Windows, CPython 3.12.10, Tk 8.6, pytest 9.1.1, pygame 2.6.1 i Pillow 13.0.0.

- 145 testów bez GUI: wszystkie zaliczone w jednym przebiegu. To 113 regresji i 32 przypadki 0.4, w tym błędy parametrów, brakujące zasoby, kopie, NPC, ruch zależny od czasu, normalizacja przekątnej, kolizje, skok, animacje i kamera.
- 30 testów rzeczywistego GUI: każdy zaliczony w osobnym świeżym procesie, bez pominięć. Obejmują 16 regresji i 14 przypadków 0.4: prawdziwy Canvas, obrót i zoom obrazów, zaokrąglony przycisk i invoke, fullscreen, mysz, syntetyczne klawisze, asynchroniczne thene, animację zakończoną eventem i dziewięć przykładów.
- Segmenty: wyjście/powrót, 50 pól w prawo i 50 z powrotem, następnie dół/góra; 52 rekordy bazy i maksymalnie cztery żywe obiekty w scenariuszu. Zachowano obiekt gracza i właściwości odtworzonego NPC. Osobny test GUI przechodzi osiem razy między dwoma segmentami bez mnożenia Canvas i NPC.
- Sprawdzono konflikt identyfikatora segmentu bez utraty aktywnych obiektów, zajętą mapę, ograniczenie prób losowania i pomijanie spawnu przy powrocie do snapshotu.
- Instalacja editable 0.4.0b1 oraz wynik CLI „Kitlean 0.4 Beta / Python-powered programming language”: zaliczone.
- START.bat uruchomiono w świeżym katalogu ze spacją w nazwie: utworzył .venv, zainstalował zależności i otworzył testowe okno zamykane timerem. Kod 0 i BAT_GUI_OK. Drugie uruchomienie bez ponownej instalacji także kod 0. Domyślny Infinite World sprawdzono oddzielnym testem GUI.
- Ruff check i format: zaliczone. Diff sprawdzony z uwzględnieniem końców linii Windows.

Łącznie 175 zaliczonych przypadków pytest. Początkowy zbiorczy przebieg GUI miał dwa pominięcia przez sporadyczny błąd inicjalizacji lokalnego Tcl/Tk; pominięć nie zaliczono. Końcowe 30 oddzielnych procesów przeszło w całości. Nie jest to deklaracja jednego zbiorczego przebiegu bez pominięć.

## Poprawione problemy

Usunięto wejście do blokującej pętli GUI po samym ustawieniu właściwości przy aktywnym zegarze świata. Canvas-backed button podnoszony jest przez właściwe Tk raise, bez kolizji z Canvas.lift. Parser rozróżnia wykrzyknik tekstu KLIKNIJ! i delimiter aliasu. Stałe pozycje NPC rezerwowane są przed losowaniem, eliminując losowy konflikt w przykładzie i teście. Zamknięcie anuluje zadania świata i kontynuacje.

## Ograniczenia i świadome decyzje

Fizyka to stałokrokowe AABB, bez mas, tarcia i ciągłego wykrywania szybkich zderzeń. Obrót i bounce są wizualne. NPC to niezależne instancje, bez AI pościgu. Kamera nie zmienia logicznych granic segmentu. Ukryte sprite’y wstrzymują symulację i animację.

W RAM żyje aktualny segment, cache źródeł obrazów ma limit 32, cache SQLite około 512 KiB. Baza na dysku rośnie wraz z odwiedzonym światem. Startowy segment i gracz są tworzeni z kodu przy starcie; snapshoty odwiedzonych pól nie stanowią pełnego save-game. Handlery nie są serializowane. Brak testu wszystkich konfiguracji Windows/DPI oraz fizycznych urządzeń wejścia; klawisze/mysz sprawdzano zdarzeniami Tk. Testy audio potwierdzają działanie dekoderów i kanałów, nie ocenę odsłuchu na każdym sprzęcie.

Przejście zapisuje i zwalnia poprzednie obiekty przed kolejnym kadrem; del game.last=copy potwierdza zwolnienie poprawnie zapisanego segmentu. thene po animate oznacza uruchomienie animacji, nie jej zakończenie. Przy odtwarzaniu pola thene summon w tym samym łańcuchu jest pomijane, aby nie dublować zapisanych NPC. Brak transakcyjnego cofania całego łańcucha.

Zachowano / i // w starszych wyrażeniach jako jawny wyjątek zgodności, mimo wymogu nowego dzielenia :. Nowe przykłady stosują :. Pełny opis semantyki i składni: docs/version-0.4.md.

## Dostarczenie

ZIP zawiera źródła, testy, dokumentację, zasoby i START.bat, bez .venv, cache, prywatnych danych zapisu i plików roboczych. Pierwsze uruchomienie wymaga Python 3.12+ z tkinter oraz internetu do pip. Aktualizacja GitHub zachowuje historię istniejącego repozytorium; wydanie v0.4.0-beta przygotowywane jest jako szkic.

---

# Raport Kitlean 0.3 Beta — 19 października 2026

## Faktycznie wykonane testy

Środowisko: Windows, CPython 3.12.10, pytest 9.1.1, pygame 2.6.1 / SDL_mixer, Pillow 13.0.0 i tkinter/Tk 8.6.

- Instalacja editable 0.3.0b1 w venv: zaliczona.
- 113 testów bez GUI: zaliczone. Obejmują dotychczasowe programy 0.1/0.2, nowy parser Pratt, priorytety i dwukropki, operatory skrócone, funkcje math, NWW/NWD, typy i zakresy, interpolację, zapisy JSON, izolację projektów i obsługę uszkodzeń.
- 16 testów rzeczywistego GUI: zaliczone, część w osobnych procesach. 6 regresji 0.2 plus 10 testów 0.3 (w tym osobne formaty obrazków).
- MP3, WAV i OGG: trzy testy rzeczywistego miksera, bez sterownika dummy. Potwierdzono dekodowanie, długość nagrania, aktywny kanał, brak nakładania kolejnej kopii, pause/resume/stop, zmianę głośności i zwolnienie mixera. Nie oceniano subiektywnej jakości odsłuchu.
- Osobny test z atrapą audio sprawdza pojedyncze wywołanie play, pętlę, pauzę i ustawienia głośności. Osobny test uszkodzonego WAV sprawdza czytelny błąd.
- PNG/JPEG/WebP: prawdziwe PhotoImage w tkinter. Potwierdzono proporcje, naturalne rozmiary, ramkę size, pozycję i visible. Uszkodzony obraz zgłasza linię przypisania file.
- Klawiatura: syntetyczne zdarzenia prawdziwego Tk KeyPress/KeyRelease sprawdzają pojedyncze naliczenie, autorepeat oraz brak skrótu gry przy focus w Entry. Nie był to test fizycznej klawiatury na wszystkich systemach.
- Timer 10 ms tykał podczas dwóch wait po 30 ms w funkcji wywołanej przyciskiem. Potwierdzono działanie innych zdarzeń, stop i brak zadań po zamknięciu. Sprawdzono również wait przed run i anulowanie oczekującego handlera.
- Clicker 0.3: trzy rzeczywiste Button.invoke(), napis Punkty: 3, jeden aktywny kanał muzyki i poprawny odczyt trzech punktów przez nowy interpreter z tego samego projektu.
- Regresja Clickera 0.2: 100 kolejnych kliknięć, zmiany ekranów i punkt 101 bez przebudowy GUI i podwójnych handlerów.
- START.bat: rzeczywiście wykonany w świeżym folderze ze spacją w nazwie. Utworzył venv, pobrał zależności z PyPI, zainstalował Kitlean i uruchomił testowy plik .kit z prawdziwym oknem zamykanym timerem. Kod wyjścia 0, komunikat BAT_GUI_OK. Ponowne uruchomienie użyło środowiska bez instalacji i również zakończyło się kodem 0. Test używał pierwszego argumentu BAT; domyślny Clicker sprawdzono osobnym testem integracyjnym.
- Ruff: wszystkie kontrole zaliczone.

Łącznie zaliczono 129 przypadków pytest (113 bez GUI + 16 GUI). Nie jest to deklaracja jednego przebiegu całego zestawu bez pominięć.

## Problem lokalnego Tk

W zbiorczym przebiegu testów GUI 0.3 jeden test WebP został pominięty, ponieważ lokalny Tcl/Tk sporadycznie nie mógł odczytać pliku tk.tcl/sizegrip.tcl przy kolejnej inicjalizacji. Tego pominięcia nie zaliczono. Ten sam test WebP uruchomiony ponownie w świeżym procesie zakończył się wynikiem 1 passed. Pozostałe przypadki przeszły. Sześć starszych testów GUI wykonywano od razu osobno.

## Ograniczenia i rozstrzygnięcia wymagań

1. Oficjalne dzielenie 0.3 to `:`. Zachowano `/` i `//` w wyrażeniach dla pełnej zgodności z programami 0.1/0.2. Wymagania jednoczesnego zakazu starego operatora i zachowania wszystkich starszych programów są sprzeczne; wybrano zgodność i jawnie opisano wyjątek.
2. Długie instrukcje bez wait mogą blokować Tk. Timery nie są zegarem czasu rzeczywistego. Początkowe wczytanie dużego audio/obrazka odbywa się synchronicznie; samo odtwarzanie jest nieblokujące.
3. Audio jest dekodowane do pamięci, nie strumieniowane. WebP i kodeki zależą od zainstalowanych Pillow/SDL_mixer.
4. Zapisy są atomowe, lecz nie mają blokady współbieżnych procesów. Pełna ścieżka pliku .kit definiuje projekt.
5. Zamknięcie anuluje oczekujące sekwencje, również kod za run. Dawne proste programy z run na końcu zachowują działanie. Nie ma dalszego wykonywania po close.app.
6. BAT nie instaluje automatycznie samego Pythona. Pierwsze uruchomienie wymaga Python >=3.12 z Tcl/Tk oraz internetu. Nie testowano gałęzi braku Pythona na czystym komputerze bez Pythona.
7. Nie przeprowadzono testów na każdej wersji Windows 10/11, DPI ani na wszystkich urządzeniach audio. Nie ma EXE ani instalacji globalnej.

## Powtórzenie testów

```powershell
python -m pip install -e ".[test]"
python -m pytest -q -m "not gui"
python -m pytest tests/test_gui03.py -q -rs
```

Jeśli lokalny Tk pomija przypadek z powodu inicjalizacji, uruchom ten konkretny identyfikator osobno. Raportuj pominięcia osobno od zaliczeń.

---

# Weryfikacja 0.2 Beta

Data: 19 października 2026. Windows, CPython 3.12.10, pytest 9.1.1, Tk 8.6.

## Wyniki aktualizacji

- Ponowna instalacja editable: `pip install -e ".[test]"` zakończona poprawnie; pakiet 0.1.0b1 zastąpiono 0.2.0b1 w lokalnym venv.
- CLI wyświetla dokładnie dwie linie: `Kitlean 0.2 Beta` i `Python-powered programming language` (test dokładnego stdout).
- 62 testy języka/CLI: zaliczone. W tym 31 dotychczasowych testów (z aktualizacją oczekiwanej wersji) i 31 testów nowej składni, interpolacji, zależności, zakresów, deduplikacji i błędów.
- 6 testów rzeczywistego GUI: zaliczone osobno w świeżych procesach, bez atrap tkinter.
- Clicker z `examples/clicker.kit` uruchomiony w prawdziwej pętli `mainloop`: napis początkowy Punkty: 0, rozmiar okna 800×500, przycisk 160×45, układ pionowy bez nakładania.
- 100 wywołań rzeczywistego `Button.invoke()` dało kolejno 1…100 punktów. Po każdym sprawdzono widoczny tekst, zmienną, tożsamość roota, przycisku i licznika. Podczas kliknięć metoda budowania GUI była zastąpiona funkcją zgłaszającą błąd — test potwierdza brak przebudowy.
- Po wielokrotnym przełączeniu menu następne kliknięcie dało dokładnie 101 punktów; nadal zarejestrowany był jeden handler.
- Testy regresji prawdziwego GUI: właściwości, wartości input/checkbox, ręczne wymiary i pozycje, hovered/clicked, przełączanie ekranów, demonstracja menu i błędy callbacków.
- Ścieżka CLI `run examples/clicker.kit` wykonana przez `cli.main`: rzeczywisty interpreter/Tk, 10 kliknięć i poprawny powrót z kodem 0. Wstrzyknięto wyłącznie interpreter z timerem automatyzującym kliknięcia.
- Ruff: formatowanie i kontrola statyczna zaliczone.

Testy GUI uruchamiane są osobno, ponieważ przy wielu instancjach Tcl/Tk w jednym procesie w tym środowisku występowały sporadyczne błędy inicjalizacji. Pominięcie testu nie oznacza zaliczenia. Wyniki powyżej pochodzą z rzeczywistych osobnych wykonań.

```powershell
python -m pytest tests/test_language.py tests/test_v02.py -q
python -m pytest tests/test_gui.py::test_real_widgets_layout_and_properties -q -rs
python -m pytest tests/test_gui.py::test_real_events_and_switching -q -rs
python -m pytest tests/test_gui.py::test_demo_mainloop -q -rs
python -m pytest tests/test_gui.py::test_callback_error_is_language_error -q -rs
python -m pytest tests/test_gui.py::test_v02_clicker_real_mainloop -q -rs
python -m pytest tests/test_gui.py::test_v02_clicker_cli_run -q -rs
```

Nie przeprowadzono osobnej walidacji na wszystkich wersjach Windows 10/11 i ustawieniach DPI. Ograniczenia Beta i zasady migracji opisano w README oraz docs/syntax.md.

---

# Weryfikacja 0.1 Beta

Data: 19 października 2026. Środowisko: Windows, CPython 3.12.10, pytest 9.1.1, tkinter/Tk 8.6.

- Instalacja `pip install -e ".[test]"` w lokalnym venv: wykonana poprawnie.
- Działający entry point `kitlean --version`: `Kitlean 0.1.0b1`.
- 31 testów języka, parsera, CLI i błędów: zaliczone.
- 4 testy rzeczywistego GUI: każdy zaliczony w osobnym procesie pytest. Nie użyto atrap widgetów.
- Test GUI obejmuje pięć rodzajów obiektów, rozmiary 800×500, 160×45 i 240×40, naturalną wysokość label/checkbox, odstępy, ręczne rozmiary/pozycje, widoczność, disabled, wartości input/checkbox i zmianę rodzica.
- Testy zdarzeń wywołują rzeczywiste `Button.invoke()` i zdarzenie `<Enter>`; sprawdzają przełączanie i ukrywanie ekranów.
- Demonstracja `examples/main_menu.kit` działała w rzeczywistej pętli `mainloop`: START → USTAWIENIA → POWRÓT → WYJDŹ; potwierdzono wydruk „Uruchomiono!” i zniszczenie okna.
- Błąd callbacka (dzielenie przez zero) wrócił z pętli jako KitleanError.

## Problem środowiska testowego

Przy tworzeniu kilku niezależnych instancji Tcl/Tk w jednym procesie wystąpiły sporadyczne błędy inicjalizacji (`tcl_findLibrary` / odczyt plików tk.tcl). W przebiegach całego zestawu część testów GUI była pomijana przez fixture. Nie zaliczono pominiętych testów; wszystkie cztery uruchomiono następnie i zaliczono osobno w świeżych procesach.

Powtórzenie testów bez współdzielenia procesu Tk:

```powershell
python -m pytest tests/test_language.py -q
python -m pytest tests/test_gui.py::test_real_widgets_layout_and_properties -q -rs
python -m pytest tests/test_gui.py::test_real_events_and_switching -q -rs
python -m pytest tests/test_gui.py::test_demo_mainloop -q -rs
python -m pytest tests/test_gui.py::test_callback_error_is_language_error -q -rs
```

Nie wykonano osobnej walidacji na fizycznych instalacjach Windows 10 i Windows 11 ani pomiarów wysokiego DPI. Ograniczenia języka opisano w README.
