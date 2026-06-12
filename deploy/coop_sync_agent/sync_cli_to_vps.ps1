param(
    [string]$EnvFile = ".env",
    [string]$WorkDir = "",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

if ($WorkDir -eq "") {
    $WorkDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}

Set-Location $WorkDir

$ExportDir = Join-Path $WorkDir "cli_export"
$LogDir = Join-Path $WorkDir "logs\cli_sync"
$TempDir = Join-Path $WorkDir "tmp"
if (-not (Test-Path $ExportDir)) { New-Item -ItemType Directory -Force -Path $ExportDir | Out-Null }
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Force -Path $LogDir | Out-Null }
if (-not (Test-Path $TempDir)) { New-Item -ItemType Directory -Force -Path $TempDir | Out-Null }

$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogFile = Join-Path $LogDir ("sync-cli-" + $Stamp + ".log")
$StatusFile = Join-Path $LogDir ("sync-cli-" + $Stamp + ".json")
$ExitCode = 0
$MysqlCharset = "utf8"

function LogLine {
    param([string]$Text)
    $line = (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + " " + $Text
    Write-Host $line
    Add-Content -LiteralPath $LogFile -Value $line -Encoding ASCII
}

function Load-EnvFile {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        throw "Falta .env. Ejecutar CONFIGURAR_ENV.bat y completar credenciales."
    }
    Get-Content -LiteralPath $Path | ForEach-Object {
        $line = $_.Trim()
        if ($line -eq "" -or $line.StartsWith("#")) { return }
        $idx = $line.IndexOf("=")
        if ($idx -lt 1) { return }
        $name = $line.Substring(0, $idx).Trim()
        $value = $line.Substring($idx + 1).Trim()
        Set-Item -Path ("env:" + $name) -Value $value
    }
}

function Require-Env {
    param([string]$Name)
    $value = [Environment]::GetEnvironmentVariable($Name)
    if ($value -eq $null -or $value -eq "") {
        throw "Falta completar $Name en .env"
    }
    return $value
}

function Resolve-MysqlExe {
    $binDir = [Environment]::GetEnvironmentVariable("MYSQL_BIN_DIR")
    if ($binDir -ne $null -and $binDir -ne "") {
        $candidate = Join-Path $binDir "mysql.exe"
        if (Test-Path $candidate) { return $candidate }
        throw "No se encontro mysql.exe en MYSQL_BIN_DIR=$binDir"
    }
    $cmd = Get-Command "mysql.exe" -ErrorAction SilentlyContinue
    if ($cmd -ne $null) { return $cmd.Path }
    throw "No se encontro mysql.exe. Completar MYSQL_BIN_DIR en .env o agregar MySQL al PATH."
}

function Write-ClientFile {
    param(
        [string]$Path,
        [string]$Prefix
    )
    $hostName = Require-Env ($Prefix + "_MYSQL_HOST")
    $port = [Environment]::GetEnvironmentVariable($Prefix + "_MYSQL_PORT")
    if ($port -eq $null -or $port -eq "") { $port = "3306" }
    $user = Require-Env ($Prefix + "_MYSQL_USER")
    $password = Require-Env ($Prefix + "_MYSQL_PASSWORD")

    Set-Content -LiteralPath $Path -Encoding ASCII -Value "[client]"
    Add-Content -LiteralPath $Path -Encoding ASCII -Value ("host=" + $hostName)
    Add-Content -LiteralPath $Path -Encoding ASCII -Value ("port=" + $port)
    Add-Content -LiteralPath $Path -Encoding ASCII -Value ("user=" + $user)
    Add-Content -LiteralPath $Path -Encoding ASCII -Value ("password=" + $password)
    $sslMode = [Environment]::GetEnvironmentVariable($Prefix + "_MYSQL_SSL_MODE")
    if ($sslMode -ne $null) {
        $sslMode = $sslMode.Trim().ToLower()
    }
    if ($sslMode -eq "disabled") {
        Add-Content -LiteralPath $Path -Encoding ASCII -Value "skip-ssl"
    } elseif ($sslMode -eq "verify") {
        Add-Content -LiteralPath $Path -Encoding ASCII -Value "ssl=1"
        Add-Content -LiteralPath $Path -Encoding ASCII -Value "ssl-verify-server-cert=1"
    } elseif ($sslMode -ne $null -and $sslMode -ne "") {
        Add-Content -LiteralPath $Path -Encoding ASCII -Value "ssl=1"
        Add-Content -LiteralPath $Path -Encoding ASCII -Value "ssl-verify-server-cert=0"
    }
}

