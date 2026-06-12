param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [switch]$SkipSmoke,
    [switch]$SkipBuild,
    [switch]$BrowserSmoke
)

$ErrorActionPreference = "Stop"

function Assert-Path {
    param(
        [string]$Path,
        [string]$Label
    )

    if (-not (Test-Path $Path)) {
        throw "Falta $Label`: $Path"
    }
}

function Run-Step {
    param(
        [string]$Name,
        [scriptblock]$Action
    )

    Write-Host "== $Name =="
    & $Action
    if ($LASTEXITCODE -ne 0) {
        throw "Fallo paso: $Name"
    }
}

$python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$frontendDir = Join-Path $ProjectRoot "frontend"
$coopPackage = Join-Path $ProjectRoot "dist\agua-dashboard-sync-agent.zip"
$vpsPackage = Join-Path $ProjectRoot "dist\agua-dashboard-vps-release.zip"
$checksums = Join-Path $ProjectRoot "dist\checksums.sha256"
$coopManifest = Join-Path $ProjectRoot "dist\agua-dashboard-sync-agent\manifest.json"
$vpsManifest = Join-Path $ProjectRoot "dist\agua-dashboard-vps-release\manifest.json"
$vpsRequirements = Join-Path $ProjectRoot "requirements-vps.txt"

Assert-Path -Path $python -Label "Python del entorno virtual"
Assert-Path -Path (Join-Path $ProjectRoot "backend\manage.py") -Label "backend Django"
Assert-Path -Path (Join-Path $frontendDir "package.json") -Label "frontend package.json"
Assert-Path -Path $vpsRequirements -Label "requirements VPS"

Run-Step -Name "pytest" -Action {
    Push-Location $ProjectRoot
    try {
        & $python -m pytest
    }
    finally {
        Pop-Location
    }
}

Run-Step -Name "django check" -Action {
    Push-Location $ProjectRoot
    try {
        & $python backend\manage.py check
    }
    finally {
        Pop-Location
    }
}

if (-not $SkipBuild) {
    Run-Step -Name "frontend build" -Action {
        Push-Location $frontendDir
        try {
            npm run build
        }
        finally {
            Pop-Location
        }
    }
}

Run-Step -Name "build coop sync package" -Action {
    powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "scripts\build_coop_sync_package.ps1") -ProjectRoot $ProjectRoot
}

Run-Step -Name "build VPS release" -Action {
    $args = @("-ExecutionPolicy", "Bypass", "-File", (Join-Path $ProjectRoot "scripts\build_vps_release.ps1"), "-ProjectRoot", $ProjectRoot)
    if ($SkipBuild) {
        $args += "-SkipBuild"
    }
    powershell @args
}

Run-Step -Name "write checksums" -Action {
    powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "scripts\write_release_checksums.ps1") -ProjectRoot $ProjectRoot
}

Run-Step -Name "verify checksums" -Action {
    powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "scripts\verify_checksums.ps1") -ProjectRoot $ProjectRoot
}

Assert-Path -Path $coopPackage -Label "ZIP agente cooperativa"
Assert-Path -Path $vpsPackage -Label "ZIP release VPS"
Assert-Path -Path $checksums -Label "checksums release"
Assert-Path -Path $coopManifest -Label "manifest agente cooperativa"
Assert-Path -Path $vpsManifest -Label "manifest release VPS"

$coopManifestText = Get-Content -LiteralPath $coopManifest -Raw
$vpsManifestText = Get-Content -LiteralPath $vpsManifest -Raw

foreach ($required in @("sync_mysql.py", "install.ps1", "run_sync.ps1", "verify.ps1")) {
    if ($coopManifestText -notmatch [regex]::Escape($required)) {
        throw "Manifest cooperativa no incluye $required"
    }
}

foreach ($required in @("backend\\manage.py", "frontend_dist\\index.html", "scripts\\smoke_dashboard.ps1", "requirements-vps.txt")) {
    if ($vpsManifestText -notmatch [regex]::Escape($required)) {
        throw "Manifest VPS no incluye $required"
    }
}

if ((Get-Content -LiteralPath $vpsRequirements -Raw) -notmatch "gunicorn") {
    throw "requirements-vps.txt no incluye gunicorn"
}

if (-not $SkipSmoke) {
    Run-Step -Name "API smoke" -Action {
        powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "scripts\smoke_dashboard.ps1") -ProjectRoot $ProjectRoot
    }
}

if ($BrowserSmoke) {
    Run-Step -Name "browser smoke" -Action {
        powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "scripts\browser_smoke.ps1") -ProjectRoot $ProjectRoot
    }
}

[pscustomobject]@{
    ok = $true
    project_root = $ProjectRoot
    coop_package = $coopPackage
    vps_package = $vpsPackage
    checksums = $checksums
    smoke = -not $SkipSmoke
    browser_smoke = [bool]$BrowserSmoke
    frontend_build = -not $SkipBuild
} | ConvertTo-Json
