param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$FrontendBase = "http://localhost:5173",
    [string]$ApiBase = "http://127.0.0.1:8000/api",
    [string]$OutputDir = (Join-Path $env:TEMP "agua-dashboard-browser-smoke"),
    [int]$WaitMs = 30000,
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

function Assert-HttpOk {
    param([string]$Url)

    $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 10
    if ($response.StatusCode -lt 200 -or $response.StatusCode -ge 300) {
        throw "$Url devolvio HTTP $($response.StatusCode)"
    }
}

$frontendDir = Join-Path $ProjectRoot "frontend"
if (-not (Test-Path (Join-Path $frontendDir "package.json"))) {
    throw "No se encontro frontend en $frontendDir"
}

Assert-HttpOk -Url "$FrontendBase/"
$health = Invoke-RestMethod -Uri "$ApiBase/health/" -Method Get
if (-not $health.ok) {
    throw "Health API no devolvio ok=true"
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

$login = Invoke-RestMethod `
    -Uri "$ApiBase/auth/login/" `
    -Method Post `
    -ContentType "application/json" `
    -Body (@{ username = $Username; password = $Password } | ConvertTo-Json)

if (-not $login.token) {
    throw "Login no devolvio token."
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$frontendOrigin = ([System.Uri]$FrontendBase).GetLeftPart([System.UriPartial]::Authority)
$storage = @{
    cookies = @()
    origins = @(
        @{
            origin = $frontendOrigin
            localStorage = @(
                @{ name = "agua_dashboard_token"; value = $login.token },
                @{ name = "agua_dashboard_user"; value = $login.user.username },
                @{ name = "agua_dashboard_is_admin"; value = $(if ($login.user.is_admin) { "1" } else { "0" }) }
            )
        }
    )
} | ConvertTo-Json -Depth 8

$storagePath = Join-Path $OutputDir "storage.json"
[System.IO.File]::WriteAllText($storagePath, $storage, [System.Text.UTF8Encoding]::new($false))

$screenshots = @(
    @{ name = "dashboard-mobile.png"; url = "$FrontendBase/#dashboard" },
    @{ name = "collections-day-mobile.png"; url = "$FrontendBase/#collections-day" }
)

Push-Location $frontendDir
try {
    foreach ($shot in $screenshots) {
        $target = Join-Path $OutputDir $shot.name
        npx playwright screenshot `
            --channel=msedge `
            "--viewport-size=390,844" `
            --load-storage $storagePath `
            --wait-for-timeout $WaitMs `
            --full-page `
            $shot.url `
            $target

        if ($LASTEXITCODE -ne 0) {
            throw "Fallo captura Playwright para $($shot.url)"
        }

        $file = Get-Item -LiteralPath $target
        if ($file.Length -lt 20000) {
            throw "Captura demasiado chica, posible pantalla en blanco: $target ($($file.Length) bytes)"
        }
    }
}
finally {
    Pop-Location
}

[pscustomobject]@{
    ok = $true
    frontend_base = $FrontendBase
    api_base = $ApiBase
    output_dir = $OutputDir
    screenshots = $screenshots | ForEach-Object {
        $path = Join-Path $OutputDir $_.name
        $file = Get-Item -LiteralPath $path
        [pscustomobject]@{
            path = $file.FullName
            bytes = $file.Length
        }
    }
} | ConvertTo-Json -Depth 5
