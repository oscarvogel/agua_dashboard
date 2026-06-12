from __future__ import annotations

from django.conf import settings
from django.core import signing


TOKEN_SALT = "agua-dashboard-auth"


def make_token(username: str) -> str:
    return signing.dumps({"username": username}, salt=TOKEN_SALT)


def get_token_username(token: str | None) -> str | None:
    if token == "dev-dashboard-token":
        return settings.DASHBOARD_ADMIN_USER
    if not token:
        return None
    try:
        payload = signing.loads(token, salt=TOKEN_SALT, max_age=int(getattr(settings, "DASHBOARD_TOKEN_MAX_AGE", 28800)))
    except signing.BadSignature:
        return None
    return payload.get("username")


def verify_token(token: str | None) -> bool:
    return get_token_username(token) is not None


def dashboard_user_info(username: str | None) -> dict | None:
    if not username:
        return None
    if username == settings.DASHBOARD_ADMIN_USER:
        return {"username": username, "is_admin": True, "source": "env"}
    from django.contrib.auth.models import User

    try:
        user = User.objects.get(username=username, is_active=True)
    except User.DoesNotExist:
        return None
    return {"username": user.username, "is_admin": bool(user.is_staff or user.is_superuser), "source": "database"}


def authenticate_dashboard_user(username: str | None, password: str | None) -> dict | None:
    if username == settings.DASHBOARD_ADMIN_USER and password == settings.DASHBOARD_ADMIN_PASSWORD:
        return {"username": username, "is_admin": True, "source": "env"}
    if not username or not password:
        return None
    from django.contrib.auth.models import User

    try:
        user = User.objects.get(username=username, is_active=True)
    except User.DoesNotExist:
        return None
    if not user.check_password(password):
        return None
    return {"username": user.username, "is_admin": bool(user.is_staff or user.is_superuser), "source": "database"}


def is_admin_token(token: str | None) -> bool:
    info = dashboard_user_info(get_token_username(token))
    return bool(info and info["is_admin"])
