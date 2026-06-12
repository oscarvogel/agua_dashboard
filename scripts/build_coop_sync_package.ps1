param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$OutputDir = (Join-Path $ProjectRoot "dist"),
    [string]$PackageName = "agua-dashboard-sync-agent"
)

$ErrorActionPreference = "Stop"

$templateDir = Join-Path $ProjectRoot "deploy\coop_sync_agent"
$syncScript = Join-Path $ProjectRoot "sync\sync_mysql.py"
$packageDir = Join-Path $OutputDir $PackageName
$zipPath = Join-Path $OutputDir "$PackageName.zip"

if (-not (Test-Path $templateDir)) {
    throw "No se encontro template del agente: $templateDir"
}

if (-not (Test-Path $syncScript)) {
    throw "No se encontro sincronizador: $syncScript"
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

if (Test-Path $packageDir) {
    Remove-Item -LiteralPath $packageDir -Recurse -Force
}
if (Test-Path $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}

Copy-Item -LiteralPath $templateDir -Destination $packageDir -Recurse
Copy-Item -LiteralPath $syncScript -Destination (Join-Path $packageDir "sync_mysql.py") -Force

foreach ($runtimePath in @(".env", ".venv", "logs", "dump")) {
    $target = Join-Path $packageDir $runtimePath
    if (Test-Path $target) {
        Remove-Item -LiteralPath $target -Recurse -Force
    }
}

$manifest = [ordered]@{
    package = $PackageName
    generated_at = (Get-Date).ToString("s")
    files = Get-ChildItem -LiteralPath $packageDir -File -Recurse | ForEach-Object {
        $_.FullName.Substring($packageDir.Length + 1)
    }
}

$manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $packageDir "manifest.json") -Encoding UTF8

$packageFiles = Get-ChildItem -LiteralPath $packageDir -Force
Compress-Archive -Path $packageFiles.FullName -DestinationPath $zipPath -Force

[pscustomobject]@{
    package_dir = $packageDir
    zip = $zipPath
    files = (Get-ChildItem -LiteralPath $packageDir -File -Recurse).Count
} | ConvertTo-Json
