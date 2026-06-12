#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/home/ferreteria/agua_dashboard_test}"
BRANCH="${BRANCH:-main}"
SERVICE_NAME="${SERVICE_NAME:-agua-dashboard.service}"
HEALTH_URL="${HEALTH_URL:-https://agua.vogelconsultoria.com.ar/api/health/}"
RUN_MIGRATIONS="${RUN_MIGRATIONS:-0}"

run_systemctl() {
  if [[ "$(id -u)" -eq 0 ]]; then
    systemctl "$@"
  else
    sudo systemctl "$@"
  fi
}

echo "==> Deploy agua-dashboard"
echo "APP_DIR=$APP_DIR"
echo "BRANCH=$BRANCH"
echo "SERVICE_NAME=$SERVICE_NAME"
echo "HEALTH_URL=$HEALTH_URL"

if [[ ! -d "$APP_DIR/.git" ]]; then
  echo "No existe un repo Git en $APP_DIR. Clonar https://github.com/oscarvogel/agua_dashboard antes de desplegar." >&2
  exit 1
fi

if [[ ! -f "$APP_DIR/.env" ]]; then
  echo "Falta $APP_DIR/.env. El deploy no crea ni sobrescribe secretos." >&2
  exit 1
fi

cd "$APP_DIR"

echo "==> Actualizando codigo desde GitHub"
git fetch origin "$BRANCH"
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"

echo "==> Preparando entorno Python"
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
if [[ -f "requirements-vps.txt" ]]; then
  .venv/bin/python -m pip install -r requirements-vps.txt
else
  .venv/bin/python -m pip install -r requirements.txt
fi

echo "==> Verificando backend"
.venv/bin/python backend/manage.py check

if [[ "$RUN_MIGRATIONS" == "1" ]]; then
  echo "==> Ejecutando migraciones"
  .venv/bin/python backend/manage.py migrate --noinput
else
  echo "==> Migraciones omitidas (RUN_MIGRATIONS=0)"
fi

if [[ -f "frontend/package.json" ]]; then
  echo "==> Compilando frontend"
  (
    cd frontend
    if [[ -f "package-lock.json" ]]; then
      npm ci
    else
      npm install
    fi
    npm run build
  )
fi

echo "==> Reiniciando servicio"
run_systemctl restart "$SERVICE_NAME"
run_systemctl status "$SERVICE_NAME" --no-pager

echo "==> Verificando health publico"
curl --fail --silent --show-error --max-time 20 "$HEALTH_URL" >/tmp/agua-dashboard-health.json
cat /tmp/agua-dashboard-health.json
echo

echo "==> Deploy finalizado"
