@echo off
setlocal
cd /d "%~dp0"
set "LWKM_PYTHON=E:\tools\deltaforge\deltaforge_4\python.exe"
if not exist "%LWKM_PYTHON%" (
  echo Python ontbreekt: %LWKM_PYTHON%
  exit /b 2
)
"%LWKM_PYTHON%" -m tools.server.start_work_e %* > work_e_console.log 2>&1
set "LWKM_RESULT=%errorlevel%"
type work_e_console.log
exit /b %LWKM_RESULT%
