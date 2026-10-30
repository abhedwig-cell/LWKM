@echo off
setlocal EnableExtensions
cd /d "%~dp0\..\.."
set "LWKM_PYTHON=E:\tools\deltaforge\deltaforge_4\python.exe"
set "LWKM_RESULTS=G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_run_resultaten_totaal\modflow"
if not exist "%LWKM_PYTHON%" (
 echo FOUT: Deltaforge Python ontbreekt: %LWKM_PYTHON%
 exit /b 2
)
if not exist "%LWKM_RESULTS%\bdgfrf" (
 echo FOUT: FRF-bronmap ontbreekt
 exit /b 2
)
if not exist "%LWKM_RESULTS%\bdgfff" (
 echo FOUT: FFF-bronmap ontbreekt
 exit /b 2
)
set "LWKM_MASK="
set "LWKM_MASK_TMP=%TEMP%\lwkm_bdgqlat_mask_%RANDOM%_%RANDOM%.txt"
"%LWKM_PYTHON%" -m tools.server.resolve_original_ibound "%CD%" "%LWKM_RESULTS%" > "%LWKM_MASK_TMP%"
if errorlevel 1 (
 type "%LWKM_MASK_TMP%"
 del "%LWKM_MASK_TMP%" >nul 2>&1
 echo FOUT: oorspronkelijke MODFLOW IBOUND niet aantoonbaar beschikbaar.
 exit /b 2
)
set /p LWKM_MASK=<"%LWKM_MASK_TMP%"
del "%LWKM_MASK_TMP%" >nul 2>&1
echo Oorspronkelijke IBOUND: %LWKM_MASK%
"%LWKM_PYTHON%" -m tools.server.bdgqlat_daily --root "%LWKM_RESULTS%" --mask "%LWKM_MASK%" --output "%LWKM_RESULTS%\bdgqlat_reconstructed" %*
exit /b %errorlevel%
