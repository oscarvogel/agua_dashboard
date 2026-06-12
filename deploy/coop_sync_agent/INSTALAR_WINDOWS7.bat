@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_win7.ps1"
echo.
echo Instalador Windows 7 finalizado. Si falta completar .env, se abre ahora.
if exist "C:\agua-dashboard-sync-agent\.env" notepad "C:\agua-dashboard-sync-agent\.env"
pause
