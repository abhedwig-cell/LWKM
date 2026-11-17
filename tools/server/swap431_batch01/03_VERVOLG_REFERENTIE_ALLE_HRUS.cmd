@echo off
setlocal
set "PY=E:\tools\deltaforge\deltaforge_4\python.exe"
if defined LWKM_BATCH_PYTHON set "PY=%LWKM_BATCH_PYTHON%"
if not exist "%PY%" (
  echo STOP: Python niet gevonden: "%PY%"
  exit /b 3
)
echo Startbatch eerst inhoudelijk beoordelen. Dit is geen wetenschappelijke productievrijgave.
set "BEVESTIG="
set /p "BEVESTIG=Typ JA om dezelfde campagne uit te breiden naar alle HRUs: "
if /I not "%BEVESTIG%"=="JA" exit /b 2
"%PY%" -u "%~dp0batch.py" approve --confirmed %*
if errorlevel 1 exit /b %ERRORLEVEL%
"%PY%" -u "%~dp0batch.py" all %*
exit /b %ERRORLEVEL%
