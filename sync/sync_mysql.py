from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pymysql
from dotenv import load_dotenv


def resolve_runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


SCRIPT_DIR = resolve_runtime_root()
PROJECT_ROOT = SCRIPT_DIR if (SCRIPT_DIR / ".env").exists() else SCRIPT_DIR.parents[0]
MIRROR_TABLES = {
    "clientes": ["idcliente", "nombre", "direccion", "telefono", "tipdoc", "numdoc", "sitiva", "zona", "activo", "cuit"],
    "conexiones": ["idconexion", "idcliente", "direccion", "ubicacion", "zona", "ultmed", "activo", "socio", "fechaingreso", "integracion"],
    "consumo": ["idconsumo", "idconexion", "fechatoma", "estadomed", "periodo", "consumo", "facturado"],
    "cabfact": ["IdCabFact", "Tipo", "Clase", "numero", "idcliente", "idconexion", "fechaem", "fechaven", "fechapag", "neto", "iva", "dgr", "periodo", "estado"],
    "detfact": ["idDetFact", "idCabfact", "idconcepto", "neto", "iva", "dgr", "detalle"],
    "ctacte": ["idCtaCte", "Fecha", "idFactura", "idRecibo", "Monto", "_usuario", "_fecha", "_hora"],
    "movcaja": ["idMovCaja", "Fecha", "idTipoComp", "numcomp", "importe", "banco", "sucursal", "numche", "vence", "estado", "idCabFact", "idCliente"],
    "pendfact": ["idpendfact", "idconexion", "idcliente", "idconcepto", "periodo", "neto", "iva", "dgr", "detalle", "facturado"],
    "conceptos": ["idconcepto", "detalle", "importe", "importenosocio", "activo", "tipoiva", "agua", "generainteres"],
    "tablas": ["ID_Tabla", "ID_TipTab", "Valor", "Descrip", "Estado", "F_Alta", "F_Baja", "Usuario"],
}

DATE_KEYS = {"fechaem", "fechaven", "fechapag", "Fecha", "_fecha", "vence", "fechatoma", "fechaingreso", "F_Alta", "F_Baja"}

DECIMAL_KEYS = {"neto", "iva", "dgr", "Monto", "importe", "importenosocio", "consumo", "integracion", "ultmed", "descuento", "Saldo"}
INT_KEYS = {
    "idcliente",
    "idconexion",
    "idconsumo",
    "IdCabFact",
    "idDetFact",
    "idCabfact",
    "idconcepto",
    "idCtaCte",
    "idFactura",
    "idRecibo",
    "idMovCaja",
    "idTipoComp",
    "idCliente",
    "idCabFact",
    "idpendfact",
    "ID_Tabla",
    "ID_TipTab",
    "periodo",
    "zona",
    "activo",
    "socio",
    "facturado",
    "estado",
    "Estado",
}

MIRROR_INDEXES = {
    "clientes": [("idx_clientes_zona_activo", ["zona", "activo"])],
    "conexiones": [("idx_conexiones_cliente", ["idcliente"]), ("idx_conexiones_zona_activo", ["zona", "activo"])],
    "consumo": [("idx_consumo_periodo", ["periodo"]), ("idx_consumo_conexion", ["idconexion"])],
    "cabfact": [("idx_cabfact_fechaem", ["fechaem"]), ("idx_cabfact_cliente", ["idcliente"]), ("idx_cabfact_conexion", ["idconexion"])],
    "detfact": [("idx_detfact_cabfact", ["idCabfact"]), ("idx_detfact_concepto", ["idconcepto"])],
    "ctacte": [("idx_ctacte_factura", ["idFactura"]), ("idx_ctacte_fecha", ["Fecha"])],
    "movcaja": [("idx_movcaja_fecha", ["Fecha"]), ("idx_movcaja_cabfact", ["idCabFact"])],
    "pendfact": [("idx_pendfact_periodo", ["periodo"]), ("idx_pendfact_cliente", ["idcliente"]), ("idx_pendfact_conexion", ["idconexion"])],
    "conceptos": [("idx_conceptos_tipoiva", ["tipoiva"])],
    "tablas": [("idx_tablas_tipo", ["ID_TipTab"])],
}
SYNC_STATUS_TABLE = "dashboard_sync_status"


def clean_date(value: Any) -> str | None:
    if value in {None, "", "0000-00-00", "0000-00-00 00:00:00"}:
        return None
    if isinstance(value, datetime):
        parsed = value.date()
    elif isinstance(value, date):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value)[:10]).date()
        except ValueError:
            return None
    if parsed.year > 2035:
        return None
    return parsed.isoformat()


def clean_int(value: Any) -> int | None:
    if value in {None, ""}:
        return None
    if isinstance(value, (bytes, bytearray)):
        return int.from_bytes(value, byteorder="big")
    text = str(value).strip()
    if not text or not text.lstrip("-").isdigit():
        return None
    return int(text)


