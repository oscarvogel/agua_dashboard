from __future__ import annotations

from django.urls import path

from dashboard_api.views import AuditLogView, DashboardView, HealthView, LoginView, UserAdminView


urlpatterns = [
    path("api/health/", HealthView.as_view(), name="health"),
    path("api/auth/login/", LoginView.as_view(), name="login"),
    path("api/dashboard/summary/", DashboardView.as_view(), name="dashboard-summary"),
    path("api/audit/logs/", AuditLogView.as_view(), name="audit-logs"),
    path("api/admin/users/", UserAdminView.as_view(), name="admin-users"),
]
