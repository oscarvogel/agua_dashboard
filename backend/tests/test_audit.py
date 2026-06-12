import json
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dashboard_project.settings")

from django.test import override_settings
from rest_framework.test import APIRequestFactory

from dashboard_api.audit import get_recent_events, record_event
from dashboard_api.auth import make_token
from dashboard_api.views import AuditLogView


def test_record_event_persists_jsonl_with_sanitized_metadata(tmp_path):
    audit_dir = tmp_path / "audit"

    event = record_event(
        "dashboard.error",
        username="admin",
        level="error",
        message="Fallo al cargar dashboard",
        metadata={"token": "secret-token", "period": "actual"},
        audit_dir=audit_dir,
    )

    log_file = audit_dir / "dashboard-audit.jsonl"
    payload = json.loads(log_file.read_text(encoding="utf-8").strip())

    assert event["event"] == "dashboard.error"
    assert payload["metadata"]["token"] == "[redacted]"
    assert payload["metadata"]["period"] == "actual"
    assert payload["level"] == "error"


def test_get_recent_events_returns_newest_first(tmp_path):
    audit_dir = tmp_path / "audit"
    record_event("older", audit_dir=audit_dir)
    record_event("newer", audit_dir=audit_dir)

    events = get_recent_events(limit=1, audit_dir=audit_dir)

    assert [event["event"] for event in events] == ["newer"]


@override_settings(DASHBOARD_ADMIN_USER="admin", DASHBOARD_ADMIN_PASSWORD="admin")
def test_audit_log_view_is_admin_only(tmp_path):
    audit_dir = tmp_path / "audit"
    record_event("dashboard.error", audit_dir=audit_dir)
    view = AuditLogView.as_view()
    factory = APIRequestFactory()

    anonymous = view(factory.get("/api/audit/logs/"))
    admin = view(
        factory.get(
            "/api/audit/logs/",
            HTTP_AUTHORIZATION=f"Bearer {make_token('admin')}",
        ),
        audit_dir=audit_dir,
    )

    assert anonymous.status_code == 401
    assert admin.status_code == 200
    assert admin.data["events"][0]["event"] == "dashboard.error"
