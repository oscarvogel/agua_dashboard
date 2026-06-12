@echo off
setlocal
cd /d "%~dp0"
if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo Se creo .env desde .env.example.
) else (
  echo Ya existe .env. Se abre el archivo actual.
)
notepad ".env"
