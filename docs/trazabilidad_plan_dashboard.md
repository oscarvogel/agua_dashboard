# Trazabilidad contra plan original

Referencia: `docs\plan_dashboard_ejecutivo_sync.md`

Fecha: 2026-05-30

## Resumen

| Area | Estado | Evidencia |
| --- | --- | --- |
| Inspeccion de base operativa | Completo | `docs\db_inspection\*.csv`, `docs\db_inspection\summary.json`, `docs\db_inspection\dashboard_oportunidades.md` |
| Dataset ejecutivo | Completo | `sync\sync_mysql.py`, `backend\dashboard_api\repository.py` |
| Sincronizador local | Listo para instalar | `dist\agua-dashboard-sync-agent.zip`, `deploy\coop_sync_agent\README.md` |
| Copia VPS | Implementada y probada desde datos actuales | logs `logs\sync\sync-*.json`, API `source_mode: mysql` |
| Backend dashboard | Completo para MVP gerencial | `backend\dashboard_api`, tests `25 passed` |
| Frontend dashboard | Completo para MVP gerencial | `frontend\src`, smoke visual OK |
| Auditoria/errores admin | Completo | `backend\dashboard_api\audit.py`, vista `#audit`, tests |
| Release VPS | Listo para desplegar | `dist\agua-dashboard-vps-release.zip` |
| Validacion gerencial | Pendiente externo | `docs\validacion_gerencial_indicadores.md` |
| Instalacion en cooperativa | Pendiente externo | requiere ejecutar paquete en PC de cooperativa |
| Publicacion HTTPS | Pendiente externo | requiere dominio/VPS final |

## Requisitos del plan

| Requisito | Estado | Evidencia / siguiente accion |
| --- | --- | --- |
| No modificar base operativa | Implementado | Dashboard consulta VPS; sincronizador lee COOP y escribe VPS. |
| Sincronizador con usuario lectura COOP | Preparado | `.env.example` del agente; requiere credencial real en cooperativa. |
| Normalizar fechas invalidas | Implementado | `clean_date` en `sync_mysql.py`, `normalize_date` en `metrics.py`, tests. |
| Enviar datos al VPS | Implementado | `sync_mysql.py`, logs reales de sync. |
| Registrar logs de cada corrida | Implementado | `write_sync_log`, `logs\sync`. |
| Alertar si falla/vieja sync | Implementado en dashboard | `sync_status.py`, alerta visual en frontend. |
| Usuario VPS sync_writer | Template listo | `deploy\mysql_vps_grants_template.sql`; pendiente ejecutar en VPS. |
| Usuario VPS dashboard_reader SELECT | Template listo | `deploy\mysql_vps_grants_template.sql`; pendiente ejecutar en VPS. |
| Backend Django + DRF | Implementado | `backend`, `manage.py check` OK. |
| Autenticacion | Implementado | `auth.py`, login frontend/API. |
| Endpoints agregados | Implementado | `DashboardView`, `AuditLogView`, `HealthView`. |
| Consultas sobre copia VPS | Implementado | `repository.py`, API smoke `source_mode: mysql`. |
| Tests de consultas | Implementado | `backend\tests\test_dashboard_metrics.py`. |
| Frontend Vue | Implementado | `frontend\src\App.vue`. |
| Login | Implementado | vista login + API. |
| Dashboard ejecutivo | Implementado | KPIs, series, breakdowns. |
| Filtros periodo/zona/estado | Implementado | frontend + API query params. |
| Seleccion multiple de periodos | Implementado | selector checkbox, `periods`. |
| Graficos principales | Implementado | barras facturacion/cobranzas. |
| Tablas resumidas | Implementado | top deudores, calidad, breakdowns. |
| Exportaciones | Implementado | CSV desde frontend. |
| Detalle diario por mes | Implementado | `#billing-day`, `#collections-day`, `#consumption-day`; cobranzas permite abrir dia y ver socio/comprobante. |
| Auditoria solo admin | Implementado | `AuditLogView` + nav admin. |
| Manejo de errores registrado | Implementado | `record_event` en login/dashboard/audit. |
| Publicar con HTTPS | Pendiente externo | `docs\despliegue_vps_dashboard.md`, templates Nginx/systemd. |
| Validar con gerencia | Pendiente externo | `docs\validacion_gerencial_indicadores.md`. |

## Indicadores

