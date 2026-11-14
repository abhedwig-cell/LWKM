@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0export_hru21.ps1" %*
if errorlevel 1 (echo EXPORT MISLUKT. Lees de foutmelding hierboven. & pause & exit /b 1)
echo Klaar. Upload de nieuwe HRU21_export ZIP.
pause
