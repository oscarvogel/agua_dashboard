param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$OutputDir = (Join-Path $ProjectRoot "dist"),
    [string]$PackageName = "agua-dashboard-vps-release",
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

$frontendDir = Join-Path $ProjectRoot "frontend"
$frontendDist = Join-Path $frontendDir "dist"
$packageDir = Join-Path $OutputDir $PackageName
$zipPath = Join-Path $OutputDir "$PackageName.zip"

if (-not (Test-Path (Join-Path $ProjectRoot "backend\manage.py"))) {
    throw "No se encontro backend Django en $ProjectRoot"
}

if (-not (Test-Path $frontendDir)) {
    throw "No se encontro frontend Vue en $frontendDir"
}

if (-not $SkipBuild) {
    Push-Location $frontendDir
    try {
        npm run build
    }
    finally {
        Pop-Location
    }
}

if (-not (Test-Path (Join-Path $frontendDist "index.html"))) {
    throw "No se encontro frontend compilado en $frontendDist. Ejecutar npm run build."
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

if (Test-Path $packageDir) {
    Remove-Item -LiteralPath $packageDir -Recurse -Force
}
if (Test-Path $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}

New-Item -ItemType Directory -Force -Path $packageDir | Out-Null

Copy-Item -LiteralPath (Join-Path $ProjectRoot "backend") -Destination (Join-Path $packageDir "backend") -Recurse
Copy-Item -LiteralPath (Join-Path $ProjectRoot "requirements.txt") -Destination (Join-Path $packageDir "requirements.txt")
Copy-Item -LiteralPath (Join-Path $ProjectRoot "requirements-vps.txt") -Destination (Join-Path $packageDir "requirements-vps.txt")
Copy-Item -LiteralPath (Join-Path $ProjectRoot ".env.example") -Destination (Join-Path $packageDir ".env.example")
Copy-Item -LiteralPath (Join-Path $ProjectRoot "README.md") -Destination (Join-Path $packageDir "README.md")
Copy-Item -LiteralPath (Join-Path $ProjectRoot "docs") -Destination (Join-Path $packageDir "docs") -Recurse
New-Item -ItemType Directory -Force -Path (Join-Path $packageDir "deploy") | Out-Null
Copy-Item -LiteralPath (Join-Path $ProjectRoot "deploy\mysql_vps_grants_template.sql") -Destination (Join-Path $packageDir "deploy\mysql_vps_grants_template.sql")
Copy-Item -LiteralPath (Join-Path $ProjectRoot "deploy\vps") -Destination (Join-Path $packageDir "deploy\vps") -Recurse
New-Item -ItemType Directory -Force -Path (Join-Path $packageDir "scripts") | Out-Null
Copy-Item -LiteralPath (Join-Path $ProjectRoot "scripts\smoke_dashboard.ps1") -Destination (Join-Path $packageDir "scripts\smoke_dashboard.ps1")
Copy-Item -LiteralPath (Join-Path $ProjectRoot "scripts\browser_smoke.ps1") -Destination (Join-Path $packageDir "scripts\browser_smoke.ps1")
Copy-Item -LiteralPath (Join-Path $ProjectRoot "scripts\verify_checksums.ps1") -Destination (Join-Path $packageDir "scripts\verify_checksums.ps1")
Copy-Item -LiteralPath $frontendDist -Destination (Join-Path $packageDir "frontend_dist") -Recurse

$runtimeDirs = @(
    (Join-Path $packageDir "backend\db.sqlite3"),
    (Join-Path $packageDir "backend\dashboard_api\__pycache__"),
    (Join-Path $packageDir "backend\dashboard_project\__pycache__"),
    (Join-Path $packageDir "backend\tests\__pycache__")
)

foreach ($path in $runtimeDirs) {
    if (Test-Path $path) {
        Remove-Item -LiteralPath $path -Recurse -Force
    }
}

$manifest = [ordered]@{
    package = $PackageName
    generated_at = (Get-Date).ToString("s")
    frontend_dist = "frontend_dist"
    backend_entrypoint = "backend\manage.py"
    docs = @(
        "docs\despliegue_vps_dashboard.md",
        "docs\estado_implementacion_dashboard.md",
        "docs\validacion_gerencial_indicadores.md"
    )
    smoke_test = "scripts\smoke_dashboard.ps1"
    browser_smoke_test = "scripts\browser_smoke.ps1"
    checksum_verifier = "scripts\verify_checksums.ps1"
    mysql_grants_template = "deploy\mysql_vps_grants_template.sql"
    vps_templates = @(
        "deploy\vps\agua-dashboard.service.example",
        "deploy\vps\nginx_agua_dashboard.conf.example",
        "deploy\vps\install_release_linux.sh"
    )
    files = Get-ChildItem -LiteralPath $packageDir -File -Recurse | ForEach-Object {
        $_.FullName.Substring($packageDir.Length + 1)
    }
}

$manifest | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $packageDir "manifest.json") -Encoding UTF8

$packageFiles = Get-ChildItem -LiteralPath $packageDir -Force
Compress-Archive -Path $packageFiles.FullName -DestinationPath $zipPath -Force

[pscustomobject]@{
    package_dir = $packageDir
    zip = $zipPath
    files = (Get-ChildItem -LiteralPath $packageDir -File -Recurse).Count
} | ConvertTo-Json
