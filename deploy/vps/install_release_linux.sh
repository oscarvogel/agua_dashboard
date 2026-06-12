#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/home/ferreteria/agua_dashboard_test}"
SERVICE_NAME="${SERVICE_NAME:-agua-dashboard}"

if [[ ! -f "$APP_DIR/.env" ]]; then
  echo "Falta $APP_DIR/.env. Copiar .env.example como .env y completar valores reales." >&2
  exit 1
fi

cd "$APP_DIR"

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
if [[ -f "requirements-vps.txt" ]]; then
  .venv/bin/python -m pip install -r requirements-vps.txt
else
  .venv/bin/python -m pip install -r requirements.txt
fi
.venv/bin/python backend/manage.py check

if [[ -f "deploy/vps/${SERVICE_NAME}.service.example" ]]; then
  cp "deploy/vps/${SERVICE_NAME}.service.example" "/etc/systemd/system/${SERVICE_NAME}.service"
else
  cp "deploy/vps/agua-dashboard.service.example" "/etc/systemd/system/${SERVICE_NAME}.service"
fi

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"
systemctl status "$SERVICE_NAME" --no-pager
