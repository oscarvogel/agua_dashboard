@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0sync_cli_to_vps.ps1"
if errorlevel 1 (
  echo.
  echo Fallo la sincronizacion CLI. Revisar logs\cli_sync.
) else (
  echo.
  echo Sincronizacion CLI completa. Revisar logs\cli_sync.
)
pause
