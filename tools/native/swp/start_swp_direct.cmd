@echo off
setlocal
set "LWKM_CALLER_DIR=%CD%"
cd /d "%~dp0\..\..\.."
set "LWKM_PYTHON=E:\tools\deltaforge\deltaforge_4\python.exe"
if not exist "%LWKM_PYTHON%" (
  echo Python niet gevonden: %LWKM_PYTHON%
  exit /b 1
)
"%LWKM_PYTHON%" -m tools.swp_direct_pipeline %*
exit /b %errorlevel%
