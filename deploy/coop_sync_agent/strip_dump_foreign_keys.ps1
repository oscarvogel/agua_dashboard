param(
    [string]$DumpFile
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $DumpFile)) {
    throw "No existe dump SQL: $DumpFile"
}

$text = [System.IO.File]::ReadAllText($DumpFile)

$text = [regex]::Replace(
    $text,
    "(?m)^\s*CONSTRAINT\s+`?[^` ]+`?\s+FOREIGN KEY\s+\([^\r\n]*\)\s+REFERENCES\s+[^\r\n]*,?\r?\n",
    ""
)

$text = [regex]::Replace(
    $text,
    ",(\r?\n\)\s+ENGINE=)",
    '$1'
)

$text = "SET FOREIGN_KEY_CHECKS=0;`r`n" + $text + "`r`nSET FOREIGN_KEY_CHECKS=1;`r`n"

[System.IO.File]::WriteAllText($DumpFile, $text, [System.Text.Encoding]::UTF8)
