@echo off
setlocal
cd /d "%~dp0"
"E:\tools\deltaforge\deltaforge_4\python.exe" -m tools.server.swp_source_inventory %*
exit /b %errorlevel%
