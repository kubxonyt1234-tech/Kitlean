# Kitlean v0.3.0-beta

Aktualizacja 0.2 Beta z zachowaniem historii i wcześniejszej składni.

## Nowości

- Audio MP3/WAV/OGG przez pygame: play, pause, resume, stop, volume i loop bez nakładających się kopii.
- Obrazki PNG/JPEG/WebP przez Pillow z proporcjonalną miniaturą.
- Save/load zmiennych w atomowym JSON w katalogu danych użytkownika, osobno dla każdego projektu.
- Klawiatura z ochroną przed autorepeat i skrótami podczas pisania w input.
- Timery oraz wait działające na Tk.after, również w funkcjach i handlerach, z anulowaniem zadań po zamknięciu.
- Parser Pratt, dzielenie :, +=, -=, *=, :=, funkcje math/random, round, sqrt, abs, min, max, pow, nww i nwd.
- Domyślne odwołania do ostatnich obiektów typu w kontekście menu.
- START.bat: podwójne kliknięcie instaluje lokalne środowisko i uruchamia Clickera 0.3.
- Nowe przykłady oraz własna melodia i obrazki na licencji MIT.

## Uruchomienie

Pobierz ZIP i rozpakuj. Kliknij START.bat dwa razy. Potrzebny jest Python 3.12+ z tkinter; pierwsza instalacja wymaga internetu. BAT poda instrukcję, jeśli brakuje Pythona. Można przeciągnąć własny plik .kit na START.bat.

## Weryfikacja

113 testów bez GUI i 16 rzeczywistych przypadków GUI zaliczone, część w osobnych procesach. MP3/WAV/OGG testowane na rzeczywistym mikserze. START.bat przetestowany od tworzenia venv po testowe okno w folderze ze spacją. Szczegóły i pominięcie Tk zakończone poprawnym osobnym testem opisano w docs/verification.md.

## Ograniczenia Beta

Oficjalne dzielenie to dwukropek. Slash pozostaje starszym wyjątkiem zgodności 0.1/0.2, mimo nowej reguły rezerwującej go dla poleceń. Duże zasoby wczytywane są synchronicznie, długie pętle bez wait mogą blokować GUI. Audio jest w pamięci, bez streamingu. Zapisy nie synchronizują równoległych procesów. Zamknięcie anuluje zadania, także kod za run. Brak EXE i testów na wszystkich Windows/DPI/urządzeniach; szczegóły w README.
