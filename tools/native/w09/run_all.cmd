@echo off
setlocal
set "HERE=%~dp0"
if not exist "%HERE%lwkm_w09_meteo.exe" (
  echo ERROR: missing lwkm_w09_meteo.exe. Obtain the Windows x64 artifact from the qualified W09 GitHub Actions run.
  exit /b 2
)
if not exist "%HERE%w09_config.ini" (
  echo ERROR: missing w09_config.ini. Set actual LHM input paths and verified conversion factors.
  exit /b 2
)
"%HERE%lwkm_w09_meteo.exe" "%HERE%w09_config.ini"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" echo ERROR: W09 meteo aggregation stopped, code %RC%.
exit /b %RC%
