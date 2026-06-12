# Agua Dashboard Ejecutivo

Proyecto separado para el dashboard ejecutivo/gerencial de la cooperativa.

## Alcance inicial

- Sincronizador local en la cooperativa.
- Copia de datos seleccionados hacia VPS.
- Backend Django + Django REST Framework.
- Frontend Vue.
- Dashboard de solo lectura sobre la copia del VPS.

## Documentacion

- `docs/plan_dashboard_ejecutivo_sync.md`
- `docs/db_inspection/dashboard_oportunidades.md`
- `docs/entrega_operativa_dashboard.md`
- `docs/estado_implementacion_dashboard.md`
- `docs/release_2026-05-30.md`
- `docs/trazabilidad_plan_dashboard.md`

## Credenciales

No versionar archivos `.env`. Crear copias locales desde `.env.example`.

## Ejecucion local

Backend:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe backend\manage.py migrate
.\.venv\Scripts\python.exe backend\manage.py runserver 127.0.0.1:8000
```

Frontend:

```powershell
cd frontend
npm install
npm run dev -- --port 5173
```

Credenciales: completar `DASHBOARD_ADMIN_USER` y `DASHBOARD_ADMIN_PASSWORD` en `.env`. No dejar claves demo en produccion.

Sin `.env`, el backend usa datos demo para validar la UX. Con `.env` completo, lee la copia MySQL del VPS.

## Usuarios del dashboard

El usuario definido en `.env` funciona como administrador raiz. Desde el panel, entrar a `Usuarios` para crear accesos adicionales y asignar si son administradores o solo lectura.

Los usuarios creados desde el panel se guardan en la base SQLite de Django con clave hasheada. En cada instalacion o despliegue nuevo ejecutar:

```powershell
.\.venv\Scripts\python.exe backend\manage.py migrate
```

## Verificacion

```powershell
.\.venv\Scripts\python.exe -m pytest
cd frontend
npm run build
```

Smoke test contra backend/API levantado:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_dashboard.ps1
```

Smoke visual contra frontend/backend levantados:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\browser_smoke.ps1
```

Verificacion integral de release:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify_release.ps1
```

Si el frontend ya fue compilado y solo queres regenerar/verificar paquetes:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify_release.ps1 -SkipBuild
```

Para incluir capturas de navegador en la verificacion:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify_release.ps1 -SkipBuild -BrowserSmoke
```

El verificador genera checksums en:

```text
dist\checksums.sha256
```

Verificar integridad de ZIPs luego de copiarlos:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify_checksums.ps1
```

## Sincronizacion

```powershell
.\.venv\Scripts\python.exe sync\sync_mysql.py --dry-run --limit 100
.\.venv\Scripts\python.exe sync\sync_mysql.py
```

Cada corrida escribe un log JSON en `logs\sync`.

## Envio llamado a asamblea

Configurar en `.env` las variables `SMTP_*` de `.env.example`. El remitente visible por defecto es `info@vogelconsultoria.com.ar`.

Previsualizar socios activos con email valido, sin enviar:

```powershell
.\.venv\Scripts\python.exe scripts\send_assembly_notice.py
```

Enviar realmente la primera tanda, respetando el limite configurado en `SMTP_HOURLY_LIMIT`:

```powershell
.\.venv\Scripts\python.exe scripts\send_assembly_notice.py --send
```

Enviar la tanda siguiente despues de una hora. Ajustar el `--offset` segun el ultimo total enviado confirmado:

```powershell
.\.venv\Scripts\python.exe scripts\send_assembly_notice.py --send --offset 100
```

El script adjunta `O:\agua\data\Llamado a Asamblea.pdf`, consulta `clientes.email` desde `COOP_MYSQL_*`, deduplica correos, omite emails invalidos, aplica `SMTP_HOURLY_LIMIT` y escribe CSV/JSON en `logs\assembly_notice`.

## Paquete para instalar en la cooperativa

Generar el paquete portable del agente de sincronizacion:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_coop_sync_package.ps1
```

El ZIP queda en:

```text
dist\agua-dashboard-sync-agent.zip
```

Ese ZIP se copia a la computadora de la cooperativa. La instalacion y verificacion estan documentadas dentro del paquete, en `README.md`.

## Permisos MySQL VPS

Template editable para crear usuarios separados:

```text
deploy\mysql_vps_grants_template.sql
```

Usar `sync_writer` para el agente de sincronizacion y `dashboard_reader` solo lectura para Django.

En la computadora de la cooperativa, registrar la tarea programada desde la carpeta descomprimida del agente:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -RegisterTask -StartTime 08:00 -IntervalMinutes 60
```

Verificar si la tarea quedo instalada y ver ultimo resultado:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -VerifyTask
```

El dashboard muestra una alerta si el ultimo log de `logs\sync` esta vencido o si la ultima sincronizacion fallo.
