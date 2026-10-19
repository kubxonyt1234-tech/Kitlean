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
