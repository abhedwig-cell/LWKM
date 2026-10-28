@echo off
setlocal
set "HERE=%~dp0"
if not exist "%HERE%lwkm_w11_packager.exe" (
 echo ERROR: Place qualified Windows package builder executable next to this CMD.
 exit /b 2
)
if not exist "%HERE%catalogue.json" (
 echo ERROR: Missing catalogue.json. Supply a full versioned consumer catalogue.
 exit /b 2
)
"%HERE%lwkm_w11_packager.exe" "%HERE%catalogue.json" "%HERE%run_packages"
exit /b %ERRORLEVEL%
