from datetime import date
import json

import sys

from sync_mysql import MIRROR_INDEXES, MIRROR_TABLES, build_create_table_sql, clean_row, resolve_runtime_root, write_sync_log


def test_mirror_tables_match_first_executive_dataset():
    assert list(MIRROR_TABLES) == [
        "clientes",
        "conexiones",
        "consumo",
        "cabfact",
        "detfact",
        "ctacte",
        "movcaja",
        "pendfact",
        "conceptos",
        "tablas",
    ]


def test_clean_row_normalizes_invalid_dates_and_decimal_like_values():
    row = clean_row({"fechaingreso": "0000-00-00", "fechaven": date(2026, 4, 30), "neto": "10.50", "activo": b"\x01", "estado": ""})

    assert row["fechaingreso"] is None
    assert row["fechaven"] == "2026-04-30"
    assert row["neto"] == "10.50"
    assert row["activo"] == 1
    assert row["estado"] is None


def test_clean_row_normalizes_invalid_integer_values():
    row = clean_row({"estado": "A", "facturado": "1", "idcliente": 42})

    assert row["estado"] is None
    assert row["facturado"] == 1
    assert row["idcliente"] == 42


def test_write_sync_log_persists_json_report(tmp_path):
    path = write_sync_log({"dry_run": True, "tables": [{"table": "clientes", "rows": 2}]}, tmp_path)

    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["dry_run"] is True
    assert data["tables"][0]["table"] == "clientes"


def test_create_table_sql_has_typed_columns_and_dashboard_indexes():
    sql = build_create_table_sql("cabfact", MIRROR_TABLES["cabfact"])

    assert "`IdCabFact` BIGINT" in sql
    assert "`estado` BIGINT" in sql
    assert "`fechaem` DATE" in sql
    assert "`neto` DECIMAL(14,2)" in sql
    assert "ENGINE=InnoDB" in sql
    assert MIRROR_INDEXES["cabfact"][0] == ("idx_cabfact_fechaem", ["fechaem"])
    assert MIRROR_INDEXES["conceptos"][0] == ("idx_conceptos_tipoiva", ["tipoiva"])


def test_resolve_runtime_root_uses_executable_directory_when_frozen(monkeypatch, tmp_path):
    exe_dir = tmp_path / "installed-agent"
    exe_dir.mkdir()
    exe_path = exe_dir / "sync.exe"
    exe_path.write_text("", encoding="utf-8")

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(exe_path))

    assert resolve_runtime_root() == exe_dir
