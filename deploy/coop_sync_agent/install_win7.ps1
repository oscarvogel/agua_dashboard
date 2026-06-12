param(
    [string]$SourceDir = "",
    [string]$InstallDir = "C:\agua-dashboard-sync-agent",
    [string]$PythonCommand = "",
    [string]$TaskName = "AguaDashboardSync",
    [string]$StartTime = "08:00",
    [int]$IntervalMinutes = 60,
    [switch]$VerifyTask
)

$ErrorActionPreference = "Stop"

if ($SourceDir -eq "") {
    $SourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}

function Write-Line {
    param([string]$Text)
    Write-Host $Text
}

function Resolve-PythonCommand {
    param([string]$Preferred)

    if ($Preferred -ne "") {
        return $Preferred
    }

    foreach ($candidate in @("py", "python")) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($command -ne $null) {
            return $candidate
        }
    }

    throw "No se encontro Python. Instalar Python 3 compatible con Windows 7 y volver a ejecutar."
}

function Copy-AgentFiles {
    param(
        [string]$From,
        [string]$To
    )

    if (-not (Test-Path $To)) {
        New-Item -ItemType Directory -Force -Path $To | Out-Null
    }

    $fromPath = (Resolve-Path $From).Path.TrimEnd("\")
    $toPath = (Resolve-Path $To).Path.TrimEnd("\")

    if ($fromPath.ToLowerInvariant() -eq $toPath.ToLowerInvariant()) {
        return
    }

    Get-ChildItem -LiteralPath $From -Force | Where-Object {
        $_.Name -ne ".venv" -and $_.Name -ne "logs"
    } | ForEach-Object {
        $destination = Join-Path $To $_.Name
        if ($_.PSIsContainer) {
            Copy-Item -LiteralPath $_.FullName -Destination $destination -Recurse -Force
        } else {
            Copy-Item -LiteralPath $_.FullName -Destination $destination -Force
        }
    }
}

function Show-TaskStatus {
    param([string]$Name)

    & schtasks.exe /Query /TN $Name /FO LIST /V
    return $LASTEXITCODE
}

if ($VerifyTask) {
    exit (Show-TaskStatus -Name $TaskName)
}

Write-Line "Instalando agente en $InstallDir"
Copy-AgentFiles -From $SourceDir -To $InstallDir

$venvPython = Join-Path $InstallDir ".venv\Scripts\python.exe"
$syncExe = Join-Path $InstallDir "sync.exe"
$requirements = Join-Path $InstallDir "requirements.txt"
$wheelsDir = Join-Path $InstallDir "wheels"
$envFile = Join-Path $InstallDir ".env"
$envExample = Join-Path $InstallDir ".env.example"
$logDir = Join-Path $InstallDir "logs\sync"
$hiddenRunner = Join-Path $InstallDir "run_sync_hidden.vbs"

if (-not (Test-Path $envFile)) {
    if (Test-Path $envExample) {
        Copy-Item -LiteralPath $envExample -Destination $envFile -Force
        Write-Line "Se creo .env desde .env.example. Completar credenciales antes de sincronizar."
    } else {
        Write-Line "Advertencia: falta .env.example. Crear .env manualmente."
    }
}

if (Test-Path $syncExe) {
    Write-Line "Se encontro sync.exe; no se instala Python ni dependencias."
} else {
    if (-not (Test-Path $venvPython)) {
        $pythonLauncher = Resolve-PythonCommand -Preferred $PythonCommand
        & $pythonLauncher -m venv (Join-Path $InstallDir ".venv")
    }

    if (Test-Path $wheelsDir) {
        & $venvPython -m pip install --no-index --find-links $wheelsDir -r $requirements
    } else {
        & $venvPython -m pip install --upgrade pip
        & $venvPython -m pip install -r $requirements
    }
}

if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
}

if (-not (Test-Path $hiddenRunner)) {
    throw "Falta run_sync_hidden.vbs en $InstallDir"
}

$taskCommand = "wscript.exe `"$hiddenRunner`""

& schtasks.exe /Create /TN $TaskName /TR $taskCommand /SC MINUTE /MO $IntervalMinutes /ST $StartTime /F | Out-Host
if ($LASTEXITCODE -ne 0) {
    throw "No se pudo crear la tarea programada con schtasks.exe."
}

Write-Line ""
Write-Line "Instalacion Windows 7 finalizada."
Write-Line "Carpeta: $InstallDir"
Write-Line "Tarea: $TaskName cada $IntervalMinutes minutos desde $StartTime"
Write-Line "Ejecucion silenciosa: wscript.exe run_sync_hidden.vbs"
Write-Line ""
Write-Line "Proximos pasos:"
Write-Line "1. Abrir y completar $envFile"
Write-Line "2. Ejecutar VERIFICAR.bat desde $InstallDir"
Write-Line "3. Ejecutar SINCRONIZAR.bat y confirmar status ok en logs\sync"
