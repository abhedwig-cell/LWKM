@echo off
call "%~dp0START_FRANK_VERDACHT.cmd" --check-only %*
exit /b %ERRORLEVEL%
