@echo off
setlocal
set "BASEDIR=%~dp0"
if not exist "%BASEDIR%datamodel_10242_2.sqlite" (
 echo Missing datamodel_10242_2.sqlite
 exit /b 2
)
if not exist "%BASEDIR%wwl.swp" (
 echo Missing wwl.swp template
 exit /b 2
)
"%BASEDIR%LWKM_SWP.exe" --database "%BASEDIR%datamodel_10242_2.sqlite" --template "%BASEDIR%wwl.swp" --output "%BASEDIR%SWP_OUTPUT"
exit /b %errorlevel%
