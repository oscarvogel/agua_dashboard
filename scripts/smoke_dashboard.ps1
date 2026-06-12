param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$ApiBase = "http://127.0.0.1:8000/api",
    [string]$Username = "",
    [string]$Password = ""
)

$ErrorActionPreference = "Stop"

function Read-DotEnv {
    param([string]$Path)

    $values = @{}
    if (-not (Test-Path $Path)) {
        return $values
    }

    Get-Content -LiteralPath $Path | ForEach-Object {
        if ($_ -match '^\s*([^#=]+)=(.*)$') {
            $values[$matches[1].Trim()] = $matches[2].Trim()
        }
    }
    return $values
}

$envMap = Read-DotEnv -Path (Join-Path $ProjectRoot ".env")
if (-not $Username) {
    $Username = $envMap["DASHBOARD_ADMIN_USER"]
}
if (-not $Password) {
    $Password = $envMap["DASHBOARD_ADMIN_PASSWORD"]
}
if (-not $Username -or -not $Password) {
    throw "Faltan credenciales. Pasar -Username/-Password o completar DASHBOARD_ADMIN_USER/DASHBOARD_ADMIN_PASSWORD en .env."
}

$health = Invoke-RestMethod -Uri "$ApiBase/health/" -Method Get
if (-not $health.ok) {
    throw "Health check no devolvio ok=true."
}

$login = Invoke-RestMethod `
    -Uri "$ApiBase/auth/login/" `
    -Method Post `
    -ContentType "application/json" `
    -Body (@{ username = $Username; password = $Password } | ConvertTo-Json)

if (-not $login.token) {
    throw "Login no devolvio token."
}

$dashboard = Invoke-RestMethod `
    -Uri "$ApiBase/dashboard/summary/" `
    -Method Get `
    -Headers @{ Authorization = "Bearer $($login.token)" }

$requiredSummary = @(
    "clientes_activos",
    "conexiones_activas",
    "facturacion_mes",
    "cobranzas_mes",
    "deuda_total",
    "deuda_vencida",
    "consumo_ultimo_periodo",
    "pendiente_facturacion"
)

foreach ($key in $requiredSummary) {
    if ($null -eq $dashboard.summary.$key) {
        throw "Falta summary.$key en respuesta dashboard."
    }
}

$requiredBreakdowns = @(
    "deuda_antiguedad",
    "deuda_zona",
    "facturacion_concepto",
    "pendientes_periodo",
    "pendientes_concepto",
    "consumo_zona"
)

foreach ($key in $requiredBreakdowns) {
    if ($null -eq $dashboard.breakdowns.$key) {
        throw "Falta breakdowns.$key en respuesta dashboard."
    }
}

$audit = Invoke-RestMethod `
    -Uri "$ApiBase/audit/logs/?limit=5" `
    -Method Get `
    -Headers @{ Authorization = "Bearer $($login.token)" }

[pscustomobject]@{
    ok = $true
    api_base = $ApiBase
    database_configured = [bool]$health.database_configured
    source_mode = $dashboard.source.mode
    sync_state = $dashboard.source.sync.state
    generated_at = $dashboard.source.generated_at
    monthly_points = @($dashboard.series.monthly).Count
    top_debtors = @($dashboard.top_deudores).Count
    audit_events = @($audit.events).Count
} | ConvertTo-Json
