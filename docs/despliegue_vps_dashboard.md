# Despliegue VPS - Dashboard ejecutivo

Esta guia cubre la publicacion del backend Django y frontend Vue en el VPS. No reemplaza la instalacion del agente de sincronizacion dentro de la cooperativa.

Para la secuencia completa de entrega cooperativa + VPS, ver:

```text
docs\entrega_operativa_dashboard.md
```

## Componentes

- Backend: Django/DRF, solo lectura sobre la base espejo del VPS.
- Frontend: Vue compilado con Vite.
- Base: MySQL `agua_dashboard` alimentada por el agente instalado en la cooperativa.

## Variables necesarias

Crear `.env` en el directorio del proyecto en el VPS:

```env
VPS_MYSQL_HOST=
VPS_MYSQL_PORT=3306
VPS_MYSQL_DATABASE=agua_dashboard
VPS_MYSQL_USER=
VPS_MYSQL_PASSWORD=
VPS_MYSQL_SSL_MODE=preferred

DJANGO_SECRET_KEY=
DJANGO_DEBUG=0
DJANGO_ALLOWED_HOSTS=agua.vogelconsultoria.com.ar
CORS_ALLOWED_ORIGINS=https://agua.vogelconsultoria.com.ar
DASHBOARD_TOKEN_MAX_AGE=28800

DASHBOARD_ADMIN_USER=
DASHBOARD_ADMIN_PASSWORD=
DASHBOARD_SYNC_MAX_AGE_MINUTES=90
```

El usuario `VPS_MYSQL_USER` del dashboard debe tener permiso `SELECT` solamente sobre las tablas espejo.

Para habilitar usuarios creados desde el panel administrativo, ejecutar migraciones Django en el VPS:

```bash
cd /home/ferreteria/agua_dashboard_test
.venv/bin/python backend/manage.py migrate --noinput
```

El usuario definido por `DASHBOARD_ADMIN_USER` y `DASHBOARD_ADMIN_PASSWORD` queda como administrador raiz. Luego desde `#admin-users` se pueden crear usuarios adicionales con clave hasheada en SQLite.

## Usuarios MySQL sugeridos

Usar como base el template:

```text
deploy\mysql_vps_grants_template.sql
```

Roles esperados:

- `sync_writer`: usado solo por el agente instalado en la cooperativa. Tiene permisos para crear/reemplazar tablas espejo en `agua_dashboard`.
- `dashboard_reader`: usado por Django/dashboard. Debe tener solo `SELECT`.

Antes de ejecutar el template:

1. Cambiar contrasenas placeholder.
2. Reemplazar `%` por IP fija si se conoce el origen.
3. Confirmar nombre de base destino.
4. Ejecutar `SHOW GRANTS` para verificar permisos efectivos.

## Backend

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe backend\manage.py check
```

En Linux el equivalente es:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements-vps.txt
./.venv/bin/python backend/manage.py check
```

Servidor recomendado: ejecutar Django detras de Nginx con un servicio systemd/gunicorn o equivalente del VPS. El backend debe exponer `/api/`.

Plantillas incluidas:

```text
deploy\vps\agua-dashboard.service.example
deploy\vps\nginx_agua_dashboard.conf.example
deploy\vps\install_release_linux.sh
```

En Linux, despues de descomprimir el release en `/var/www/agua-dashboard` y completar `.env`:

```bash
sudo APP_DIR=/var/www/agua-dashboard bash deploy/vps/install_release_linux.sh
```

Luego adaptar/copiar `nginx_agua_dashboard.conf.example` a `/etc/nginx/sites-available/`, activar el sitio y emitir certificado HTTPS con Certbot o el mecanismo del VPS.

## Frontend

Configurar `VITE_API_BASE` si el backend no queda en `https://dominio/api` por proxy:

```powershell
cd frontend
npm ci
npm run build
```

Publicar `frontend\dist` como contenido estatico del dominio HTTPS.

## Proxy HTTPS

Regla esperada:

- `/api/` -> backend Django.
- `/` -> `frontend/dist`.

HTTPS es obligatorio antes de uso real con credenciales.

## Verificacion posterior al despliegue

1. Abrir el dominio HTTPS.
2. Iniciar sesion con usuario admin real.
3. Confirmar `Fuente: VPS MySQL`.
4. Confirmar que el estado de sincronizacion no este vencido.
5. Abrir:
   - Dashboard ejecutivo.
   - Facturacion.
   - Cobranzas.
   - Consumos.
   - Auditoria.
6. Probar un detalle diario de cobranzas.
7. Exportar CSV.
8. Revisar logs de backend ante errores.

Tambien se puede ejecutar un smoke test de API:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_dashboard.ps1 -ApiBase https://agua.vogelconsultoria.com.ar/api
```

En Linux, adaptar el chequeo con PowerShell 7 o hacer las mismas llamadas HTTP:

- `GET /api/health/`
- `POST /api/auth/login/`
- `GET /api/dashboard/summary/`
- `GET /api/audit/logs/?limit=5`

## Pendientes que no debe resolver el VPS

- La lectura de la base operativa local se hace desde la computadora de la cooperativa con `agua-dashboard-sync-agent.zip`.
- El dashboard nunca debe escribir en la base operativa de la cooperativa.
