@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PY=E:\tools\deltaforge\deltaforge_4\python.exe"
set "PYTHONUTF8=1"
if not exist "%PY%" (
  echo STOP: de eerder gebruikte Deltaforge Python ontbreekt: "%PY%"
  exit /b 2
)
"%PY%" -c "import sys; assert sys.version_info >= (3, 8), 'Python 3.8 of nieuwer vereist'"
if errorlevel 1 (
  echo STOP: Python 3.8 of nieuwer is vereist.
  exit /b 2
)
"%PY%" -u "%~dp0frank_verdacht.py" %*
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" echo De verwerking is gestopt. De bestaande v07-tabellen zijn niet gewijzigd.
exit /b %RESULT%
