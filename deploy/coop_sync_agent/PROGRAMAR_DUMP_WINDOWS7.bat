@echo off
setlocal
cd /d "%~dp0"
schtasks.exe /Create /TN AguaDashboardDumpSync /TR "wscript.exe \"%~dp0sync_dump_to_vps_hidden.vbs\"" /SC MINUTE /MO 60 /ST 08:00 /F
echo.
echo Tarea simple por dump creada o actualizada: AguaDashboardDumpSync
echo Corre cada 60 minutos desde las 08:00 en forma silenciosa.
pause
