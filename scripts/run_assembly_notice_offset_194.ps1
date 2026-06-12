$ErrorActionPreference = "Stop"

$ProjectRoot = "O:\agua_dashboard"
$LogDir = Join-Path $ProjectRoot "logs\assembly_notice"
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$RunLog = Join-Path $LogDir "scheduled-send-offset-194-$Stamp.log"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Start-Transcript -Path $RunLog -Append | Out-Null

try {
    Set-Location $ProjectRoot
    & ".\.venv\Scripts\python.exe" "scripts\send_assembly_notice.py" "--send" "--offset" "194"
    $ExitCode = $LASTEXITCODE
    if ($ExitCode -ne 0) {
        throw "send_assembly_notice.py termino con codigo $ExitCode"
    }
}
finally {
    Stop-Transcript | Out-Null
}
