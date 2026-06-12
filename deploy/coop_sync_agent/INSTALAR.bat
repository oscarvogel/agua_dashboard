@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
echo.
echo Instalacion finalizada. Si hubo errores, revisar el mensaje anterior.
pause
