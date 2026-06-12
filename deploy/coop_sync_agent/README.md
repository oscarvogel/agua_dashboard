# Agente de sincronizacion - Cooperativa Agua

Este paquete se instala en una computadora dentro de la cooperativa. Desde ahi lee la base operativa local `agua` y actualiza la copia del VPS que usa el dashboard ejecutivo.

## Contenido

- `sync_mysql.py`: sincronizador de tablas seleccionadas.
- `requirements.txt`: dependencias Python minimas.
- `.env.example`: plantilla de credenciales.
- `LEER_PRIMERO.txt`: guia corta para instalar en la computadora de la cooperativa.
- `install.ps1`: crea entorno virtual, instala dependencias y opcionalmente registra la tarea programada.
- `install_win7.ps1`: instalador compatible con Windows 7 usando `schtasks.exe`.
- `INSTALAR_WIN7_COMPLETO.bat`: instalador para Windows 7 que usa `sync.exe` incluido en el paquete completo.
- `run_sync.ps1`: ejecuta una sincronizacion real y guarda logs.
- `run_sync_hidden.vbs`: ejecuta `run_sync.ps1` en forma silenciosa para la tarea programada.
- `verify.ps1`: valida configuracion, dependencias y conectividad.
- `sync_dump_to_vps.bat`: modo simple sin Python, usa `mysqldump.exe` y `mysql.exe` para reemplazar tablas completas en el VPS.
- `SINCRONIZAR_DUMP.bat`: prueba manual del modo dump; deja la ventana abierta al terminar.
- `sync_dump_to_vps_hidden.vbs`: ejecuta el modo dump en forma silenciosa.
- `PROGRAMAR_DUMP_WINDOWS7.bat`: programa el modo dump cada 60 minutos en Windows 7.
- `sync_cli_to_vps.ps1`: modo simple sin Python ni `sync.exe`, usa solo `mysql.exe` para exportar columnas seleccionadas y cargarlas en el VPS.
- `SINCRONIZAR_CLI.bat`: prueba manual del modo CLI; deja la ventana abierta al terminar.
- `sync_cli_to_vps_hidden.vbs`: ejecuta el modo CLI en forma silenciosa.
- `PROGRAMAR_CLI_WINDOWS7.bat`: programa el modo CLI cada 60 minutos en Windows 7.
- `CONFIGURAR_ENV.bat`, `INSTALAR.bat`, `VERIFICAR.bat`, `SINCRONIZAR.bat`, `PROGRAMAR_TAREA.bat`: accesos directos para ejecutar los pasos principales en Windows.
- `INSTALAR_WINDOWS7.bat`, `VER_TAREA_WINDOWS7.bat`: instalacion y control de tarea en Windows 7.

## Instalacion recomendada en Windows 7

Windows 7 no incluye los cmdlets modernos `Register-ScheduledTask` y `Get-ScheduledTask`. Para esa maquina usar este flujo:

Si se entrega el paquete completo `agua-dashboard-sync-agent-win7-full.zip`, ejecutar:

```text
INSTALAR_WIN7_COMPLETO.bat
```

Ese instalador usa `sync.exe` incluido en el ZIP. No instala Python, no usa internet y no requiere dependencias adicionales en la cooperativa.

1. Descomprimir el paquete en cualquier carpeta temporal.
2. Ejecutar doble clic en:

```text
INSTALAR_WINDOWS7.bat
```

El instalador copia el agente a:

```text
C:\agua-dashboard-sync-agent
```

Tambien crea el entorno Python, instala dependencias, crea `.env` si falta y registra una tarea programada con `schtasks.exe`.

La tarea queda configurada como:

```text
AguaDashboardSync
```

y ejecuta cada 60 minutos desde las 08:00 en forma silenciosa mediante:

```text
wscript.exe C:\agua-dashboard-sync-agent\run_sync_hidden.vbs
```

Despues de instalar:

1. Completar `C:\agua-dashboard-sync-agent\.env`.
2. Ejecutar `C:\agua-dashboard-sync-agent\VERIFICAR.bat`.
3. Ejecutar `C:\agua-dashboard-sync-agent\SINCRONIZAR.bat`.
4. Confirmar que el ultimo JSON en `C:\agua-dashboard-sync-agent\logs\sync` tenga `status: ok`.

Para consultar la tarea en Windows 7:

```text
C:\agua-dashboard-sync-agent\VER_TAREA_WINDOWS7.bat
```

## Modo simple por dump MySQL

