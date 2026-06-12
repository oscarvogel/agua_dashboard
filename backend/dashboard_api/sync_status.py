from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from django.conf import settings


def default_sync_log_dir() -> Path:
    return Path(getattr(settings, "PROJECT_ROOT", Path.cwd())) / "logs" / "sync"


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def latest_sync_status(
    *,
    log_dir: Path | None = None,
    now: datetime | None = None,
    max_age_minutes: int | None = None,
    remote_status_loader: Callable[[], dict[str, Any] | None] | None = None,
) -> dict[str, Any]:
    target_dir = log_dir or default_sync_log_dir()
    if max_age_minutes is not None:
        max_age = max_age_minutes
    elif settings.configured:
        max_age = int(getattr(settings, "DASHBOARD_SYNC_MAX_AGE_MINUTES", 90))
    else:
        max_age = 90
    current_time = (now or datetime.now(UTC)).astimezone(UTC)
    fallback_remote = remote_status_loader is not None or log_dir is None
    if not target_dir.exists():
        remote = remote_sync_status(remote_status_loader) if fallback_remote else None
        return remote or {"state": "warning", "message": "Sin logs de sincronizacion", "tables": []}

    logs = sorted(target_dir.glob("sync-*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not logs:
        remote = remote_sync_status(remote_status_loader) if fallback_remote else None
        return remote or {"state": "warning", "message": "Sin logs de sincronizacion", "tables": []}

    try:
        payload = json.loads(logs[0].read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"state": "error", "message": f"Log invalido: {logs[0].name}", "tables": []}

    status = str(payload.get("status") or "").lower()
    finished_at = payload.get("finished_at")
    base = {
        "state": "ok",
        "message": "Sincronizacion correcta",
        "started_at": payload.get("started_at"),
        "finished_at": finished_at,
        "tables": payload.get("tables") or [],
        "log_file": logs[0].name,
    }
    if status and status != "ok":
        base["state"] = "error"
        base["message"] = payload.get("error") or "La ultima sincronizacion fallo"
        return base

    finished = parse_timestamp(finished_at)
    if finished and (current_time - finished).total_seconds() > max_age * 60:
        base["state"] = "warning"
        base["message"] = "La ultima sincronizacion esta vieja"
    return base


def remote_sync_status(loader: Callable[[], dict[str, Any] | None] | None = None) -> dict[str, Any] | None:
    if loader:
        return loader()
    try:
        from .repository import latest_database_sync_status

        return latest_database_sync_status()
    except Exception:
        return None
