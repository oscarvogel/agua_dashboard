import os
from unittest import TestCase
from unittest.mock import patch

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dashboard_project.settings")

import django
from django.test.utils import setup_databases, teardown_databases
from rest_framework.test import APIRequestFactory

django.setup()

from dashboard_api.views import HealthView


class HealthViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._db_config = setup_databases(verbosity=0, interactive=False, aliases={"default"})

    @classmethod
    def tearDownClass(cls):
        teardown_databases(cls._db_config, verbosity=0)
        super().tearDownClass()

    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = HealthView.as_view()

    @patch("dashboard_api.views.latest_sync_status")
    @patch("dashboard_api.views.check_mysql_connection")
    @patch("dashboard_api.views.has_vps_config")
    def test_health_reports_application_database_mysql_and_sync_checks(
        self,
        has_vps_config,
        check_mysql_connection,
        latest_sync_status,
    ):
        has_vps_config.return_value = True
        check_mysql_connection.return_value = {"state": "ok", "message": "Conexion MySQL correcta"}
        latest_sync_status.return_value = {"state": "ok", "message": "Sincronizacion correcta", "tables": []}

        response = self.view(self.factory.get("/api/health/"))

        assert response.status_code == 200
        assert response.data["ok"] is True
        assert response.data["status"] == "ok"
        assert response.data["service"] == "agua-dashboard"
        assert response.data["database_configured"] is True
        assert response.data["checks"]["application"]["state"] == "ok"
        assert response.data["checks"]["django_database"]["state"] == "ok"
        assert response.data["checks"]["mysql"]["state"] == "ok"
        assert response.data["checks"]["sync"]["state"] == "ok"
        check_mysql_connection.assert_called_once_with()
        latest_sync_status.assert_called_once_with()

    @patch("dashboard_api.views.latest_sync_status")
    @patch("dashboard_api.views.check_mysql_connection")
    @patch("dashboard_api.views.has_vps_config")
    def test_health_skips_mysql_when_vps_database_is_not_configured(
        self,
        has_vps_config,
        check_mysql_connection,
        latest_sync_status,
    ):
        has_vps_config.return_value = False
        latest_sync_status.return_value = {"state": "warning", "message": "Sin logs de sincronizacion", "tables": []}

        response = self.view(self.factory.get("/api/health/"))

        assert response.status_code == 200
        assert response.data["ok"] is True
        assert response.data["status"] == "warning"
        assert response.data["database_configured"] is False
        assert response.data["checks"]["mysql"] == {
            "state": "skipped",
            "message": "Base MySQL VPS no configurada",
            "configured": False,
        }
        assert response.data["checks"]["sync"]["state"] == "warning"
        check_mysql_connection.assert_not_called()

    @patch("dashboard_api.views.latest_sync_status")
    @patch("dashboard_api.views.check_mysql_connection")
    @patch("dashboard_api.views.has_vps_config")
    def test_health_returns_503_when_mysql_validation_fails(
        self,
        has_vps_config,
        check_mysql_connection,
        latest_sync_status,
    ):
        has_vps_config.return_value = True
        check_mysql_connection.return_value = {"state": "error", "message": "No se pudo conectar a MySQL"}
        latest_sync_status.return_value = {"state": "ok", "message": "Sincronizacion correcta", "tables": []}

        response = self.view(self.factory.get("/api/health/"))

        assert response.status_code == 503
        assert response.data["ok"] is False
        assert response.data["status"] == "error"
        assert response.data["checks"]["mysql"]["state"] == "error"
