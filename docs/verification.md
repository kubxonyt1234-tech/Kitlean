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
