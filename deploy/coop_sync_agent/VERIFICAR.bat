@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0verify.ps1"
echo.
echo Verificacion finalizada. Si dry_run aparece en true, la configuracion basica esta OK.
pause
