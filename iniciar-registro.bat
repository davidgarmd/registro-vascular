@echo off
REM Doble clic para arrancar el registro en Windows.
REM Para que arranque solo al encender el ordenador, pon un acceso directo a
REM este fichero en la carpeta de inicio (Win+R, escribe shell:startup).
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python servir.py
pause
