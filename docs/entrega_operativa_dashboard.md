# Entrega operativa - Dashboard ejecutivo

Fecha: 2026-05-30

Esta hoja resume que entregar, donde instalarlo y como verificarlo.

Nota de release:

```text
docs\release_2026-05-30.md
```

Trazabilidad contra el plan original:

```text
docs\trazabilidad_plan_dashboard.md
```

## Artefactos

| Destino | Archivo | Uso |
| --- | --- | --- |
| Computadora de la cooperativa | `dist\agua-dashboard-sync-agent.zip` | Agente que lee la base local `agua` y sincroniza al VPS. |
| VPS | `dist\agua-dashboard-vps-release.zip` | Backend Django, frontend compilado, docs y templates de despliegue. |
| Control de integridad | `dist\checksums.sha256` | Hashes SHA-256 para verificar que los ZIPs llegaron intactos. |

## Verificacion antes de copiar

Ejecutar desde el proyecto:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify_release.ps1 -SkipBuild -BrowserSmoke
```

Resultado esperado:

- tests backend/sync en verde;
- `django check` correcto;
- ZIP cooperativa regenerado;
- ZIP VPS regenerado;
- checksums escritos y verificados;
- smoke API correcto;
- smoke visual con capturas moviles.

## Instalacion en la cooperativa

1. Copiar `dist\agua-dashboard-sync-agent.zip` a la computadora de la cooperativa.
2. Descomprimir en una carpeta fija, por ejemplo:

```powershell
C:\agua-dashboard-sync-agent
```

3. Copiar `.env.example` como `.env` y completar:

- credenciales de la base local `agua`;
- credenciales `sync_writer` del VPS.

4. Instalar dependencias:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

En Windows 7 usar el instalador compatible:

```text
INSTALAR_WINDOWS7.bat
```

Ese instalador copia el agente a `C:\agua-dashboard-sync-agent`, crea la tarea con `schtasks.exe` y la deja ejecutando cada 60 minutos en forma silenciosa mediante `run_sync_hidden.vbs`.

5. Verificar conectividad y dry-run:

```powershell
powershell -ExecutionPolicy Bypass -File .\verify.ps1
```

6. Ejecutar una sincronizacion manual:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_sync.ps1
```

7. Confirmar log JSON con `status: ok` en:

```text
logs\sync
```

8. Registrar tarea programada:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -RegisterTask -StartTime 08:00 -IntervalMinutes 60
```

9. Ver estado de tarea:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -VerifyTask
```

## Instalacion en VPS

1. Copiar `dist\agua-dashboard-vps-release.zip` al VPS.
2. Descomprimir en:

```text
/var/www/agua-dashboard
```

3. Copiar `.env.example` como `.env` y completar:

- credenciales `dashboard_reader`;
- `DJANGO_SECRET_KEY`;
- `DJANGO_ALLOWED_HOSTS`;
- `CORS_ALLOWED_ORIGINS`;
- usuario admin real del dashboard.

4. Crear usuarios MySQL usando como base:

```text
deploy\mysql_vps_grants_template.sql
```

5. En Linux, instalar servicio:

```bash
sudo APP_DIR=/var/www/agua-dashboard bash deploy/vps/install_release_linux.sh
```

6. Configurar Nginx desde:

```text
deploy\vps\nginx_agua_dashboard.conf.example
```

7. Publicar con HTTPS.

8. Ejecutar smoke API:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_dashboard.ps1 -ApiBase https://DOMINIO/api
```

## Validacion gerencial

Usar:

```text
docs\validacion_gerencial_indicadores.md
```

Validar como minimo:

- facturacion del periodo;
- cobranzas del periodo desde `movcaja`;
- deuda total;
- deuda vencida;
- pendientes de facturacion;
- consumo ultimo periodo;
- conexiones/clientes activos.

## Criterio de aceptacion

El proyecto queda aceptado cuando:

- el agente sincroniza desde la computadora de la cooperativa con `status: ok`;
- la tarea programada queda instalada y con ultimo resultado correcto;
- el VPS sirve el dashboard por HTTPS;
- el dashboard muestra `Fuente: VPS MySQL`;
- el smoke API pasa en el dominio final;
- la validacion gerencial no tiene diferencias pendientes de definicion.
