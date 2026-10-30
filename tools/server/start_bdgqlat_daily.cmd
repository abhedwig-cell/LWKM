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
 echo FOUT: FRF-bronmap ontbreekt: %LWKM_RESULTS%\bdgfrf
 exit /b 2
)
if not exist "%LWKM_RESULTS%\bdgfff" (
 echo FOUT: FFF-bronmap ontbreekt: %LWKM_RESULTS%\bdgfff
 exit /b 2
)
set "LWKM_MASK="
rem Prefer the BBC09 original IBOUND distributed next to the package.
for %%F in ("source_data\IBOUND_L1.IDF" "tools\server\source_data\IBOUND_L1.IDF" "IBOUND_L1.IDF") do (
 if not defined LWKM_MASK if exist "%%~F" set "LWKM_MASK=%%~fF"
)
if not defined LWKM_MASK (
 echo FOUT: IBOUND_L1.IDF ontbreekt in het BBC09/LWKM-pakket.
 echo Lever het oorspronkelijke BBC09-pakket inclusief source_data mee.
 echo Er wordt niet automatisch een willekeurig masker gekozen.
 exit /b 2
)
echo Python: %LWKM_PYTHON%
echo Bron: %LWKM_RESULTS%
echo IBOUND: %LWKM_MASK%
echo Uitvoer: %LWKM_RESULTS%\bdgqlat_reconstructed
"%LWKM_PYTHON%" -m tools.server.bdgqlat_daily --root "%LWKM_RESULTS%" --mask "%LWKM_MASK%" --output "%LWKM_RESULTS%\bdgqlat_reconstructed" %*
exit /b %errorlevel%
