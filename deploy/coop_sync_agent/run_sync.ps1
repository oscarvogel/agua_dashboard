param(
    [string]$ProjectRoot = "",
    [switch]$DryRun,
    [int]$Limit = 0
)

$ErrorActionPreference = "Stop"

if ($ProjectRoot -eq "") {
    $ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
}

$python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$syncExe = Join-Path $ProjectRoot "sync.exe"
$syncScript = Join-Path $ProjectRoot "sync_mysql.py"
$logDir = Join-Path $ProjectRoot "logs\sync"

if (-not (Test-Path (Join-Path $ProjectRoot ".env"))) {
    throw "Falta .env. Copiar .env.example como .env y completar credenciales."
}

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$syncArgs = @("--log-dir", $logDir)
if ($DryRun) {
    $syncArgs += "--dry-run"
}
if ($Limit -gt 0) {
    $syncArgs += @("--limit", $Limit)
}

if (Test-Path $syncExe) {
    & $syncExe @syncArgs
    exit $LASTEXITCODE
}

if (-not (Test-Path $python)) {
    throw "No se encontro sync.exe ni el entorno virtual. Ejecutar install.ps1 primero."
}

$pythonArgs = @($syncScript) + $syncArgs
& $python @pythonArgs
exit $LASTEXITCODE
