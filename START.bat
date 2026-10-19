@echo off
setlocal DisableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto checkinstall
where py >nul 2>nul
if errorlevel 1 goto trypython
py -3.12 -c "import sys; raise SystemExit(sys.version_info < (3,12))" >nul 2>nul
if errorlevel 1 goto trylatest
py -3.12 -m venv ".venv"
goto checkenv
:trylatest
py -3 -c "import sys; raise SystemExit(sys.version_info < (3,12))" >nul 2>nul
if errorlevel 1 goto trypython
py -3 -m venv ".venv"
goto checkenv
:trypython
python -c "import sys; raise SystemExit(sys.version_info < (3,12))" >nul 2>nul
if errorlevel 1 goto missing
python -m venv ".venv"
:checkenv
if errorlevel 1 goto failed
if not exist ".venv\Scripts\python.exe" goto failed
:checkinstall
if not exist ".venv\Scripts\kitlean.exe" goto install
".venv\Scripts\python.exe" -c "from importlib.metadata import version; assert version('kitlean') == '0.3.0b1'; import pygame, PIL" >nul 2>nul
if not errorlevel 1 goto launch
:install
echo Instalowanie Kitlean 0.3 Beta i bibliotek audio/obrazkow...
echo Pierwsze uruchomienie wymaga internetu.
".venv\Scripts\python.exe" -m pip install -e .
if errorlevel 1 goto failed
:launch
if "%~1"=="" goto demo
".venv\Scripts\python.exe" -m kitlean run "%~1"
goto finished
:demo
".venv\Scripts\python.exe" -m kitlean run "examples\clicker_03.kit"
:finished
if errorlevel 1 goto failed
exit /b 0
:missing
echo Brak Pythona 3.12 lub nowszego.
echo Zainstaluj Python dla Windows z https://www.python.org/downloads/windows/
echo W instalatorze zaznacz Add Python to PATH oraz Tcl/Tk, potem uruchom START.bat ponownie.
goto failed
:failed
echo Nie udalo sie zainstalowac lub uruchomic Kitlean. Skopiuj komunikat powyzej.
if not defined KITLEAN_NO_PAUSE pause
exit /b 1
