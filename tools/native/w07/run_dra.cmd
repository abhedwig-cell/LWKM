@echo off
setlocal
set "HERE=%~dp0"
if not exist "%HERE%W07Dra.exe" (echo ERROR missing W07Dra.exe & exit /b 2)
if not exist "%HERE%renderer_catalogue.json" (echo ERROR missing qualified renderer_catalogue.json & exit /b 2)
"%HERE%W07Dra.exe" "%HERE%renderer_catalogue.json" "%HERE%dra_output" "%HERE%dra_status.json"
exit /b %ERRORLEVEL%
