import os
from unittest import TestCase

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dashboard_project.settings")

import django
from django.conf import settings
from django.test.utils import setup_databases, teardown_databases
from rest_framework.test import APIRequestFactory

django.setup()

from django.contrib.auth.models import User

from dashboard_api.auth import make_token
from dashboard_api.views import LoginView, UserAdminView


class UserAdminViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._db_config = setup_databases(verbosity=0, interactive=False, aliases={"default"})

    @classmethod
    def tearDownClass(cls):
        teardown_databases(cls._db_config, verbosity=0)
        super().tearDownClass()

    def setUp(self):
        self._old_admin_user = settings.DASHBOARD_ADMIN_USER
        self._old_admin_password = settings.DASHBOARD_ADMIN_PASSWORD
        settings.DASHBOARD_ADMIN_USER = "admin"
        settings.DASHBOARD_ADMIN_PASSWORD = "root-secret"
        User.objects.all().delete()
        self.factory = APIRequestFactory()
        self.view = UserAdminView.as_view()

    def tearDown(self):
        settings.DASHBOARD_ADMIN_USER = self._old_admin_user
        settings.DASHBOARD_ADMIN_PASSWORD = self._old_admin_password

    def test_admin_can_create_dashboard_user_with_password(self):
        response = self.view(
            self.factory.post(
                "/api/admin/users/",
                {"username": "operador", "password": "clave-segura-123", "is_admin": False},
                format="json",
                HTTP_AUTHORIZATION=f"Bearer {make_token('admin')}",
            )
        )

        user = User.objects.get(username="operador")
        assert response.status_code == 201
        assert response.data["user"]["username"] == "operador"
        assert response.data["user"]["is_admin"] is False
        assert user.check_password("clave-segura-123")
        assert user.is_active is True
        assert user.is_staff is False

    def test_non_admin_token_cannot_create_user(self):
        User.objects.create_user(username="lector", password="clave-segura-123")

        response = self.view(
            self.factory.post(
                "/api/admin/users/",
                {"username": "otro", "password": "clave-segura-123"},
                format="json",
                HTTP_AUTHORIZATION=f"Bearer {make_token('lector')}",
            )
        )

        assert response.status_code == 401
        assert not User.objects.filter(username="otro").exists()

    def test_create_user_validates_required_fields_and_duplicates(self):
        User.objects.create_user(username="existente", password="clave-segura-123")

        missing_password = self.view(
            self.factory.post(
                "/api/admin/users/",
                {"username": "nuevo", "password": ""},
                format="json",
                HTTP_AUTHORIZATION=f"Bearer {make_token('admin')}",
            )
        )
        duplicate = self.view(
            self.factory.post(
                "/api/admin/users/",
                {"username": "existente", "password": "clave-segura-123"},
                format="json",
                HTTP_AUTHORIZATION=f"Bearer {make_token('admin')}",
            )
        )

        assert missing_password.status_code == 400
        assert duplicate.status_code == 400

    def test_created_database_user_can_login_without_admin_permissions(self):
        User.objects.create_user(username="lector", password="clave-segura-123")
        view = LoginView.as_view()

        response = view(
            self.factory.post(
                "/api/auth/login/",
                {"username": "lector", "password": "clave-segura-123"},
                format="json",
            )
        )

        assert response.status_code == 200
        assert response.data["token"]
        assert response.data["user"]["username"] == "lector"
        assert response.data["user"]["is_admin"] is False
