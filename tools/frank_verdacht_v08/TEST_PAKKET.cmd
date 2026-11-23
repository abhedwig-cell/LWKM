@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PY=E:\tools\deltaforge\deltaforge_4\python.exe"
set "PYTHONUTF8=1"
if not exist "%PY%" (
  echo STOP: Deltaforge Python ontbreekt: "%PY%"
  exit /b 2
)
"%PY%" -m unittest discover -s tests -v
exit /b %ERRORLEVEL%
