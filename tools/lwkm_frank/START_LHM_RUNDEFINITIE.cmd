@echo off
setlocal
rem Read-only run-definition inventory: use from a checkout in tools\lwkm_frank.
set "PYTHON=E:\tools\deltaforge\deltaforge_4\python.exe"
set "RUNS=G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM"
set "OUTPUT=%RUNS%\LWKM_run_resultaten_totaal"
set "REPORT=%RUNS%\LWKM_tools\LWKM_LHM_RunDef_resultaten_v01"
if not exist "%PYTHON%" (
  echo STOP: Python niet gevonden: %PYTHON%
  exit /b 2
)
"%PYTHON%" "%~dp0run_definition.py" --ini-root "%RUNS%" --ini-root "E:\LHM_4.3.3" --out "%REPORT%" --output-root "%OUTPUT%"
if errorlevel 1 (
  echo STOP: geen bruikbare run-INIs gevonden; controleer de bronlocaties.
  exit /b 1
)
echo GEREED: %REPORT%
endlocal
