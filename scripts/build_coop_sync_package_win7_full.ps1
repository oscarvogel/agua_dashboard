param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$OutputDir = (Join-Path $ProjectRoot "dist"),
    [string]$PackageName = "agua-dashboard-sync-agent-win7-full",
    [string]$LegacyPythonExe = ""
)

$ErrorActionPreference = "Stop"

$downloadsDir = Join-Path $ProjectRoot "downloads"
$legacyPythonUrl = "https://www.python.org/ftp/python/3.7.9/python-3.7.9.exe"
$legacyPythonInstaller = Join-Path $downloadsDir "python-3.7.9.exe"
$legacyPythonDir = Join-Path $downloadsDir "python37-32"
$templateDir = Join-Path $ProjectRoot "deploy\coop_sync_agent"
$syncScript = Join-Path $ProjectRoot "sync\sync_mysql.py"
$packageDir = Join-Path $OutputDir $PackageName
$zipPath = Join-Path $OutputDir "$PackageName.zip"
$requirements = Join-Path $templateDir "requirements.txt"
$fullInstaller = Join-Path $templateDir "INSTALAR_WIN7_COMPLETO.bat"
$buildDir = Join-Path $ProjectRoot ".build\sync-agent-win7"
$venvPython = Join-Path $buildDir ".venv\Scripts\python.exe"
$syncExe = Join-Path $buildDir "dist\sync.exe"

if (-not (Test-Path $fullInstaller)) {
    throw "No se encontro instalador completo: INSTALAR_WIN7_COMPLETO.bat"
}

New-Item -ItemType Directory -Force -Path $downloadsDir | Out-Null
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

if ($LegacyPythonExe -eq "") {
    $LegacyPythonExe = Join-Path $legacyPythonDir "python.exe"
}

if (-not (Test-Path $LegacyPythonExe)) {
    if (-not (Test-Path $legacyPythonInstaller)) {
        Write-Host "Descargando $legacyPythonUrl"
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($legacyPythonUrl, $legacyPythonInstaller)
    }
    Write-Host "Instalando Python 3.7.9 x86 local para build: $legacyPythonDir"
    & $legacyPythonInstaller /quiet InstallAllUsers=0 TargetDir="$legacyPythonDir" Include_pip=1 Include_test=0 PrependPath=0
}

if (-not (Test-Path $LegacyPythonExe)) {
    throw "No se encontro Python legacy para build: $LegacyPythonExe"
}

if (Test-Path $buildDir) {
    Remove-Item -LiteralPath $buildDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $buildDir | Out-Null

& $LegacyPythonExe -m venv (Join-Path $buildDir ".venv")
if ($LASTEXITCODE -ne 0) {
    throw "Fallo creacion de venv para build Win7."
}

$pipTrustedHosts = @("--trusted-host", "pypi.org", "--trusted-host", "files.pythonhosted.org")
& $venvPython -m pip install @pipTrustedHosts --upgrade "pip<24"
& $venvPython -m pip install @pipTrustedHosts "pyinstaller==4.10" -r $requirements
if ($LASTEXITCODE -ne 0) {
    throw "Fallo instalacion de dependencias de build Win7."
}

& $venvPython -m PyInstaller --onefile --clean --name sync --distpath (Join-Path $buildDir "dist") --workpath (Join-Path $buildDir "work") --specpath $buildDir $syncScript
if ($LASTEXITCODE -ne 0) {
    throw "Fallo compilacion de sync.exe con PyInstaller."
}

if (-not (Test-Path $syncExe)) {
    throw "No se genero sync.exe: $syncExe"
}

if (Test-Path $packageDir) {
    Remove-Item -LiteralPath $packageDir -Recurse -Force
}
if (Test-Path $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}

Copy-Item -LiteralPath $templateDir -Destination $packageDir -Recurse
Copy-Item -LiteralPath $syncScript -Destination (Join-Path $packageDir "sync_mysql.py") -Force
Copy-Item -LiteralPath $syncExe -Destination (Join-Path $packageDir "sync.exe") -Force

foreach ($runtimePath in @(".env", ".venv", "logs", "dump", "wheels")) {
    $target = Join-Path $packageDir $runtimePath
    if (Test-Path $target) {
        Remove-Item -LiteralPath $target -Recurse -Force
    }
}

$manifest = [ordered]@{
    package = $PackageName
    generated_at = (Get-Date).ToString("s")
    runtime = "sync.exe"
    build_python = $LegacyPythonExe
    build_python_url = $legacyPythonUrl
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
