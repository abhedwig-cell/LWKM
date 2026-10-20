@echo off
setlocal EnableExtensions
set "PACKAGE=%~dp0"
if not defined LWKM_MSW_ROOT set "LWKM_MSW_ROOT=G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_run_resultaten_totaal\metaswap"
set "OUTPUT=%PACKAGE%metaswap_hru_output"
if not exist "%PACKAGE%lwkm_metaswap_hru.exe" (
 echo FOUT: lwkm_metaswap_hru.exe ontbreekt in "%PACKAGE%".
 exit /b 2
)
if not exist "%LWKM_MSW_ROOT%\" (
 echo FOUT: bronmap ontbreekt: "%LWKM_MSW_ROOT%".
 echo Controleer de G:-schijf. Bij een andere locatie: set "LWKM_MSW_ROOT=volledig_pad"
 exit /b 2
)
echo LWKM MetaSWAP naar 10.242 HRUs, 1970-2024, 1.980 decades.
echo Bron:   "%LWKM_MSW_ROOT%"
echo Uitvoer: "%OUTPUT%"
echo Bestaande resultaten worden met SHA-256 gecontroleerd.
echo Laat dit venster open. Na onderbreken: start hetzelfde commando opnieuw.
"%PACKAGE%lwkm_metaswap_hru.exe" "%PACKAGE%data\area_svat.inp" "%PACKAGE%data\svat_hru.csv" "%PACKAGE%sources.csv" "%LWKM_MSW_ROOT%" "%OUTPUT%" 10242
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" (
 echo FOUT: verwerking afgebroken, foutcode %RESULT%.
 echo Zie de foutmelding hierboven en "%OUTPUT%\run.log".
 exit /b %RESULT%
)
echo KLAAR. Resultaten en controles: "%OUTPUT%"
exit /b 0
