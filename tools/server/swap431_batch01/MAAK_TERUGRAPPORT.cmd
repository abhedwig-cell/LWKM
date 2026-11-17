@echo off
setlocal
set "PY=E:\tools\deltaforge\deltaforge_4\python.exe"
if defined LWKM_BATCH_PYTHON set "PY=%LWKM_BATCH_PYTHON%"
if not exist "%PY%" (
  echo STOP: Python niet gevonden: "%PY%"
  exit /b 3
)
"%PY%" -u "%~dp0batch.py" pack %*
exit /b %ERRORLEVEL%
