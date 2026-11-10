@echo off
setlocal
set "PYTHON=E:\tools\deltaforge\deltaforge_4\python.exe"
if not exist "%PYTHON%" (
  echo STOP: Deltaforge Python niet gevonden: %PYTHON%
  exit /b 2
)
"%PYTHON%" -u "%~dp0tools\lwkm_frank\msw_basic_run.py" --config "%~dp0config\production\frank_msw_basic_v03.json" --report "%~dp0MSW_BASIC_RUN.json" --run
set "RC=%ERRORLEVEL%"
endlocal & exit /b %RC%
