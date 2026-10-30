@echo off
setlocal
cd /d "%~dp0\..\.."
set "LWKM_PYTHON=E:\tools\deltaforge\deltaforge_4\python.exe"
if not exist "%LWKM_PYTHON%" (
  echo Deltaforge Python ontbreekt: %LWKM_PYTHON%
  exit /b 2
)
set "LWKM_RESULTS=G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_run_resultaten_totaal\modflow"
"%LWKM_PYTHON%" -m tools.server.bdgqlat_daily --root "%LWKM_RESULTS%" --mask "source_data\IBOUND_L1.IDF" --output "%LWKM_RESULTS%\bdgqlat_reconstructed" %*
exit /b %errorlevel%
