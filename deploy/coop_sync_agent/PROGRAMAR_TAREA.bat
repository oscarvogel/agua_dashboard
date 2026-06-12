@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" -RegisterTask -StartTime 08:00 -IntervalMinutes 60
echo.
echo Tarea programada creada o actualizada. Para consultar estado ejecutar:
echo powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" -VerifyTask
pause
