param(
    [string]$TaskName = "AguaDashboardSync",
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$StartTime = "08:00",
    [int]$IntervalMinutes = 60,
    [switch]$Verify
)

$ErrorActionPreference = "Stop"

$python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$syncScript = Join-Path $ProjectRoot "sync\sync_mysql.py"
$logDir = Join-Path $ProjectRoot "logs\sync"

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

if ($Verify) {
    Get-TaskStatus -Name $TaskName | ConvertTo-Json -Depth 4
    exit 0
}

if (-not (Test-Path $python)) {
    throw "No se encontro Python del entorno virtual: $python"
}

if (-not (Test-Path (Join-Path $ProjectRoot ".env"))) {
    throw "Falta .env en $ProjectRoot. Cargalo antes de programar la sincronizacion."
}

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$action = New-ScheduledTaskAction -Execute $python -Argument "`"$syncScript`" --log-dir `"$logDir`"" -WorkingDirectory $ProjectRoot
$trigger = New-ScheduledTaskTrigger -Once -At $StartTime -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration (New-TimeSpan -Hours 12)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel LeastPrivilege

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Description "Sincroniza datos seleccionados de la cooperativa al VPS para el dashboard ejecutivo." -Force

Get-TaskStatus -Name $TaskName | ConvertTo-Json -Depth 4
