@echo off
setlocal
set "PYTHON=E:\tools\deltaforge\deltaforge_4\python.exe"
set "CONFIG=%~dp0..\..\config\production\frank_run_source_binding_v01.json"
if not "%~1"=="" set "CONFIG=%~1"
if not exist "%PYTHON%" (
  echo STOP: Deltaforge Python niet gevonden: %PYTHON%
  exit /b 2
)
"%PYTHON%" "%~dp0run_source_binding.py" --config "%CONFIG%"
set "RC=%ERRORLEVEL%"
endlocal & exit /b %RC%
