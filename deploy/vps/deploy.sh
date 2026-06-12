#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/home/ferreteria/agua_dashboard_test}"
BRANCH="${BRANCH:-main}"
SERVICE_NAME="${SERVICE_NAME:-agua-dashboard.service}"
PUBLIC_URL="${PUBLIC_URL:-https://agua.vogelconsultoria.com.ar/}"
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
echo "PUBLIC_URL=$PUBLIC_URL"
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

check_url() {
  local label="$1"
  local url="$2"
  local output_file="$3"

  echo "==> Verificando $label: $url"
  curl --fail --silent --show-error --max-time 20 "$url" >"$output_file"
}

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
  echo "==> Publicando frontend en frontend_dist"
  rm -rf frontend_dist.next
  cp -a frontend/dist frontend_dist.next
  if [[ -d "frontend_dist" ]]; then
    rm -rf frontend_dist.previous
    mv frontend_dist frontend_dist.previous
  fi
  mv frontend_dist.next frontend_dist
fi

echo "==> Reiniciando servicio"
run_systemctl restart "$SERVICE_NAME"
run_systemctl status "$SERVICE_NAME" --no-pager

check_url "health publico" "$HEALTH_URL" /tmp/agua-dashboard-health.json
cat /tmp/agua-dashboard-health.json
echo

if ! check_url "home publica" "$PUBLIC_URL" /tmp/agua-dashboard-home.html; then
  echo "La home publica fallo despues del deploy." >&2
  if [[ -d "frontend_dist.previous" ]]; then
    echo "Restaurando frontend_dist anterior." >&2
    rm -rf frontend_dist
    mv frontend_dist.previous frontend_dist
  fi
  exit 1
fi

echo "==> Deploy finalizado"
