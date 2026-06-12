param(
    [string]$ProjectRoot = $PSScriptRoot,
    [string]$PythonCommand = "",
    [switch]$RegisterTask,
    [switch]$VerifyTask,
    [string]$TaskName = "AguaDashboardSync",
    [string]$StartTime = "08:00",
    [int]$IntervalMinutes = 60
)

$ErrorActionPreference = "Stop"

$venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$requirements = Join-Path $ProjectRoot "requirements.txt"
$runScript = Join-Path $ProjectRoot "run_sync.ps1"
$logDir = Join-Path $ProjectRoot "logs\sync"

function Resolve-PythonCommand {
    param([string]$Preferred)

    if ($Preferred) {
        return $Preferred
    }

    foreach ($candidate in @("py", "python")) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($command) {
            return $candidate
        }
    }

    throw "No se encontro Python. Instalar Python 3 y volver a ejecutar install.ps1."
}

function Get-TaskStatus {
    param([string]$Name)

    $task = Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue
    if (-not $task) {
        return [pscustomobject]@{
            TaskName = $Name
            Installed = $false
        }
    }

    $info = Get-ScheduledTaskInfo -TaskName $Name
    return [pscustomobject]@{
        TaskName = $task.TaskName
        Installed = $true
        State = $task.State
        LastRunTime = $info.LastRunTime
        LastTaskResult = $info.LastTaskResult
        NextRunTime = $info.NextRunTime
        Actions = ($task.Actions | ForEach-Object { "$($_.Execute) $($_.Arguments)" }) -join " | "
    }
}

if ($VerifyTask) {
    Get-TaskStatus -Name $TaskName | ConvertTo-Json -Depth 4
    exit 0
}

if (-not (Test-Path (Join-Path $ProjectRoot ".env"))) {
    Write-Warning "Falta .env. Copiar .env.example como .env y completar credenciales antes de sincronizar."
}

if (-not (Test-Path $venvPython)) {
    $pythonLauncher = Resolve-PythonCommand -Preferred $PythonCommand
    & $pythonLauncher -m venv (Join-Path $ProjectRoot ".venv")
}

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r $requirements

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

if ($RegisterTask) {
    $action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$runScript`"" `
        -WorkingDirectory $ProjectRoot
    $trigger = New-ScheduledTaskTrigger `
        -Once `
        -At $StartTime `
        -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) `
        -RepetitionDuration (New-TimeSpan -Hours 12)
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel LeastPrivilege

    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Principal $principal `
        -Description "Sincroniza datos seleccionados de la cooperativa al VPS para el dashboard ejecutivo." `
        -Force | Out-Null
}

[pscustomobject]@{
    project_root = $ProjectRoot
    venv_python = $venvPython
    env_file = Test-Path (Join-Path $ProjectRoot ".env")
    log_dir = $logDir
    task = Get-TaskStatus -Name $TaskName
} | ConvertTo-Json -Depth 5
