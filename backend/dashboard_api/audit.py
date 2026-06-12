from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from django.conf import settings


SENSITIVE_KEYS = {"authorization", "password", "secret", "token"}
AUDIT_FILE_NAME = "dashboard-audit.jsonl"


def default_audit_dir() -> Path:
    return Path(getattr(settings, "PROJECT_ROOT", Path.cwd())) / "logs" / "audit"


def sanitize_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for key, value in (metadata or {}).items():
        if any(part in key.lower() for part in SENSITIVE_KEYS):
            clean[key] = "[redacted]"
        else:
            clean[key] = value
    return clean


def record_event(
    event: str,
    *,
    username: str | None = None,
    level: str = "info",
    message: str = "",
    metadata: dict[str, Any] | None = None,
    audit_dir: Path | None = None,
) -> dict[str, Any]:
    target_dir = audit_dir or default_audit_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "level": level,
        "event": event,
        "username": username or "anonymous",
        "message": message,
        "metadata": sanitize_metadata(metadata),
    }
    with (target_dir / AUDIT_FILE_NAME).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return payload


def get_recent_events(*, limit: int = 100, audit_dir: Path | None = None) -> list[dict[str, Any]]:
    target_file = (audit_dir or default_audit_dir()) / AUDIT_FILE_NAME
    if not target_file.exists():
        return []
    lines = target_file.read_text(encoding="utf-8").splitlines()
    events: list[dict[str, Any]] = []
    for line in reversed(lines[-limit:]):
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events