def clean_row(row: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in row.items():
        if key in DATE_KEYS:
            cleaned[key] = clean_date(value)
        elif key in INT_KEYS:
            cleaned[key] = clean_int(value)
        elif isinstance(value, (bytes, bytearray)):
            cleaned[key] = int.from_bytes(value, byteorder="big")
        elif isinstance(value, Decimal):
            cleaned[key] = str(value)
        else:
            cleaned[key] = value
    return cleaned


def connect(prefix: str) -> pymysql.connections.Connection:
    ssl_mode = os.getenv(f"{prefix}_MYSQL_SSL_MODE", "preferred").lower()
    ssl: dict[str, Any] | None = None if ssl_mode in {"disabled", "disable", "false", "0", "none"} else {"check_hostname": False}
    return pymysql.connect(
        host=os.environ[f"{prefix}_MYSQL_HOST"],
        port=int(os.getenv(f"{prefix}_MYSQL_PORT", "3306")),
        user=os.environ[f"{prefix}_MYSQL_USER"],
        password=os.environ[f"{prefix}_MYSQL_PASSWORD"],
        database=os.environ[f"{prefix}_MYSQL_DATABASE"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        ssl=ssl,
    )


def ident(value: str) -> str:
    return "`" + value.replace("`", "``") + "`"


def column_type(column: str) -> str:
    if column in DATE_KEYS:
        return "DATE NULL"
    if column in DECIMAL_KEYS:
        return "DECIMAL(14,2) NULL"
    if column in INT_KEYS:
        return "BIGINT NULL"
    return "VARCHAR(255) NULL"


def build_create_table_sql(table: str, columns: list[str]) -> str:
    defs = ", ".join(f"{ident(col)} {column_type(col)}" for col in columns)
    return f"CREATE TABLE IF NOT EXISTS {ident(table)} ({defs}) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"


def read_table(conn: pymysql.connections.Connection, table: str, columns: list[str], limit: int | None) -> list[dict[str, Any]]:
    sql = f"SELECT {', '.join(ident(col) for col in columns)} FROM {ident(table)}"
    params: tuple[Any, ...] = ()
    if limit:
        sql += " LIMIT %s"
        params = (limit,)
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return [clean_row(row) for row in cur.fetchall()]


def ensure_table(conn: pymysql.connections.Connection, table: str, columns: list[str]) -> None:
    with conn.cursor() as cur:
        cur.execute(build_create_table_sql(table, columns))
        for col in columns:
            cur.execute(f"ALTER TABLE {ident(table)} MODIFY COLUMN {ident(col)} {column_type(col)}")
        for index_name, index_columns in MIRROR_INDEXES.get(table, []):
            try:
                cur.execute(f"CREATE INDEX {ident(index_name)} ON {ident(table)} ({', '.join(ident(col) for col in index_columns)})")
            except pymysql.err.OperationalError as exc:
                if exc.args and exc.args[0] == 1061:
                    continue
                raise


def replace_table(conn: pymysql.connections.Connection, table: str, columns: list[str], rows: list[dict[str, Any]]) -> None:
    ensure_table(conn, table, columns)
    with conn.cursor() as cur:
        cur.execute(f"TRUNCATE TABLE {ident(table)}")
        if rows:
            placeholders = ", ".join(["%s"] * len(columns))
            sql = f"INSERT INTO {ident(table)} ({', '.join(ident(col) for col in columns)}) VALUES ({placeholders})"
            cur.executemany(sql, [[row.get(col) for col in columns] for row in rows])


def write_database_sync_status(conn: pymysql.connections.Connection, report: dict[str, Any]) -> None:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {ident(SYNC_STATUS_TABLE)} (
                id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                started_at DATETIME NULL,
                finished_at DATETIME NULL,
                status VARCHAR(20) NULL,
                error TEXT NULL,
                tables_json JSON NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
        cur.execute(
            f"""
            INSERT INTO {ident(SYNC_STATUS_TABLE)}
                (started_at, finished_at, status, error, tables_json)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                report.get("started_at"),
                report.get("finished_at"),
                report.get("status"),
                report.get("error"),
                json.dumps(report.get("tables") or [], default=str),
            ),
        )


def run_sync(dry_run: bool, limit: int | None) -> dict[str, Any]:
    load_dotenv(PROJECT_ROOT / ".env", override=True)
    started = datetime.now()
    report = {"started_at": started.isoformat(timespec="seconds"), "dry_run": dry_run, "tables": []}

    with connect("COOP") as source:
        target = None if dry_run else connect("VPS")
        try:
            for table, columns in MIRROR_TABLES.items():
                rows = read_table(source, table, columns, limit)
                if target:
                    replace_table(target, table, columns, rows)
                    target.commit()
                report["tables"].append({"table": table, "rows": len(rows)})
            report["finished_at"] = datetime.now().isoformat(timespec="seconds")
            report["status"] = "ok"
            if target:
                write_database_sync_status(target, report)
                target.commit()
        finally:
            if target:
                target.close()

    return report


def write_sync_log(report: dict[str, Any], log_dir: str | Path) -> Path:
    target_dir = Path(log_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = target_dir / f"sync-{stamp}.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync selected cooperative data into the dashboard VPS mirror.")
    parser.add_argument("--dry-run", action="store_true", help="Read source data and print row counts without writing to VPS.")
    parser.add_argument("--limit", type=int, default=None, help="Optional row limit per table for tests.")
    parser.add_argument("--log-dir", default="logs/sync", help="Directory for JSON run logs.")
    args = parser.parse_args()
    try:
        report = run_sync(args.dry_run, args.limit)
        report["status"] = "ok"
    except Exception as exc:
        report = {
            "started_at": datetime.now().isoformat(timespec="seconds"),
            "finished_at": datetime.now().isoformat(timespec="seconds"),
            "dry_run": args.dry_run,
            "status": "error",
            "error": str(exc),
        }
        write_sync_log(report, args.log_dir)
        print(json.dumps(report, indent=2))
        raise SystemExit(1) from exc
    write_sync_log(report, args.log_dir)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
