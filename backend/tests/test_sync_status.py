from datetime import UTC, datetime, timedelta

from dashboard_api.sync_status import latest_sync_status


def test_latest_sync_status_reports_missing_log(tmp_path):
    status = latest_sync_status(log_dir=tmp_path, now=datetime(2026, 5, 30, 10, 0, tzinfo=UTC))

    assert status["state"] == "warning"
    assert status["message"] == "Sin logs de sincronizacion"


def test_latest_sync_status_uses_remote_status_when_local_log_is_missing(tmp_path):
    status = latest_sync_status(
        log_dir=tmp_path,
        now=datetime(2026, 5, 30, 10, 0, tzinfo=UTC),
        remote_status_loader=lambda: {
            "state": "ok",
            "message": "Sincronizacion correcta",
            "finished_at": "2026-05-30T09:40:00",
            "tables": [{"table": "clientes", "rows": 10}],
            "source": "database",
        },
    )

    assert status["state"] == "ok"
    assert status["source"] == "database"
    assert status["tables"][0]["table"] == "clientes"


def test_latest_sync_status_reports_latest_successful_run(tmp_path):
    (tmp_path / "sync-20260530-093000.json").write_text(
        '{"started_at":"2026-05-30T09:29:00","finished_at":"2026-05-30T09:30:00","status":"ok","tables":[{"table":"clientes","rows":10}]}',
        encoding="utf-8",
    )

    status = latest_sync_status(log_dir=tmp_path, now=datetime(2026, 5, 30, 10, 0, tzinfo=UTC), max_age_minutes=90)

    assert status["state"] == "ok"
    assert status["finished_at"] == "2026-05-30T09:30:00"
    assert status["tables"][0]["table"] == "clientes"


def test_latest_sync_status_warns_when_success_is_stale(tmp_path):
    stale_time = datetime(2026, 5, 30, 7, 0)
    (tmp_path / "sync-20260530-070000.json").write_text(
        f'{{"finished_at":"{stale_time.isoformat()}","status":"ok","tables":[]}}',
        encoding="utf-8",
    )

    status = latest_sync_status(log_dir=tmp_path, now=datetime(2026, 5, 30, 10, 0, tzinfo=UTC), max_age_minutes=90)

    assert status["state"] == "warning"
    assert "vieja" in status["message"]


def test_latest_sync_status_reports_error_log(tmp_path):
    (tmp_path / "sync-20260530-093000.json").write_text(
        '{"finished_at":"2026-05-30T09:30:00","status":"error","error":"timeout"}',
        encoding="utf-8",
    )

    status = latest_sync_status(log_dir=tmp_path, now=datetime(2026, 5, 30, 10, 0, tzinfo=UTC))

    assert status["state"] == "error"
    assert status["message"] == "timeout"
