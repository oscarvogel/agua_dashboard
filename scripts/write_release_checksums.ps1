param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$OutputFile = (Join-Path $ProjectRoot "dist\checksums.sha256")
)

$ErrorActionPreference = "Stop"

$artifacts = @(
    (Join-Path $ProjectRoot "dist\agua-dashboard-sync-agent.zip"),
    (Join-Path $ProjectRoot "dist\agua-dashboard-vps-release.zip")
)

$lines = @()
foreach ($artifact in $artifacts) {
    if (-not (Test-Path $artifact)) {
        throw "No existe artefacto para checksum: $artifact"
    }

    $hash = Get-FileHash -LiteralPath $artifact -Algorithm SHA256
    $relative = $artifact.Substring($ProjectRoot.Length + 1).Replace("\", "/")
    $lines += "$($hash.Hash.ToLowerInvariant())  $relative"
}

Set-Content -LiteralPath $OutputFile -Value $lines -Encoding ASCII

[pscustomobject]@{
    output = $OutputFile
    artifacts = $lines.Count
} | ConvertTo-Json
