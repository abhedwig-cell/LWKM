@echo off
setlocal
set "PYTHON=E:\tools\deltaforge\deltaforge_4\python.exe"
if not exist "%PYTHON%" exit /b 2
"%PYTHON%" -m unittest discover -s "%~dp0tests" -p "test_lwkm_frank_msw_basic.py" -v
set "RC=%ERRORLEVEL%"
endlocal & exit /b %RC%
