from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import pymysql


REQUIRED_ENV = [
    "COOP_MYSQL_HOST",
    "COOP_MYSQL_PORT",
    "COOP_MYSQL_DATABASE",
    "COOP_MYSQL_USER",
    "COOP_MYSQL_PASSWORD",
]


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")

    missing = [key for key in REQUIRED_ENV if not values.get(key)]
    if missing:
        raise SystemExit(f"Missing required keys in {path}: {', '.join(missing)}")
    return values


def connect(env: dict[str, str]) -> pymysql.connections.Connection:
    ssl_mode = env.get("COOP_MYSQL_SSL_MODE", "preferred").lower()
    ssl: dict[str, Any] | None
    if ssl_mode in {"disabled", "disable", "false", "0", "none"}:
        ssl = None
    else:
        # The cooperative server may use an internal/self-signed certificate.
        # For metadata inspection we encrypt the session but do not validate CA.
        ssl = {"check_hostname": False}

    return pymysql.connect(
        host=env["COOP_MYSQL_HOST"],
        port=int(env.get("COOP_MYSQL_PORT", "3306")),
        user=env["COOP_MYSQL_USER"],
        password=env["COOP_MYSQL_PASSWORD"],
        database=env["COOP_MYSQL_DATABASE"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        ssl=ssl,
        connect_timeout=10,
        read_timeout=60,
        write_timeout=60,
    )


def fetch_all(conn: pymysql.connections.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return list(cur.fetchall())


def fetch_one(conn: pymysql.connections.Connection, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def ident(name: str) -> str:
    return "`" + name.replace("`", "``") + "`"


def safe_filename(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value).strip("_")


def table_inventory(conn: pymysql.connections.Connection, schema: str) -> list[dict[str, Any]]:
    return fetch_all(
        conn,
        """
        SELECT
            TABLE_NAME AS table_name,
            TABLE_TYPE AS table_type,
            ENGINE AS engine,
            COALESCE(TABLE_ROWS, 0) AS approx_rows,
            ROUND((COALESCE(DATA_LENGTH, 0) + COALESCE(INDEX_LENGTH, 0)) / 1024 / 1024, 2) AS mb,
            CREATE_TIME AS create_time,
            UPDATE_TIME AS update_time
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = %s
        ORDER BY TABLE_TYPE, TABLE_NAME
        """,
        (schema,),
    )


def column_inventory(conn: pymysql.connections.Connection, schema: str) -> list[dict[str, Any]]:
    return fetch_all(
        conn,
        """
        SELECT
            TABLE_NAME AS table_name,
            ORDINAL_POSITION AS ordinal_position,
            COLUMN_NAME AS column_name,
            COLUMN_TYPE AS column_type,
            IS_NULLABLE AS is_nullable,
            COLUMN_KEY AS column_key,
            COLUMN_DEFAULT AS column_default,
            EXTRA AS extra,
            COLUMN_COMMENT AS column_comment
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s
        ORDER BY TABLE_NAME, ORDINAL_POSITION
        """,
        (schema,),
    )


def index_inventory(conn: pymysql.connections.Connection, schema: str) -> list[dict[str, Any]]:
    return fetch_all(
        conn,
        """
        SELECT
            TABLE_NAME AS table_name,
            INDEX_NAME AS index_name,
            NON_UNIQUE AS non_unique,
            SEQ_IN_INDEX AS seq_in_index,
            COLUMN_NAME AS column_name,
            CARDINALITY AS cardinality,
            INDEX_TYPE AS index_type
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = %s
        ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX
        """,
        (schema,),
    )


def fk_inventory(conn: pymysql.connections.Connection, schema: str) -> list[dict[str, Any]]:
    return fetch_all(
        conn,
        """
        SELECT
            TABLE_NAME AS table_name,
            COLUMN_NAME AS column_name,
            REFERENCED_TABLE_NAME AS referenced_table_name,
            REFERENCED_COLUMN_NAME AS referenced_column_name,
            CONSTRAINT_NAME AS constraint_name
        FROM information_schema.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = %s
          AND REFERENCED_TABLE_SCHEMA IS NOT NULL
        ORDER BY TABLE_NAME, COLUMN_NAME
        """,
        (schema,),
    )


def date_ranges(conn: pymysql.connections.Connection, schema: str, columns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    date_types = {"date", "datetime", "timestamp"}
    candidates = [
        (col["table_name"], col["column_name"])
        for col in columns
        if str(col["column_type"]).split("(", 1)[0].lower() in date_types
    ]

    ranges: list[dict[str, Any]] = []
    for table, column in candidates:
        try:
            row = fetch_one(
                conn,
                f"SELECT COUNT(*) AS filled, MIN({ident(column)}) AS min_value, MAX({ident(column)}) AS max_value "
                f"FROM {ident(schema)}.{ident(table)} WHERE {ident(column)} IS NOT NULL"
            )
            if row:
                ranges.append({"table_name": table, "column_name": column, **row})
        except Exception as exc:
            ranges.append({"table_name": table, "column_name": column, "error": str(exc)})
    return ranges


def likely_dashboard_topics(tables: list[dict[str, Any]], columns_by_table: dict[str, list[dict[str, Any]]]) -> list[str]:
    names = {t["table_name"].lower() for t in tables}
    suggestions: list[str] = []

    if {"cabfact", "detfact"} & names:
        suggestions.append("Facturacion: evolucion mensual, importes por tipo de comprobante, servicios/familias facturadas.")
    if "ctacte" in names:
        suggestions.append("Cuenta corriente: saldos, deuda vencida, antiguedad de deuda, clientes con mayor saldo.")
    if "consumo" in names:
        suggestions.append("Consumos: evolucion por periodo, conexiones sin lectura, consumos cero, saltos anormales.")
    if "conexiones" in names:
        suggestions.append("Conexiones: altas/bajas, estado del padron, distribucion por zona/tipo de servicio.")
    if "clientes" in names:
        suggestions.append("Clientes/socios: padron activo, segmentacion por zona, titularidad y datos incompletos.")
    if "movcaja" in names:
        suggestions.append("Caja/cobranzas: ingresos por fecha, medios/conceptos, conciliacion operativa.")
    if "pendfact" in names:
        suggestions.append("Pendientes de facturacion: volumen pendiente, antiguedad y riesgo operativo.")
    if "articulos" in names or "artprov" in names:
        suggestions.append("Articulos/proveedores: inventario o items facturables si aplican a la operatoria.")

    geo_tables = []
    for table, cols in columns_by_table.items():
        col_names = {c["column_name"].lower() for c in cols}
        if {"ubicacion", "latitud", "longitud", "lat", "lon"} & col_names:
            geo_tables.append(table)
    if geo_tables:
        suggestions.append("Mapa ejecutivo: capas geograficas disponibles en " + ", ".join(sorted(geo_tables)) + ".")

    return suggestions


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(
    path: Path,
    schema: str,
    server_info: dict[str, Any],
    tables: list[dict[str, Any]],
    columns_by_table: dict[str, list[dict[str, Any]]],
    indexes: list[dict[str, Any]],
    fks: list[dict[str, Any]],
    ranges: list[dict[str, Any]],
    suggestions: list[str],
) -> None:
    index_count = defaultdict(int)
    for idx in indexes:
        index_count[idx["table_name"]] += 1

    lines: list[str] = []
    lines.append("# Inspeccion base cooperativa")
    lines.append("")
    lines.append(f"- Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- Base: `{schema}`")
    lines.append(f"- Servidor: `{server_info.get('version', '')}`")
    lines.append(f"- Tablas/vistas: `{len(tables)}`")
    lines.append("")
    lines.append("## Inventario")
    lines.append("")
    lines.append("| Tabla | Tipo | Filas aprox. | MB | Columnas | Indices |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for table in tables:
        name = table["table_name"]
        lines.append(
            f"| `{name}` | {table['table_type']} | {table['approx_rows']} | {table['mb']} | "
            f"{len(columns_by_table.get(name, []))} | {index_count[name]} |"
        )

    lines.append("")
    lines.append("## Tablas principales por volumen")
    lines.append("")
    for table in sorted(tables, key=lambda row: int(row.get("approx_rows") or 0), reverse=True)[:12]:
        cols = ", ".join(f"`{c['column_name']}`" for c in columns_by_table.get(table["table_name"], [])[:16])
        lines.append(f"- `{table['table_name']}`: aprox. {table['approx_rows']} filas. Columnas: {cols}")

    if fks:
        lines.append("")
        lines.append("## Relaciones declaradas")
        lines.append("")
        for fk in fks:
            lines.append(
                f"- `{fk['table_name']}.{fk['column_name']}` -> "
                f"`{fk['referenced_table_name']}.{fk['referenced_column_name']}`"
            )
    else:
        lines.append("")
        lines.append("## Relaciones declaradas")
        lines.append("")
        lines.append("- No se detectaron foreign keys declaradas en `information_schema`.")

    lines.append("")
    lines.append("## Rangos de fechas")
    lines.append("")
    for row in ranges:
        if row.get("error"):
            lines.append(f"- `{row['table_name']}.{row['column_name']}`: error al inspeccionar.")
        else:
            lines.append(
                f"- `{row['table_name']}.{row['column_name']}`: {row.get('filled', 0)} registros, "
                f"desde `{row.get('min_value')}` hasta `{row.get('max_value')}`"
            )

    lines.append("")
    lines.append("## Ideas iniciales para dashboard ejecutivo")
    lines.append("")
    for suggestion in suggestions:
        lines.append(f"- {suggestion}")

    lines.append("")
    lines.append("## Archivos generados")
    lines.append("")
    lines.append("- `tables.csv`: inventario de tablas y tamanos.")
    lines.append("- `columns.csv`: columnas y tipos.")
    lines.append("- `indexes.csv`: indices detectados.")
    lines.append("- `foreign_keys.csv`: relaciones declaradas, si existen.")
    lines.append("- `date_ranges.csv`: rangos de campos fecha.")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect cooperative MariaDB/MySQL metadata without dumping personal data.")
    parser.add_argument("--env", default=".env.coop", help="Path to .env.coop")
    parser.add_argument("--out", default="reports/db_inspection", help="Output directory")
    args = parser.parse_args()

    env_path = Path(args.env).resolve()
    out_dir = Path(args.out).resolve()
    env = load_env(env_path)
    schema = env["COOP_MYSQL_DATABASE"]

    with connect(env) as conn:
        server_info = fetch_one(conn, "SELECT VERSION() AS version, DATABASE() AS database_name") or {}
        tables = table_inventory(conn, schema)
        columns = column_inventory(conn, schema)
        indexes = index_inventory(conn, schema)
        fks = fk_inventory(conn, schema)
        ranges = date_ranges(conn, schema, columns)

    columns_by_table: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for col in columns:
        columns_by_table[col["table_name"]].append(col)

    suggestions = likely_dashboard_topics(tables, columns_by_table)

    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "tables.csv", tables)
    write_csv(out_dir / "columns.csv", columns)
    write_csv(out_dir / "indexes.csv", indexes)
    write_csv(out_dir / "foreign_keys.csv", fks)
    write_csv(out_dir / "date_ranges.csv", ranges)
    (out_dir / "summary.json").write_text(
        json.dumps(
            {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "schema": schema,
                "server_info": server_info,
                "table_count": len(tables),
                "column_count": len(columns),
                "suggestions": suggestions,
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    write_markdown(
        out_dir / "dashboard_oportunidades.md",
        schema,
        server_info,
        tables,
        columns_by_table,
        indexes,
        fks,
        ranges,
        suggestions,
    )

    print(f"OK: inspected {len(tables)} tables/views from `{schema}`.")
    print(f"Report: {out_dir / 'dashboard_oportunidades.md'}")


if __name__ == "__main__":
    main()
