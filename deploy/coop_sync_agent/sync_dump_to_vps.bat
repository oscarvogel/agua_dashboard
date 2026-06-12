@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"

set "DUMP_DIR=%~dp0dump"
set "LOG_DIR=%~dp0logs\dump_sync"
if not exist "%DUMP_DIR%" mkdir "%DUMP_DIR%"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

set "STAMP=%DATE:/=-%_%TIME::=-%"
set "STAMP=%STAMP: =0%"
set "STAMP=%STAMP:,=-%"
set "LOG_FILE=%LOG_DIR%\sync-%STAMP%.log"
set "STATUS_FILE=%LOG_DIR%\sync-%STAMP%.json"

echo Inicio %DATE% %TIME% > "%LOG_FILE%"

if not exist ".env" (
  echo Falta .env. Ejecutar CONFIGURAR_ENV.bat y completar credenciales.
  echo ERROR falta .env >> "%LOG_FILE%"
  > "%STATUS_FILE%" echo {"status":"error","mode":"mysqldump","error":"falta .env"}
  goto error_pause
)

call :load_env ".env"

if "%SIMPLE_SYNC_TABLES%"=="" set "SIMPLE_SYNC_TABLES=clientes conexiones consumo cabfact detfact ctacte movcaja pendfact conceptos tablas"

if "%MYSQL_BIN_DIR%"=="" (
  set "MYSQLDUMP=mysqldump.exe"
  set "MYSQL=mysql.exe"
) else (
  set "MYSQLDUMP=%MYSQL_BIN_DIR%\mysqldump.exe"
  set "MYSQL=%MYSQL_BIN_DIR%\mysql.exe"
)

set "DUMP_FILE=%DUMP_DIR%\agua-dashboard-dump.sql"
set "SRC_CNF=%TEMP%\agua-dashboard-source-%RANDOM%.cnf"
set "DST_CNF=%TEMP%\agua-dashboard-target-%RANDOM%.cnf"

if "%MYSQL_BIN_DIR%"=="" (
  where mysqldump.exe >nul 2>nul
  if errorlevel 1 (
    echo No se encontro mysqldump.exe. Completar MYSQL_BIN_DIR en .env o agregar MySQL al PATH.
    echo No se encontro mysqldump.exe: %MYSQLDUMP% >> "%LOG_FILE%"
    goto error
  )
) else (
  if not exist "%MYSQLDUMP%" (
    echo No se encontro mysqldump.exe. Completar MYSQL_BIN_DIR en .env o agregar MySQL al PATH.
    echo No se encontro mysqldump.exe: %MYSQLDUMP% >> "%LOG_FILE%"
    goto error
  )
)

if "%MYSQL_BIN_DIR%"=="" (
  where mysql.exe >nul 2>nul
  if errorlevel 1 (
    echo No se encontro mysql.exe. Completar MYSQL_BIN_DIR en .env o agregar MySQL al PATH.
    echo No se encontro mysql.exe: %MYSQL% >> "%LOG_FILE%"
    goto error
  )
) else (
  if not exist "%MYSQL%" (
    echo No se encontro mysql.exe. Completar MYSQL_BIN_DIR en .env o agregar MySQL al PATH.
    echo No se encontro mysql.exe: %MYSQL% >> "%LOG_FILE%"
    goto error
  )
)

call :write_client_file "%SRC_CNF%" "%COOP_MYSQL_HOST%" "%COOP_MYSQL_PORT%" "%COOP_MYSQL_USER%" "%COOP_MYSQL_PASSWORD%"
call :write_client_file "%DST_CNF%" "%VPS_MYSQL_HOST%" "%VPS_MYSQL_PORT%" "%VPS_MYSQL_USER%" "%VPS_MYSQL_PASSWORD%"

echo Tablas: %SIMPLE_SYNC_TABLES% >> "%LOG_FILE%"
echo Archivo opciones origen: >> "%LOG_FILE%"
type "%SRC_CNF%" | findstr /v /i "^password=" >> "%LOG_FILE%"
echo Archivo opciones destino: >> "%LOG_FILE%"
type "%DST_CNF%" | findstr /v /i "^password=" >> "%LOG_FILE%"

echo Ejecutando mysqldump.exe...
"%MYSQLDUMP%" --defaults-extra-file="%SRC_CNF%" --single-transaction --quick --skip-lock-tables --add-drop-table --default-character-set=utf8mb4 "%COOP_MYSQL_DATABASE%" %SIMPLE_SYNC_TABLES% > "%DUMP_FILE%" 2>> "%LOG_FILE%"
if errorlevel 1 goto error

echo Quitando foreign keys incompatibles del dump...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$p=$env:DUMP_FILE; $t=[System.IO.File]::ReadAllText($p); $t=[regex]::Replace($t,'(?m)^\s*CONSTRAINT\s+`?[^` ]+`?\s+FOREIGN KEY\s+\([^\r\n]*\)\s+REFERENCES\s+[^\r\n]*,?\r?\n',''); $t=[regex]::Replace($t,',(\r?\n\)\s+ENGINE=)','$1'); [System.IO.File]::WriteAllText($p,'SET FOREIGN_KEY_CHECKS=0;'+[Environment]::NewLine+$t+[Environment]::NewLine+'SET FOREIGN_KEY_CHECKS=1;',[System.Text.Encoding]::UTF8)" >> "%LOG_FILE%" 2>> "%LOG_FILE%"
if errorlevel 1 goto error

echo Restaurando en VPS con mysql.exe...
"%MYSQL%" --defaults-extra-file="%DST_CNF%" --default-character-set=utf8mb4 "%VPS_MYSQL_DATABASE%" < "%DUMP_FILE%" 2>> "%LOG_FILE%"
if errorlevel 1 goto error

echo OK %DATE% %TIME% >> "%LOG_FILE%"
> "%STATUS_FILE%" echo {"status":"ok","mode":"mysqldump","finished_at":"%DATE% %TIME%","tables":"%SIMPLE_SYNC_TABLES%"}
del "%SRC_CNF%" >nul 2>nul
del "%DST_CNF%" >nul 2>nul
echo Sincronizacion completa. Log: %LOG_FILE%
if /i "%~1"=="--pause" pause
exit /b 0

:error
echo ERROR %DATE% %TIME% >> "%LOG_FILE%"
> "%STATUS_FILE%" echo {"status":"error","mode":"mysqldump","finished_at":"%DATE% %TIME%","log":"%LOG_FILE:\=\\%"}
del "%SRC_CNF%" >nul 2>nul
del "%DST_CNF%" >nul 2>nul
echo Fallo la sincronizacion. Revisar: %LOG_FILE%
if /i "%~1"=="--pause" pause
exit /b 1

:error_pause
echo Fallo la sincronizacion. Revisar: %LOG_FILE%
if /i "%~1"=="--pause" pause
exit /b 1

:load_env
for /f "usebackq eol=# tokens=1,* delims==" %%A in (%1) do (
  if not "%%A"=="" set "%%A=%%B"
)
exit /b 0

:write_client_file
> "%~1" echo [client]
>> "%~1" echo host=%~2
>> "%~1" echo port=%~3
>> "%~1" echo user=%~4
>> "%~1" echo password=%~5
exit /b 0
