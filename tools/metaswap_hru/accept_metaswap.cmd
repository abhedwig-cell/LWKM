@echo off
setlocal
cd /d "%~dp0"
set "LWKM_INPUT=G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_tools\LWKM_MetaSWAP_HRU_Windows_x64_1.0.0\metaswap_hru_output"
if not "%~1"=="" set "LWKM_INPUT=%~1"
accept_metaswap.exe "%LWKM_INPUT%" "%~dp0sources.csv" "%~dp0metaswap_compact" 10242
set "LWKM_RC=%ERRORLEVEL%"
if "%LWKM_RC%"=="1" exit /b 1
powershell -NoProfile -Command "Compress-Archive -Path '.\metaswap_compact\*' -DestinationPath '.\metaswap_compact.zip' -Force"
if errorlevel 1 exit /b 1
echo Compacte overdracht: %~dp0metaswap_compact.zip
echo Controlecode %LWKM_RC%: 0=volledig; 2=ontbrekende waarden. Geen productie-admission.
exit /b %LWKM_RC%
