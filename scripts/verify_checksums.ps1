param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$ChecksumFile = (Join-Path $ProjectRoot "dist\checksums.sha256")
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $ChecksumFile)) {
    throw "No se encontro archivo de checksums: $ChecksumFile"
}

$baseDir = Split-Path -Parent $ChecksumFile
$results = @()

Get-Content -LiteralPath $ChecksumFile | Where-Object { $_.Trim() } | ForEach-Object {
    $parts = $_ -split "\s+", 2
    if ($parts.Count -ne 2) {
        throw "Linea invalida en checksums: $_"
    }

    $expected = $parts[0].Trim().ToLowerInvariant()
    $relative = $parts[1].Trim().Replace("/", "\")
    $path = Join-Path $ProjectRoot $relative

    if (-not (Test-Path $path)) {
        throw "No existe artefacto listado en checksum: $path"
    }

    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    $ok = $actual -eq $expected
    $results += [pscustomobject]@{
        file = $relative
        ok = $ok
        expected = $expected
        actual = $actual
    }
}

$failed = @($results | Where-Object { -not $_.ok })
if ($failed.Count -gt 0) {
    $failed | ConvertTo-Json -Depth 4
    throw "Fallaron checksums: $($failed.Count)"
}

[pscustomobject]@{
    ok = $true
    checksum_file = $ChecksumFile
    verified = $results.Count
} | ConvertTo-Json
