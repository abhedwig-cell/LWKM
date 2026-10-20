@echo off
setlocal
cd /d "%~dp0"
where g++ >nul 2>nul
if errorlevel 1 (
 echo Install MinGW-w64 x64 or use the recorded Linux cross-build command.
 exit /b 1
)
g++ -std=c++17 -O2 -Wall -Wextra -static -static-libgcc -static-libstdc++ -o lwkm_metaswap_hru.exe lwkm_metaswap_hru.cpp -lbcrypt
exit /b %ERRORLEVEL%
