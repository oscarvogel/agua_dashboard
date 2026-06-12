@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_sync.ps1"
echo.
echo Sincronizacion finalizada. Revisar logs\sync para el resultado JSON.
pause