| Indicador propuesto | Estado | Evidencia |
| --- | --- | --- |
| Conexiones activas | Implementado | `summary.conexiones_activas` |
| Clientes activos | Implementado | `summary.clientes_activos` |
| Facturacion del mes/periodo | Implementado | `summary.facturacion_mes` |
| Cobranzas del mes/periodo | Implementado | `summary.cobranzas_mes`, usa `movcaja` |
| Deuda total estimada | Implementado | `summary.deuda_total` |
| Deuda vencida | Implementado | `summary.deuda_vencida` |
| Consumos ultimo periodo | Implementado | `summary.consumo_ultimo_periodo` |
| Conexiones sin lectura reciente | Implementado | `summary.conexiones_sin_lectura_reciente` |
| Pendientes de facturacion | Implementado | `summary.pendiente_facturacion` |
| Facturacion mensual | Implementado | `series.monthly.facturacion` |
| Facturacion por concepto | Implementado | `breakdowns.facturacion_concepto` |
| Emitido vs pagado | Parcial | facturacion vs cobranzas mensual; requiere validacion gerencial para regla final. |
| Facturas vencidas | Parcial | deuda vencida agregada; no hay listado individual. |
| Importe promedio por conexion | Implementado | `summary.importe_promedio_conexion`. |
| Evolucion intermensual | Implementado | grafico mensual. |
| Cobranzas por dia/mes | Implementado | `series.daily`, `series.monthly`; drill-down por socio en `breakdowns.cobranzas_por_dia_socio`. |
| Pagos aplicados | Parcial avanzado | cobranzas desde `movcaja` con detalle por socio/dia; conciliacion contable final pendiente. |
| Comprobantes anulados/dudosos | Implementado | `summary.comprobantes_estado_dudoso`, `breakdowns.comprobantes_estado`. |
| Conciliacion caja/facturas/ctacte | Pendiente | requiere definicion contable. |
| Clientes con pagos recientes | Implementado | `breakdowns.clientes_pagos_recientes`, `summary.clientes_con_pagos_recientes`. |
| Deuda por antiguedad | Implementado | `breakdowns.deuda_antiguedad` |
| Top deudores | Implementado | `top_deudores` |
| Deuda por zona | Implementado | `breakdowns.deuda_zona` |
| Conexiones con deuda recurrente | Implementado inicial | `summary.conexiones_con_deuda_recurrente`; regla sujeta a validacion gerencial. |
| Consumo por periodo | Implementado | `series.monthly.consumo` |
| Consumo promedio por conexion | Implementado | `summary.consumo_promedio_conexion`. |
| Conexiones con consumo cero | Implementado | `summary.consumos_cero` |
| Saltos anormales de consumo | Implementado inicial | `summary.saltos_anormales_consumo`, `breakdowns.saltos_consumo`; regla sujeta a validacion gerencial. |
| Conexiones sin consumo registrado | Implementado | `summary.conexiones_sin_consumo_registrado`. |
| Consumo por zona | Implementado | `breakdowns.consumo_zona` |
| Conexiones activas/inactivas | Implementado | `breakdowns.padron_estado_zona`. |
| Clientes activos/inactivos | Implementado | `breakdowns.padron_estado_zona`. |
| Distribucion por zona | Implementado | `breakdowns.padron_zona`, deuda/consumo por zona. |
| Conexiones sin ubicacion | Implementado | `summary.conexiones_sin_ubicacion`. |
| Datos incompletos | Parcial | panel calidad general. |
| Altas por periodo | Implementado inicial | `breakdowns.altas_periodo`; requiere validar confiabilidad de `fechaingreso`. |
| Pendientes por concepto | Implementado | `breakdowns.pendientes_concepto` |
| Pendientes por periodo | Implementado | `breakdowns.pendientes_periodo` |
| Monto pendiente | Implementado | `summary.pendiente_facturacion` |
| Pendientes repetidos | Implementado inicial | `summary.pendientes_repetidos`, `breakdowns.pendientes_repetidos`; regla sujeta a validacion gerencial. |

## Gate de release

Comando recomendado:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify_release.ps1 -SkipBuild -BrowserSmoke
```

Ultimo resultado registrado:

- `25 passed`
- `django check` correcto
- ZIP cooperativa regenerado
- ZIP VPS regenerado
- checksums escritos y verificados
- smoke API correcto
- smoke visual correcto

## Cierre

El software y los artefactos de release estan listos. El cierre total del objetivo requiere ejecutar las tareas externas:

1. instalar agente en computadora de la cooperativa;
2. ejecutar sync real desde esa computadora;
3. instalar release en VPS con HTTPS;
4. validar indicadores con gerencia.
