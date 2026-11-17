@echo off
setlocal
set "PY=E:\tools\deltaforge\deltaforge_4\python.exe"
if defined LWKM_BATCH_PYTHON set "PY=%LWKM_BATCH_PYTHON%"
if not exist "%PY%" (
  echo STOP: Python niet gevonden: "%PY%"
  exit /b 3
)
"%PY%" "%~dp0batch.py" verify
if errorlevel 1 exit /b %ERRORLEVEL%
"%PY%" -m unittest discover -s "%~dp0tests" -p "test_*.py" -v
exit /b %ERRORLEVEL%
