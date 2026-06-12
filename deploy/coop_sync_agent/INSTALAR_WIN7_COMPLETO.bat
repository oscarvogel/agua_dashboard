@echo off
setlocal
cd /d "%~dp0"

if not exist "%~dp0sync.exe" (
  echo Falta sync.exe en esta carpeta.
  echo Volver a generar el paquete completo Win7.
  pause
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_win7.ps1"
echo.
echo Instalacion completa finalizada.
if exist "C:\agua-dashboard-sync-agent\.env" notepad "C:\agua-dashboard-sync-agent\.env"
pause
