@echo off
setlocal
cd /d "%~dp0"
if not defined LWKM_PYTHON set "LWKM_PYTHON=E:\tools\deltaforge\deltaforge_4\python.exe"
if not exist "%LWKM_PYTHON%" (
  echo STOP: Python niet gevonden: %LWKM_PYTHON%
  echo Er wordt niets geinstalleerd en geen bronbestand gewijzigd.
  exit /b 2
)
"%LWKM_PYTHON%" "%~dp0maak_frank_leesbaar.py" %*
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" echo Geen nieuwe complete uitvoer gepubliceerd; zie fout hierboven.
exit /b %RC%
