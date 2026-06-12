# Estado de implementacion del dashboard ejecutivo

Fecha: 2026-05-30

## Entregado

- Backend Django/DRF con autenticacion por token simple.
- Frontend Vue con login, dashboard ejecutivo, filtros por periodo/zona/estado, exportacion CSV y vistas de detalle.
- Seleccion multiple de periodos.
- Indicador de carga mientras cambian filtros o se consulta el VPS.
- Auditoria de accesos, errores y eventos administrativos, visible solo para admin.
- Sincronizador MySQL para copiar tablas seleccionadas desde la cooperativa al VPS.
- Logs JSON de sincronizacion en `logs\sync`.
- Estado de ultima sincronizacion visible en el dashboard.
- Paquete portable para instalar el agente de sincronizacion en la computadora de la cooperativa:
  - `dist\agua-dashboard-sync-agent.zip`
  - `scripts\build_coop_sync_package.ps1`
- Paquete de release para VPS:
  - `dist\agua-dashboard-vps-release.zip`
  - `scripts\build_vps_release.ps1`
- Dependencias especificas de runtime VPS:
  - `requirements-vps.txt` incluye `gunicorn`
- `.env.example` para desarrollo/dashboard y `.env.example` dentro del agente portable.
- Guia de despliegue VPS:
  - `docs\despliegue_vps_dashboard.md`
- Checklist de validacion gerencial:
  - `docs\validacion_gerencial_indicadores.md`
- Hoja de entrega operativa:
  - `docs\entrega_operativa_dashboard.md`
- Nota de release:
  - `docs\release_2026-05-30.md`
- Trazabilidad contra plan original:
  - `docs\trazabilidad_plan_dashboard.md`
- Smoke test API/dashboard:
  - `scripts\smoke_dashboard.ps1`
- Smoke visual de navegador:
  - `scripts\browser_smoke.ps1`
- Verificador integral de release:
  - `scripts\verify_release.ps1`
- Checksums SHA-256 de artefactos:
  - `dist\checksums.sha256`
- Verificador de checksums:
  - `scripts\verify_checksums.ps1`
- Template de usuarios/permisos MySQL para VPS:
  - `deploy\mysql_vps_grants_template.sql`
- Templates de despliegue Linux para VPS:
  - `deploy\vps\agua-dashboard.service.example`
  - `deploy\vps\nginx_agua_dashboard.conf.example`
  - `deploy\vps\install_release_linux.sh`

## Indicadores implementados

- Clientes activos.
- Conexiones activas.
- Facturacion del periodo.
- Cobranzas del periodo desde `movcaja`.
- Deuda total.
- Deuda vencida.
- Consumo del ultimo periodo.
- Conexiones sin lectura reciente.
- Pendientes de facturacion.
- Consumos cero.
- Top deudores.
- Evolucion mensual de facturacion, cobranzas y consumo.
- Detalle diario por mes para facturacion, cobranzas y consumo.
- Detalle de cobranza diaria por socio, con cantidad de movimientos y comprobantes.
- Deuda por antiguedad.
- Deuda por zona.
- Facturacion por concepto.
- Pendientes por periodo.
- Pendientes por concepto.
- Consumo por zona.
- Importe promedio por conexion.
- Consumo promedio por conexion.
- Conexiones sin ubicacion.
- Comprobantes con estado dudoso.
- Padron por zona.
- Clientes con pagos recientes.
- Conexiones sin consumo registrado.
- Conexiones con deuda recurrente.
- Altas por periodo.
- Saltos anormales de consumo.
- Pendientes repetidos.

## Verificacion local

Ultima verificacion ejecutada:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe backend\manage.py check
cd frontend
npm run build
```

Resultado:

- `25 passed`
- `System check identified no issues`
- `vite build` correcto

Verificacion integral adicional:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify_release.ps1 -SkipBuild
```

Resultado:

- `25 passed`
- `django check` correcto
- paquete cooperativa regenerado
- release VPS regenerado
- release VPS incluye `requirements-vps.txt` y templates Linux
- smoke API correcto con `source_mode: mysql`

Verificacion integral con navegador:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify_release.ps1 -SkipBuild -BrowserSmoke
```

Resultado:

- `25 passed`
- `django check` correcto
- paquete cooperativa regenerado
- release VPS regenerado
- smoke API correcto con `source_mode: mysql`
- smoke visual correcto con capturas:
  - `C:\Users\Ventas\AppData\Local\Temp\agua-dashboard-browser-smoke\dashboard-mobile.png`
  - `C:\Users\Ventas\AppData\Local\Temp\agua-dashboard-browser-smoke\collections-day-mobile.png`
- checksums generados:
  - `dist\checksums.sha256`
- checksums verificados:
  - `scripts\verify_checksums.ps1`

## Artefactos generados

- Cooperativa: `dist\agua-dashboard-sync-agent.zip`
- VPS: `dist\agua-dashboard-vps-release.zip`
- Checksums: `dist\checksums.sha256`

## Verificacion visual

Se verifico el dashboard en viewport movil con Playwright local contra `localhost:5173`.

Captura de referencia:

```text
C:\Users\Ventas\AppData\Local\Temp\agua-dashboard-verify\dashboard-mobile-breakdowns-final.png
```

Nota: el conector de @Navegador fallo por un problema de cwd con `O:\agua_dashboard`, por eso la verificacion visual se automatizo con `scripts\browser_smoke.ps1` usando Playwright local.

## Pendientes externos para cierre total del plan

- Instalar `dist\agua-dashboard-sync-agent.zip` en una computadora dentro de la cooperativa.
- Completar `.env` del agente con credenciales reales de la base local y del VPS.
- Ejecutar `verify.ps1` en esa computadora.
- Ejecutar `run_sync.ps1` manualmente desde esa computadora y confirmar log `status: ok`.
- Registrar tarea programada desde esa computadora con `install.ps1 -RegisterTask`.
- Validar indicadores contra reportes actuales de gerencia usando `docs\validacion_gerencial_indicadores.md`.
- Crear/confirmar usuarios MySQL separados usando `deploy\mysql_vps_grants_template.sql`:
  - `sync_writer` para escritura del sincronizador.
  - `dashboard_reader` solo `SELECT` para Django/dashboard.
- Definir dominio final y publicacion HTTPS siguiendo `docs\despliegue_vps_dashboard.md`.
