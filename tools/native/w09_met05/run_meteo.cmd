@echo off
setlocal
cd /d "%~dp0"
if not exist "w09_direct_met.exe" (echo ERROR: w09_direct_met.exe ontbreekt. & exit /b 2)
if not exist "w09_met_config.ini" (echo ERROR: w09_met_config.ini ontbreekt. & exit /b 2)
"w09_direct_met.exe" "w09_met_config.ini"
exit /b %errorlevel%