function Ident {
    param([string]$Value)
    return ('`' + $Value.Replace('`', '``') + '`')
}

function SqlString {
    param([string]$Value)
    return ("'" + $Value.Replace('\', '\\').Replace("'", "''") + "'")
}

function JsonString {
    param([string]$Value)
    if ($Value -eq $null) { return "null" }
    return ('"' + $Value.Replace('\', '\\').Replace('"', '\"') + '"')
}

function SqlValue {
    param(
        [string]$Value,
        [string]$Column
    )
    $text = ""
    if ($Value -ne $null) {
        $text = $Value.Trim()
    }
    if ($text -eq "__AGUA_NULL__") { return "NULL" }
    if ($DateKeys.ContainsKey($Column) -and ($text -eq "" -or $text -notmatch "^\d{4}-\d{2}-\d{2}$")) {
        return "NULL"
    }
    if ($IntKeys.ContainsKey($Column) -and ($text -eq "" -or $text -notmatch "^-?\d+$")) {
        return "NULL"
    }
    if ($DecimalKeys.ContainsKey($Column) -and ($text -eq "" -or $text -notmatch "^-?\d+([\.,]\d+)?$")) {
        return "NULL"
    }
    return (SqlString $text)
}

function ColumnType {
    param([string]$Column)
    if ($DateKeys.ContainsKey($Column)) { return "DATE NULL" }
    if ($DecimalKeys.ContainsKey($Column)) { return "DECIMAL(14,2) NULL" }
    if ($IntKeys.ContainsKey($Column)) { return "BIGINT NULL" }
    return "VARCHAR(255) NULL"
}

function ExportExpression {
    param([string]$Column)
    $id = Ident $Column
    if ($DateKeys.ContainsKey($Column)) {
        return ("IF($id IS NULL OR CAST($id AS CHAR) IN ('','0000-00-00','0000-00-00 00:00:00') OR YEAR($id) > 2035, '__AGUA_NULL__', DATE_FORMAT($id, '%Y-%m-%d'))")
    }
    if ($IntKeys.ContainsKey($Column)) {
        return ("IF($id IS NULL OR CAST($id AS CHAR) = '', '__AGUA_NULL__', CAST(($id + 0) AS CHAR))")
    }
    if ($DecimalKeys.ContainsKey($Column)) {
        return ("IF($id IS NULL OR CAST($id AS CHAR) = '', '__AGUA_NULL__', CAST($id AS CHAR))")
    }
    return ("IFNULL(REPLACE(REPLACE(REPLACE(CAST($id AS CHAR), CHAR(9), ' '), CHAR(13), ' '), CHAR(10), ' '), '__AGUA_NULL__')")
}

function Invoke-Mysql {
    param(
        [string]$DefaultsFile,
        [string]$Database,
        [string]$Sql,
        [string]$OutputFile
    )
    if ($OutputFile -eq "") {
        & $MysqlExe "--defaults-extra-file=$DefaultsFile" "--default-character-set=$MysqlCharset" $Database "-e" $Sql 2>> $LogFile
    } else {
        & $MysqlExe "--defaults-extra-file=$DefaultsFile" "--default-character-set=$MysqlCharset" "--batch" "--raw" "--skip-column-names" $Database "-e" $Sql 2>> $LogFile | Set-Content -LiteralPath $OutputFile -Encoding UTF8
    }
    if ($LASTEXITCODE -ne 0) {
        throw "mysql.exe termino con codigo $LASTEXITCODE"
    }
}

function Invoke-MysqlFile {
    param(
        [string]$DefaultsFile,
        [string]$Database,
        [string]$SqlFile
    )
    Get-Content -LiteralPath $SqlFile | & $MysqlExe "--defaults-extra-file=$DefaultsFile" "--default-character-set=$MysqlCharset" $Database 2>> $LogFile
    if ($LASTEXITCODE -ne 0) {
        throw "mysql.exe termino con codigo $LASTEXITCODE ejecutando $SqlFile"
    }
}

function New-Utf8Writer {
    param([string]$Path)
    $encoding = New-Object System.Text.UTF8Encoding $false
    return New-Object System.IO.StreamWriter($Path, $false, $encoding)
}

function Write-TableSqlFile {
    param(
        [string]$Path,
        [string]$Table,
        [object[]]$Columns,
        [string]$TsvPath
    )

    $writer = New-Utf8Writer $Path
    try {
        $defs = @()
        foreach ($col in $Columns) {
            $defs += ((Ident $col) + " " + (ColumnType $col))
        }
        $writer.WriteLine("SET NAMES " + $MysqlCharset + ";")
        $writer.WriteLine("SET FOREIGN_KEY_CHECKS=0;")
        $writer.WriteLine("CREATE TABLE IF NOT EXISTS " + (Ident $Table) + " (" + ($defs -join ", ") + ") ENGINE=InnoDB DEFAULT CHARSET=" + $MysqlCharset + ";")
        $writer.WriteLine("TRUNCATE TABLE " + (Ident $Table) + ";")
        foreach ($col in $Columns) {
            $writer.WriteLine("ALTER TABLE " + (Ident $Table) + " MODIFY COLUMN " + (Ident $col) + " " + (ColumnType $col) + ";")
        }

        $batch = @()
        if (Test-Path $TsvPath) {
            Get-Content -LiteralPath $TsvPath | ForEach-Object {
                $parts = $_ -split "`t"
                while ($parts.Count -lt $Columns.Count) {
                    $parts += ""
                }
                $values = @()
                for ($i = 0; $i -lt $Columns.Count; $i++) {
                    $values += (SqlValue -Value $parts[$i] -Column $Columns[$i])
                }
                $batch += ("(" + ($values -join ", ") + ")")
                if ($batch.Count -ge 100) {
                    $writer.WriteLine("INSERT INTO " + (Ident $Table) + " (" + (($Columns | ForEach-Object { Ident $_ }) -join ", ") + ") VALUES " + ($batch -join ", ") + ";")
                    $batch = @()
                }
            }
        }
        if ($batch.Count -gt 0) {
            $writer.WriteLine("INSERT INTO " + (Ident $Table) + " (" + (($Columns | ForEach-Object { Ident $_ }) -join ", ") + ") VALUES " + ($batch -join ", ") + ";")
        }
        $writer.WriteLine("SET FOREIGN_KEY_CHECKS=1;")
    }
    finally {
        $writer.Close()
    }
}

$DateKeys = @{}
"fechaem","fechaven","fechapag","Fecha","_fecha","vence","fechatoma","fechaingreso","F_Alta","F_Baja" | ForEach-Object { $DateKeys[$_] = $true }
$DecimalKeys = @{}
"neto","iva","dgr","Monto","importe","importenosocio","consumo","integracion","ultmed","descuento","Saldo" | ForEach-Object { $DecimalKeys[$_] = $true }
$IntKeys = @{}
"idcliente","idconexion","idconsumo","IdCabFact","idDetFact","idCabfact","idconcepto","idCtaCte","idFactura","idRecibo","idMovCaja","idTipoComp","idCliente","idCabFact","idpendfact","ID_Tabla","ID_TipTab","periodo","zona","activo","socio","facturado","estado","Estado" | ForEach-Object { $IntKeys[$_] = $true }

$Tables = New-Object System.Collections.Specialized.OrderedDictionary
$Tables.Add("clientes", @("idcliente","nombre","direccion","telefono","tipdoc","numdoc","sitiva","zona","activo","cuit"))
$Tables.Add("conexiones", @("idconexion","idcliente","direccion","ubicacion","zona","ultmed","activo","socio","fechaingreso","integracion"))
$Tables.Add("consumo", @("idconsumo","idconexion","fechatoma","estadomed","periodo","consumo","facturado"))
$Tables.Add("cabfact", @("IdCabFact","Tipo","Clase","numero","idcliente","idconexion","fechaem","fechaven","fechapag","neto","iva","dgr","periodo","estado"))
$Tables.Add("detfact", @("idDetFact","idCabfact","idconcepto","neto","iva","dgr","detalle"))
$Tables.Add("ctacte", @("idCtaCte","Fecha","idFactura","idRecibo","Monto","_usuario","_fecha","_hora"))
$Tables.Add("movcaja", @("idMovCaja","Fecha","idTipoComp","numcomp","importe","banco","sucursal","numche","vence","estado","idCabFact","idCliente"))
$Tables.Add("pendfact", @("idpendfact","idconexion","idcliente","idconcepto","periodo","neto","iva","dgr","detalle","facturado"))
$Tables.Add("conceptos", @("idconcepto","detalle","importe","importenosocio","activo","tipoiva","agua","generainteres"))
$Tables.Add("tablas", @("ID_Tabla","ID_TipTab","Valor","Descrip","Estado","F_Alta","F_Baja","Usuario"))

$srcCnf = Join-Path $TempDir ("agua-dashboard-cli-source-" + (Get-Random) + ".cnf")
$dstCnf = Join-Path $TempDir ("agua-dashboard-cli-target-" + (Get-Random) + ".cnf")
$rows = New-Object System.Collections.ArrayList

try {
    LogLine "Inicio sincronizacion CLI"
    Load-EnvFile (Join-Path $WorkDir $EnvFile)
    $MysqlExe = Resolve-MysqlExe
    $configuredCharset = [Environment]::GetEnvironmentVariable("MYSQL_CHARSET")
    if ($configuredCharset -ne $null -and $configuredCharset -ne "") {
        $MysqlCharset = $configuredCharset
    }
    LogLine ("Charset MySQL: " + $MysqlCharset)
    $sourceDb = Require-Env "COOP_MYSQL_DATABASE"
    $targetDb = Require-Env "VPS_MYSQL_DATABASE"
    Write-ClientFile $srcCnf "COOP"
    Write-ClientFile $dstCnf "VPS"

    foreach ($table in $Tables.Keys) {
        $columns = $Tables[$table]
        $tsv = Join-Path $ExportDir ($table + ".tsv")
        $selectParts = @()
        foreach ($col in $columns) { $selectParts += (ExportExpression $col) }
        $exportSql = "SELECT CONCAT_WS(CHAR(9), " + ($selectParts -join ", ") + ") FROM " + (Ident $table)
        LogLine ("Exportando " + $table)
        Invoke-Mysql $srcCnf $sourceDb $exportSql $tsv

        $lineCount = 0
        if (Test-Path $tsv) {
            $lineCount = @(Get-Content -LiteralPath $tsv).Count
        }

        if (-not $DryRun) {
            $tableSql = Join-Path $ExportDir ($table + ".sql")
            Write-TableSqlFile $tableSql $table $columns $tsv
            LogLine ("Cargando " + $table + " en VPS")
            Invoke-MysqlFile $dstCnf $targetDb $tableSql
        }

        [void]$rows.Add(@{ table = $table; rows = $lineCount })
        LogLine ($table + ": " + $lineCount + " filas")
    }

    if (-not $DryRun) {
        $tableJsonObjects = @()
        foreach ($row in $rows) {
            $tableJsonObjects += "JSON_OBJECT('table'," + (SqlString $row.table) + ",'rows'," + $row.rows + ")"
        }
        if ($tableJsonObjects.Count -gt 0) {
            $tablesJsonSql = "JSON_ARRAY(" + ($tableJsonObjects -join ",") + ")"
        } else {
            $tablesJsonSql = "JSON_ARRAY()"
        }
        try {
            $statusSql = "CREATE TABLE IF NOT EXISTS dashboard_sync_status (id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY, started_at DATETIME NULL, finished_at DATETIME NULL, status VARCHAR(20) NULL, error TEXT NULL, tables_json JSON NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP) ENGINE=InnoDB DEFAULT CHARSET=" + $MysqlCharset + "; INSERT INTO dashboard_sync_status (started_at, finished_at, status, error, tables_json) VALUES (NOW(), NOW(), 'ok', NULL, " + $tablesJsonSql + ");"
            Invoke-Mysql $dstCnf $targetDb $statusSql ""
        }
        catch {
            LogLine ("No se pudo registrar dashboard_sync_status: " + $_.Exception.Message)
        }
    }

    $json = "{""status"":""ok"",""mode"":""mysql-cli"",""finished_at"":""" + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + """,""log"":""" + $LogFile.Replace("\", "\\") + """}"
    Set-Content -LiteralPath $StatusFile -Encoding ASCII -Value $json
    LogLine "Sincronizacion CLI completa"
}
catch {
    $ExitCode = 1
    LogLine ("ERROR: " + $_.Exception.Message)
    $json = "{""status"":""error"",""mode"":""mysql-cli"",""finished_at"":""" + (Get-Date -Format "yyyy-MM-dd HH:mm:ss") + """,""error"":""" + $_.Exception.Message.Replace("""", "'") + """,""log"":""" + $LogFile.Replace("\", "\\") + """}"
    Set-Content -LiteralPath $StatusFile -Encoding ASCII -Value $json
}
finally {
    if ($srcCnf -ne $null -and [System.IO.File]::Exists($srcCnf)) {
        [System.IO.File]::Delete($srcCnf)
    }
    if ($dstCnf -ne $null -and [System.IO.File]::Exists($dstCnf)) {
        [System.IO.File]::Delete($dstCnf)
    }
}

exit $ExitCode
