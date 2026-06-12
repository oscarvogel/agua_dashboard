from __future__ import annotations

from datetime import date

from django.conf import settings
from django.db import connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .audit import get_recent_events, record_event
from .auth import authenticate_dashboard_user, get_token_username, is_admin_token, make_token, verify_token
from .metrics import build_dashboard_payload
from .repository import check_mysql_connection, fetch_rows, has_vps_config
from .sync_status import latest_sync_status


def bearer_token(request) -> str:
    return request.headers.get("Authorization", "").removeprefix("Bearer ").strip()


class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    @staticmethod
    def check_django_database() -> dict:
        try:
            connection.ensure_connection()
            return {"state": "ok", "message": "Base Django disponible"}
        except Exception as exc:
            return {"state": "error", "message": f"Base Django no disponible ({exc.__class__.__name__})"}

    @staticmethod
    def check_auth_schema() -> dict:
        try:
            tables = set(connection.introspection.table_names())
        except Exception as exc:
            return {"state": "error", "message": f"No se pudo inspeccionar el esquema Django ({exc.__class__.__name__})"}
        if "auth_user" not in tables:
            return {"state": "error", "message": "Falta tabla auth_user; ejecutar migraciones Django"}
        return {"state": "ok", "message": "Esquema de usuarios disponible"}

    @staticmethod
    def overall_status(checks: dict) -> str:
        states = [str(check.get("state", "ok")) for check in checks.values()]
        if "error" in states:
            return "error"
        if "warning" in states:
            return "warning"
        return "ok"

    def get(self, request):
        database_configured = has_vps_config()
        checks = {
            "application": {"state": "ok", "message": "Aplicacion disponible"},
            "django_database": self.check_django_database(),
            "django_auth_schema": self.check_auth_schema(),
            "mysql": check_mysql_connection()
            if database_configured
            else {"state": "skipped", "message": "Base MySQL VPS no configurada", "configured": False},
            "sync": latest_sync_status(),
        }
        current_status = self.overall_status(checks)
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE if current_status == "error" else status.HTTP_200_OK
        return Response(
            {
                "ok": current_status != "error",
                "status": current_status,
                "service": "agua-dashboard",
                "database_configured": database_configured,
                "checks": checks,
            },
            status=http_status,
        )


class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user_info = authenticate_dashboard_user(username, password)
        if user_info:
            record_event("auth.login.success", username=username, message="Inicio de sesion correcto")
            return Response({"token": make_token(user_info["username"]), "user": user_info})
        record_event(
            "auth.login.failed",
            username=username,
            level="warning",
            message="Credenciales invalidas",
            metadata={"remote_addr": request.META.get("REMOTE_ADDR")},
        )
        return Response({"detail": "Credenciales invalidas"}, status=status.HTTP_401_UNAUTHORIZED)


class DashboardView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        token = bearer_token(request)
        if not verify_token(token):
            record_event("dashboard.access.denied", level="warning", message="Consulta sin token valido")
            return Response({"detail": "No autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        period = request.query_params.get("period", "actual")
        periods = [value.strip() for value in request.query_params.get("periods", "").split(",") if value.strip()]
        zone = request.query_params.get("zone", "")
        status_filter = request.query_params.get("status", "todos")
        try:
            mode, rows = fetch_rows()
            payload = build_dashboard_payload(
                rows,
                today=date.today(),
                period=period,
                periods=periods,
                zone=zone,
                status_filter=status_filter,
            )
            payload["source"]["mode"] = mode
            payload["source"]["database_configured"] = has_vps_config()
            payload["source"]["sync"] = latest_sync_status()
            return Response(payload)
        except Exception as exc:
            record_event(
                "dashboard.error",
                username=get_token_username(token),
                level="error",
                message=str(exc),
                metadata={"period": period, "periods": periods, "zone": zone, "status": status_filter},
            )
            return Response({"detail": "No se pudo cargar el dashboard"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AuditLogView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, audit_dir=None):
        token = bearer_token(request)
        if not is_admin_token(token):
            record_event("audit.access.denied", level="warning", message="Acceso no autorizado al registro de auditoria")
            return Response({"detail": "No autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            limit = min(int(request.query_params.get("limit", 100)), 500)
        except ValueError:
            limit = 100
        return Response({"events": get_recent_events(limit=limit, audit_dir=audit_dir)})


class UserAdminView(APIView):
    authentication_classes = []
    permission_classes = []

    @staticmethod
    def serialize_user(user) -> dict:
        return {
            "id": user.id,
            "username": user.username,
            "is_admin": bool(user.is_staff or user.is_superuser),
            "is_active": bool(user.is_active),
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "date_joined": user.date_joined.isoformat() if user.date_joined else None,
        }

    def get(self, request):
        from django.contrib.auth.models import User

        token = bearer_token(request)
        if not is_admin_token(token):
            record_event("admin.users.access.denied", level="warning", message="Acceso no autorizado a usuarios")
            return Response({"detail": "No autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        users = User.objects.order_by("username")
        return Response({"users": [self.serialize_user(user) for user in users]})

    def post(self, request):
        from django.contrib.auth.models import User

        token = bearer_token(request)
        admin_username = get_token_username(token)
        if not is_admin_token(token):
            record_event("admin.users.create.denied", level="warning", message="Intento no autorizado de crear usuario")
            return Response({"detail": "No autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

        username = str(request.data.get("username") or "").strip()
        password = str(request.data.get("password") or "")
        is_admin = bool(request.data.get("is_admin"))

        if not username:
            return Response({"detail": "El usuario es obligatorio"}, status=status.HTTP_400_BAD_REQUEST)
        if len(password) < 8:
            return Response({"detail": "La clave debe tener al menos 8 caracteres"}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=username).exists() or username == settings.DASHBOARD_ADMIN_USER:
            return Response({"detail": "Ese usuario ya existe"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, password=password, is_active=True)
        user.is_staff = is_admin
        user.is_superuser = is_admin
        user.save(update_fields=["is_staff", "is_superuser"])
        record_event(
            "admin.users.created",
            username=admin_username,
            message=f"Usuario creado: {username}",
            metadata={"created_username": username, "is_admin": is_admin},
        )
        return Response({"user": self.serialize_user(user)}, status=status.HTTP_201_CREATED)
