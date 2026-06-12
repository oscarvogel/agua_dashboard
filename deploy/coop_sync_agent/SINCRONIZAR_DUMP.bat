@echo off
setlocal
cd /d "%~dp0"
call "%~dp0sync_dump_to_vps.bat" --pause
