@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (set PY=py) else (set PY=python)
%PY% --version >nul 2>nul
if errorlevel 1 (
  echo No se encontro Python. Instale Python 3.10 o superior y active Add Python to PATH.
  pause
  exit /b 1
)
start "HT-01 Enterprise" cmd /c "timeout /t 2 >nul & start http://127.0.0.1:8000"
%PY% app\server.py
pause
