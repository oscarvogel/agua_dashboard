from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

import pymysql

from .sample_data import SAMPLE_ROWS


MIRROR_TABLES = ["clientes", "conexiones", "consumo", "cabfact", "detfact", "ctacte", "movcaja", "pendfact", "conceptos", "tablas"]
DASHBOARD_QUERY_TABLES = ["clientes", "conexiones", "consumo", "cabfact", "detfact", "ctacte", "movcaja", "pendfact", "conceptos", "tablas"]
SYNC_STATUS_TABLE = "dashboard_sync_status"


def has_vps_config() -> bool:
    return all(os.getenv(key) for key in ["VPS_MYSQL_HOST", "VPS_MYSQL_DATABASE", "VPS_MYSQL_USER", "VPS_MYSQL_PASSWORD"])


def check_mysql_connection() -> dict[str, Any]:
    if not has_vps_config():
        return {"state": "skipped", "message": "Base MySQL VPS no configurada", "configured": False}
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 AS ok")
                cur.fetchone()
        return {"state": "ok", "message": "Conexion MySQL correcta", "configured": True}
    except Exception as exc:
        return {
            "state": "error",
            "message": f"No se pudo conectar a MySQL ({exc.__class__.__name__})",
            "configured": True,
        }


def _connect() -> pymysql.connections.Connection:
    ssl_mode = os.getenv("VPS_MYSQL_SSL_MODE", "preferred").lower()
    ssl: dict[str, Any] | None = None if ssl_mode in {"disabled", "disable", "false", "0", "none"} else {"check_hostname": False}
    return pymysql.connect(
        host=os.environ["VPS_MYSQL_HOST"],
        port=int(os.getenv("VPS_MYSQL_PORT", "3306")),
        user=os.environ["VPS_MYSQL_USER"],
        password=os.environ["VPS_MYSQL_PASSWORD"],
        database=os.environ["VPS_MYSQL_DATABASE"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        ssl=ssl,
        connect_timeout=5,
        read_timeout=30,
        write_timeout=30,
    )


def fetch_rows(limit: int | None = None) -> tuple[str, dict[str, list[dict[str, Any]]]]:
    if not has_vps_config():
        return "demo", SAMPLE_ROWS

    rows: dict[str, list[dict[str, Any]]] = {}
    with _connect() as conn:
        with conn.cursor() as cur:
            for table in DASHBOARD_QUERY_TABLES:
                if limit:
                    cur.execute(f"SELECT * FROM `{table}` LIMIT %s", (limit,))
                else:
                    cur.execute(f"SELECT * FROM `{table}`")
                rows[table] = list(cur.fetchall())
    return "mysql", rows


def latest_database_sync_status() -> dict[str, Any] | None:
    if not has_vps_config():
        return None
    with _connect() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    f"SELECT started_at, finished_at, status, error, tables_json FROM `{SYNC_STATUS_TABLE}` "
                    "ORDER BY id DESC LIMIT 1"
                )
            except pymysql.err.ProgrammingError:
                return None
            row = cur.fetchone()
    if not row:
        return None
    status = str(row.get("status") or "").lower()
    state = "ok" if status in {"", "ok"} else "error"
    finished = row.get("finished_at")
    if isinstance(finished, datetime):
        finished_at = finished.astimezone(UTC).isoformat(timespec="seconds")
    else:
        finished_at = str(finished) if finished else None
    tables_json = row.get("tables_json") or "[]"
    try:
        import json

        tables = json.loads(tables_json)
    except (TypeError, ValueError):
        tables = []
    return {
        "state": state,
        "message": "Sincronizacion correcta" if state == "ok" else (row.get("error") or "La ultima sincronizacion fallo"),
        "started_at": str(row.get("started_at")) if row.get("started_at") else None,
        "finished_at": finished_at,
        "tables": tables,
        "source": "database",
    }
