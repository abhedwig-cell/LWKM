@echo off
setlocal
set "PYTHON=E:\tools\deltaforge\deltaforge_4\python.exe"
if not exist "%PYTHON%" (
  echo STOP: Deltaforge Python niet gevonden: %PYTHON%
  exit /b 2
)
set "CONFIG=%~dp0config\production\frank_pipeline_v03.json"
rem Alleen MODFLOW. Bestaande MetaSWAP-resultaten blijven staan.
"%PYTHON%" -B "%~dp0tools\lwkm_frank\compare_modflow_v03.py" check-reference --config "%CONFIG%"
if errorlevel 1 exit /b %ERRORLEVEL%
"%PYTHON%" -B "%~dp0tools\lwkm_frank\pipeline_v03.py" check --config "%CONFIG%" --through modflow_original
if errorlevel 1 exit /b %ERRORLEVEL%
"%PYTHON%" -B "%~dp0tools\lwkm_frank\pipeline_v03.py" diagnostic-run --config "%CONFIG%" --through modflow_original
if errorlevel 1 exit /b %ERRORLEVEL%
"%PYTHON%" -B "%~dp0tools\lwkm_frank\compare_modflow_v03.py" compare --config "%CONFIG%"
set "RC=%ERRORLEVEL%"
endlocal & exit /b %RC%
