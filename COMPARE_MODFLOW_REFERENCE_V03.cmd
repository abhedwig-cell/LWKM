@echo off
setlocal
set "PYTHON=E:\tools\deltaforge\deltaforge_4\python.exe"
if not exist "%PYTHON%" (
  echo STOP: Deltaforge Python niet gevonden: %PYTHON%
  exit /b 2
)
set "CONFIG=%~dp0config\production\frank_pipeline_v03.json"
"%PYTHON%" -B "%~dp0tools\lwkm_frank\compare_modflow_v03.py" compare --config "%CONFIG%"
set "RC=%ERRORLEVEL%"
endlocal & exit /b %RC%
