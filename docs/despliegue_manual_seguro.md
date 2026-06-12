# Despliegue manual seguro

Proyecto: Agua Dashboard Cooperativa Garuhape-Mi

## Alcance

Estas instrucciones preparan un despliegue manual controlado del dashboard en `https://agua.vogelconsultoria.com.ar`.
No incluyen despliegue automatico, cambios directos de Nginx, rotacion de secretos ni envio de alertas.

## Datos productivos

- Ruta Linux: `/home/ferreteria/agua_dashboard_test`
- Servicio systemd: `agua-dashboard.service`
- URL interna: `http://127.0.0.1:8010`
- API interna: `http://127.0.0.1:8010/api/`
- Health publico: `https://agua.vogelconsultoria.com.ar/api/health/`
- Rama esperada: `main`

## Prechequeos locales

Ejecutar desde la raiz del proyecto:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe backend\manage.py check
cd frontend
npm run build
cd ..
```

Si alguno falla, no continuar con el despliegue.

## Preparacion del release

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify_release.ps1
```

Este paso valida tests, check de Django, build frontend, paquete de sincronizacion, release VPS, checksums y smoke API local salvo que se indiquen flags explicitos.

## Despliegue en Linux

### Opcion recomendada: deploy desde GitHub

Ejecutar en el servidor, desde `/home/ferreteria/agua_dashboard_test`:

```bash
bash deploy.sh
```

El script:

- actualiza `main` desde GitHub con `git pull --ff-only`;
- no crea ni sobrescribe `.env`;
- instala/actualiza dependencias Python;
- ejecuta `backend/manage.py check`;
- omite migraciones salvo `RUN_MIGRATIONS=1`;
- compila el frontend Vue/Vite;
- reinicia `agua-dashboard.service`;
- valida `https://agua.vogelconsultoria.com.ar/api/health/`.

Si el cambio requiere migraciones:

```bash
RUN_MIGRATIONS=1 bash deploy.sh
```

### Opcion de instalacion de release

1. Copiar el release validado al servidor.
2. Descomprimirlo en `/home/ferreteria/agua_dashboard_test`.
3. Confirmar que el `.env` productivo existe en el servidor y no fue sobrescrito.
4. Revisar que las variables `VPS_MYSQL_*` apunten a la base espejo correcta.
5. Ejecutar:

```bash
cd /home/ferreteria/agua_dashboard_test
bash deploy/vps/install_release_linux.sh
```

No modificar Nginx en este paso salvo revision manual explicita.

## Migraciones

Las migraciones no son obligatorias en todos los despliegues. Ejecutarlas solo cuando haya cambios Django que lo requieran:

```bash
cd /home/ferreteria/agua_dashboard_test
.venv/bin/python backend/manage.py migrate --noinput
```

## Validacion post-despliegue

Desde una maquina externa o desde el entorno de operacion:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_dashboard.ps1 -ApiBase https://agua.vogelconsultoria.com.ar/api
```

Comprobar tambien:

- `GET https://agua.vogelconsultoria.com.ar/api/health/` devuelve HTTP 200 si no hay errores criticos.
- `checks.django_database.state` esta en `ok`.
- `checks.mysql.state` esta en `ok` cuando `VPS_MYSQL_*` esta configurado.
- `checks.sync.state` esta en `ok` o `warning` segun frescura de sincronizacion.

Si el health devuelve HTTP 503, no activar monitoreo como saludable hasta revisar el check en estado `error`.

## Alertas

El servicio debe considerarse de prioridad `baja`, con alertas por Telegram y email configuradas fuera del repositorio. No guardar tokens, destinatarios privados ni credenciales en Git.
