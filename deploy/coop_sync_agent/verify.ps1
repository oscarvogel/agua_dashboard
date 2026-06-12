param(
    [string]$ProjectRoot = ""
)

$ErrorActionPreference = "Stop"

if ($ProjectRoot -eq "") {
    $ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
}

$python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$syncExe = Join-Path $ProjectRoot "sync.exe"
$envFile = Join-Path $ProjectRoot ".env"
$syncScript = Join-Path $ProjectRoot "sync_mysql.py"

$result = @{
    project_root = $ProjectRoot
    sync_exe = Test-Path $syncExe
    python = Test-Path $python
    env_file = Test-Path $envFile
    sync_script = Test-Path $syncScript
    dependencies = $false
    dry_run = $false
}

if ($result.sync_exe) {
    $result.dependencies = $true
} elseif ($result.python) {
    & $python -c "import pymysql, dotenv; print('dependencies ok')" | Out-Null
    $result.dependencies = ($LASTEXITCODE -eq 0)
}

if (($result.sync_exe -or ($result.python -and $result.sync_script)) -and $result.env_file -and $result.dependencies) {
    & (Join-Path $ProjectRoot "run_sync.ps1") -DryRun -Limit 1 | Out-Null
    $result.dry_run = ($LASTEXITCODE -eq 0)
}

Write-Host "project_root=$($result.project_root)"
Write-Host "sync_exe=$($result.sync_exe)"
Write-Host "python=$($result.python)"
Write-Host "env_file=$($result.env_file)"
Write-Host "sync_script=$($result.sync_script)"
Write-Host "dependencies=$($result.dependencies)"
Write-Host "dry_run=$($result.dry_run)"

if (-not (($result.sync_exe -or ($result.python -and $result.sync_script)) -and $result.env_file -and $result.dependencies -and $result.dry_run)) {
    exit 1
}