Si se quiere evitar Python y hacer algo mas directo, el paquete incluye:

```text
sync_dump_to_vps.bat
```

Ese script hace:

1. Lee `.env`.
2. Ejecuta `mysqldump.exe` contra la base local de la cooperativa.
3. Genera `dump\agua-dashboard-dump.sql`.
4. Ejecuta `mysql.exe` contra la base del VPS.
5. Reemplaza tablas completas usando `--add-drop-table`.
6. Guarda logs en `logs\dump_sync`.

Requisitos:

- `mysqldump.exe` y `mysql.exe` instalados en la PC.
- Si no estan en `PATH`, completar `MYSQL_BIN_DIR` en `.env`.
- Usuario local con `SELECT`.
- Usuario VPS con permisos para `DROP`, `CREATE`, `INSERT`, `ALTER`, `INDEX`.

Variables especificas:

```text
MYSQL_BIN_DIR=C:\Program Files\MySQL\MySQL Server 5.7\bin
SIMPLE_SYNC_TABLES=clientes conexiones consumo cabfact detfact ctacte movcaja pendfact conceptos tablas
```

Prueba manual:

```text
SINCRONIZAR_DUMP.bat
```

Programar cada 60 minutos en Windows 7:

```text
PROGRAMAR_DUMP_WINDOWS7.bat
```

Este modo es mas simple, pero tiene una diferencia importante: copia la estructura y datos tal como estan en la base local. No limpia fechas invalidas ni normaliza columnas como el sincronizador Python.

## Modo CLI MySQL para Windows 7

Si `sync.exe` no inicia en Windows 7 por falta de runtimes de Microsoft, usar este modo antes que el dump completo:

```text
SINCRONIZAR_CLI.bat
```

Este modo no usa Python, no usa `sync.exe` y no usa `mysqldump.exe`. Solo necesita `mysql.exe`, que muchas instalaciones de MySQL ya traen.

Hace:

1. Lee `.env`.
2. Exporta desde la base local solo las columnas que usa el dashboard.
3. Limpia fechas invalidas como `0000-00-00`.
4. Crea o ajusta las tablas espejo en el VPS.
5. Reemplaza los datos de cada tabla espejo con `INSERT` por lotes.
6. Guarda logs en `logs\cli_sync`.

No usa `LOAD DATA LOCAL INFILE`, porque muchos servidores MySQL lo tienen deshabilitado por seguridad.

Requisitos:

- `mysql.exe` instalado en la PC.
- Si no esta en `PATH`, completar `MYSQL_BIN_DIR` en `.env`.
- `MYSQL_CHARSET=utf8` en `.env` para clientes MySQL viejos. Cambiar a `utf8mb4` solo si el cliente lo soporta.
- Usuario local con `SELECT`.
- Usuario VPS con permisos para `CREATE`, `ALTER`, `TRUNCATE` e `INSERT`.

Prueba manual:

```text
SINCRONIZAR_CLI.bat
```

Programar cada 60 minutos en Windows 7:

```text
PROGRAMAR_CLI_WINDOWS7.bat
```

La tarea queda como:

```text
AguaDashboardCliSync
```

## Instalacion

1. Copiar la carpeta del paquete a la computadora de la cooperativa, por ejemplo:

```powershell
C:\agua-dashboard-sync-agent
```

2. Crear y completar `.env` con credenciales reales:

```powershell
Copy-Item .env.example .env
notepad .env
```

Tambien se puede hacer doble clic en:

```text
CONFIGURAR_ENV.bat
```

3. Ejecutar instalacion:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

Si Python no esta registrado como `py`, se puede indicar el ejecutable:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -PythonCommand python
```

Tambien se puede hacer doble clic en:

```text
INSTALAR.bat
```

4. Verificar:

```powershell
powershell -ExecutionPolicy Bypass -File .\verify.ps1
```

O doble clic en:

```text
VERIFICAR.bat
```

5. Probar una corrida manual:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_sync.ps1
```

O doble clic en:

```text
SINCRONIZAR.bat
```

## Tarea programada

Para registrar la sincronizacion cada 60 minutos durante 12 horas desde las 08:00:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -RegisterTask -StartTime 08:00 -IntervalMinutes 60
```

O doble clic en:

```text
PROGRAMAR_TAREA.bat
```

Para ver el estado de la tarea:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -VerifyTask
```

## Logs

Cada corrida genera un JSON en:

```text
logs\sync
```

El dashboard usa esos logs para mostrar si la ultima sincronizacion esta vieja o fallo.
