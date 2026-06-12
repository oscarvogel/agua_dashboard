const API_BASE = import.meta.env.VITE_API_BASE || "/api";

export async function login(username, password) {
  const response = await fetch(`${API_BASE}/auth/login/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) {
    throw new Error("Credenciales invalidas");
  }
  return response.json();
}

export async function fetchDashboard({ period, periods = [], zone, status, token }) {
  const params = new URLSearchParams({ period: period || "actual", zone: zone || "", status: status || "todos" });
  if (periods.length) {
    params.set("periods", periods.join(","));
  }
  const response = await fetch(`${API_BASE}/dashboard/summary/?${params}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) {
    const message = response.status === 401 ? "No autenticado" : "No se pudo cargar el dashboard";
    throw new Error(message);
  }
  return response.json();
}

export async function fetchAuditLogs({ token, limit = 100 }) {
  const params = new URLSearchParams({ limit: String(limit) });
  const response = await fetch(`${API_BASE}/audit/logs/?${params}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) {
    const message = response.status === 401 ? "Auditoria disponible solo para admin" : "No se pudo cargar la auditoria";
    throw new Error(message);
  }
  return response.json();
}

export async function fetchAdminUsers({ token }) {
  const response = await fetch(`${API_BASE}/admin/users/`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) {
    const message = response.status === 401 ? "Usuarios disponible solo para admin" : "No se pudo cargar usuarios";
    throw new Error(message);
  }
  return response.json();
}

export async function createAdminUser({ token, username, password, isAdmin }) {
  const response = await fetch(`${API_BASE}/admin/users/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ username, password, is_admin: isAdmin }),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || "No se pudo crear el usuario");
  }
  return response.json();
}
