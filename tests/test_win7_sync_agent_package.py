from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENT = ROOT / "deploy" / "coop_sync_agent"


def test_win7_agent_has_hidden_runner_and_schtasks_installer():
    assert (AGENT / "run_sync_hidden.vbs").exists()
    assert (AGENT / "install_win7.ps1").exists()
    assert (AGENT / "INSTALAR_WINDOWS7.bat").exists()

    installer = (AGENT / "install_win7.ps1").read_text(encoding="utf-8")
    assert "schtasks.exe" in installer
    assert "Get-ScheduledTask" not in installer
    assert "Register-ScheduledTask" not in installer
    assert "AguaDashboardSync" in installer
    assert "--no-index" in installer
    assert "wheels" in installer


def test_win7_full_package_builder_includes_python_installer_and_offline_wheels():
    builder = ROOT / "scripts" / "build_coop_sync_package_win7_full.ps1"
    assert builder.exists()
    text = builder.read_text(encoding="utf-8")
    assert "pyinstaller" in text.lower()
    assert "--onefile" in text
    assert "sync.exe" in text
    assert "python-3.8.10.exe" not in text
    assert "INSTALAR_WIN7_COMPLETO.bat" in text


def test_agent_has_simple_dump_restore_mode_for_win7():
    assert (AGENT / "sync_dump_to_vps.bat").exists()
    assert (AGENT / "SINCRONIZAR_DUMP.bat").exists()
    assert (AGENT / "sync_dump_to_vps_hidden.vbs").exists()
    assert (AGENT / "PROGRAMAR_DUMP_WINDOWS7.bat").exists()

    script = (AGENT / "sync_dump_to_vps.bat").read_text(encoding="utf-8")
    assert "mysqldump.exe" in script
    assert "mysql.exe" in script
    assert "--add-drop-table" in script
    assert "SIMPLE_SYNC_TABLES" in script
    assert "host=" in script
    assert "port=" in script
    assert "user=" in script
    assert "password=" in script
    assert "type \"%SRC_CNF%\"" in script
    assert "python" not in script.lower()


def test_agent_has_mysql_cli_mode_for_win7_without_python_or_dump():
    assert (AGENT / "sync_cli_to_vps.ps1").exists()
    assert (AGENT / "SINCRONIZAR_CLI.bat").exists()
    assert (AGENT / "sync_cli_to_vps_hidden.vbs").exists()
    assert (AGENT / "PROGRAMAR_CLI_WINDOWS7.bat").exists()

    script = (AGENT / "sync_cli_to_vps.ps1").read_text(encoding="utf-8")
    assert "mysql.exe" in script
    assert "INSERT INTO" in script
    assert "LOAD DATA LOCAL INFILE" not in script
    assert "local-infile=1" not in script
    assert "mysqldump" not in script.lower()
    assert "python" not in script.lower()
    assert "ConvertTo-Json" not in script
    assert "$MysqlCharset = \"utf8\"" in script
    assert "--default-character-set=$MysqlCharset" in script
    assert "CHARSET=utf8mb4" not in script
    assert "CAST(($id + 0) AS CHAR)" in script
    assert "CAST($id AS CHAR) = ''" in script
    assert '"facturado","estado","Estado" | ForEach-Object' in script
    assert "SqlValue -Value $parts[$i] -Column $Columns[$i]" in script
    assert r'$text -notmatch "^-?\d+$"' in script
    assert "JSON_OBJECT('table'," in script
    assert "$tablesJsonSql" in script
    assert "tables_json JSON NULL" in script
    assert "table + \":\" + $row.rows" not in script


def test_cli_mode_writes_sync_status_with_mysql_json_functions():
    script = (AGENT / "sync_cli_to_vps.ps1").read_text(encoding="utf-8")

    assert "$tableJsonObjects = @()" in script
    assert "JSON_ARRAY(" in script
    assert "JSON_OBJECT(" in script
    assert "VALUES (NOW(), NOW(), 'ok', NULL, \" + $tablesJsonSql + \");" in script
    assert "SqlString $tablesJson" not in script


def test_cli_mode_does_not_fail_completed_sync_when_status_write_fails():
    script = (AGENT / "sync_cli_to_vps.ps1").read_text(encoding="utf-8")

    status_start = script.index("if (-not $DryRun) {", script.index("foreach ($table in $Tables.Keys)"))
    status_end = script.index('$json = "{""status"":""ok""', status_start)
    status_block = script[status_start:status_end]

    assert "try {" in status_block
    assert "No se pudo registrar dashboard_sync_status" in status_block
    assert "throw" not in status_block


def test_cli_mode_honors_mysql_ssl_mode_from_env_file():
    script = (AGENT / "sync_cli_to_vps.ps1").read_text(encoding="utf-8")

    assert '$sslMode = [Environment]::GetEnvironmentVariable($Prefix + "_MYSQL_SSL_MODE")' in script
    assert '"skip-ssl"' in script
    assert '"ssl-verify-server-cert=0"' in script
    assert '"ssl=1"' in script

    env_example = (AGENT / ".env.example").read_text(encoding="utf-8")
    assert "MYSQL_CHARSET=utf8" in env_example


def test_cli_mode_truncates_existing_dirty_rows_before_altering_column_types():
    script = (AGENT / "sync_cli_to_vps.ps1").read_text(encoding="utf-8")

    create_pos = script.index("CREATE TABLE IF NOT EXISTS")
    truncate_pos = script.index("TRUNCATE TABLE")
    alter_pos = script.index("ALTER TABLE")

    assert create_pos < truncate_pos < alter_pos


def test_win7_powershell_scripts_do_not_require_psscriptroot():
    for script_name in ("install_win7.ps1", "run_sync.ps1", "verify.ps1"):
        script = (AGENT / script_name).read_text(encoding="utf-8")
        assert "$MyInvocation.MyCommand.Path" in script
        assert "ConvertTo-Json" not in script
        assert "[ordered]" not in script


def test_win7_agent_docs_explain_legacy_install_flow():
    readme = (AGENT / "README.md").read_text(encoding="utf-8")
    quick_start = (AGENT / "LEER_PRIMERO.txt").read_text(encoding="utf-8")

    assert "Windows 7" in readme
    assert "INSTALAR_WINDOWS7.bat" in readme
    assert "silenciosa" in readme.lower()
    assert "INSTALAR_WINDOWS7.bat" in quick_start
    assert "sync_dump_to_vps.bat" in quick_start
    assert "SINCRONIZAR_DUMP.bat" in quick_start
    assert "SINCRONIZAR_CLI.bat" in quick_start


def test_win7_scripts_prefer_packaged_sync_exe():
    run_sync = (AGENT / "run_sync.ps1").read_text(encoding="utf-8")
    installer = (AGENT / "install_win7.ps1").read_text(encoding="utf-8")
    verifier = (AGENT / "verify.ps1").read_text(encoding="utf-8")
    full_installer = (AGENT / "INSTALAR_WIN7_COMPLETO.bat").read_text(encoding="utf-8")

    assert "sync.exe" in run_sync
    assert "sync.exe" in installer
    assert "sync.exe" in verifier
    assert "python-3.8.10.exe" not in full_installer
