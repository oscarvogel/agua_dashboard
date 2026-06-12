@echo off
setlocal
cd /d "%~dp0"
schtasks.exe /Create /TN AguaDashboardCliSync /TR "wscript.exe \"%~dp0sync_cli_to_vps_hidden.vbs\"" /SC MINUTE /MO 60 /ST 08:00 /F
echo.
echo Tarea simple por mysql.exe creada o actualizada: AguaDashboardCliSync
echo Corre cada 60 minutos desde las 08:00 en forma silenciosa.
pause
