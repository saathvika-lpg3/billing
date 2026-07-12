from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from config.app_config import AppConfig
from services.license_service import LicenseError, LicenseService
from tools.prepare_installer_database import build_installer_database


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DB = ROOT / "database" / "prm_billing_inventory_seed.db"


def _write_test_license(root: Path) -> Path:
    license_dir = root / "license"
    license_dir.mkdir(parents=True, exist_ok=True)
    path = license_dir / "client.prmlic"
    path.write_text(
        json.dumps(
            {
                "format": "PRM_CLIENT_LICENSE",
                "version": "2026-06-28",
                "client_company_name": "Installer QA Client",
                "phone_number": "9000000000",
                "area": "QA Area",
                "license_key": "PRM-INSTALLQA-2026-ABC123",
                "installation_key": "INST-INSTALL-QA",
                "super_admin_username": "admin@installer.qa",
                "super_admin_password": "InstallerQA@123",
                "developer_login_key": "DEV-INSTALL-QA",
                "plan": "Premium",
                "expiry_date": "2099-12-31",
                "status": "Active",
                "business_type_code": "distributor_wholesale",
            }
        ),
        encoding="utf-8",
    )
    return path


def test_installer_seed_is_unbound_and_contains_no_client_runtime_rows(tmp_path: Path) -> None:
    seed = tmp_path / "prm_billing_inventory.db"

    result = build_installer_database(SOURCE_DB, seed)

    assert result["integrity"] == "ok"
    assert result["license_activation_rows"] == 0
    assert result["license_rows"] == 0
    assert result["user_rows"] == 0
    assert result["transaction_rows"] == 0
    with sqlite3.connect(seed) as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        for table in (
            "company",
            "license",
            "license_activation",
            "users",
            "customers",
            "suppliers",
            "items",
            "sales",
            "purchases",
            "receipts",
            "payments",
            "ledger_postings",
            "gst_postings",
            "app_settings",
        ):
            assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM print_templates").fetchone()[0] > 0
        assert conn.execute("SELECT COUNT(*) FROM dev_business_types").fetchone()[0] > 0


def test_fresh_seed_binds_license_but_foreign_machine_binding_stays_blocked(tmp_path: Path) -> None:
    seed = tmp_path / "prm_billing_inventory.db"
    build_installer_database(SOURCE_DB, seed)
    _write_test_license(tmp_path)
    service = LicenseService(AppConfig(tmp_path, tmp_path), seed)
    context = service.require_license()

    service.apply_to_database(context)

    with sqlite3.connect(seed) as conn:
        activation = conn.execute(
            "SELECT machine_hash,status,expiry_date FROM license_activation"
        ).fetchone()
        assert activation is not None
        assert activation[0] == service.machine_hash()
        assert activation[1] == "Active"
        assert activation[2] == "2099-12-31"
        conn.execute("UPDATE license_activation SET machine_hash='foreign-machine'")

    with pytest.raises(LicenseError, match="already activated on another machine"):
        service.apply_to_database(context)


def test_installer_preserves_database_and_uses_sanitized_seed() -> None:
    spec = (ROOT / "PRM_Billing_Inventory.spec").read_text(encoding="utf-8")
    inno = (ROOT / "installer" / "prm_billing_inventory.iss").read_text(encoding="utf-8")
    build_script = (ROOT / "tools" / "build_desktop.ps1").read_text(encoding="utf-8")
    installer_script = (ROOT / "tools" / "build_installer.ps1").read_text(encoding="utf-8")

    assert "installer_payload" in spec
    assert 'root / "database" / "prm_billing_inventory.db"' not in spec
    assert 'root / "uploads"' not in spec
    assert '"pysqlite"' not in spec
    assert "prepare_installer_database.py" in build_script
    assert '--source "$Root\\database\\prm_billing_inventory_seed.db"' in build_script
    assert build_script.count("$LASTEXITCODE -ne 0") >= 2
    assert "stale output" in build_script
    assert "$LASTEXITCODE -ne 0" in installer_script
    assert "stale PRM_Billing_Inventory_V1.0_Setup.exe" in installer_script
    assert 'Excludes: "_internal\\database\\prm_billing_inventory.db"' in inno
    database_line = next(
        line
        for line in inno.splitlines()
        if line.startswith('Source: "..\\dist\\PRM_Billing_Inventory\\_internal\\database')
    )
    assert "onlyifdoesntexist" in database_line
    assert "uninsneveruninstall" in database_line


def test_installer_json_preflight_lists_all_required_snake_case_fields() -> None:
    inno = (ROOT / "installer" / "prm_billing_inventory.iss").read_text(encoding="utf-8")
    required = {
        "client_company_name",
        "phone_number",
        "area",
        "license_key",
        "installation_key",
        "super_admin_username",
        "super_admin_password",
        "developer_login_key",
        "plan",
        "expiry_date",
        "status",
        "business_type_code",
    }
    for field in required:
        assert f'"{field}"' in inno


def test_installer_release_includes_stabilized_ui_resources() -> None:
    spec = (ROOT / "PRM_Billing_Inventory.spec").read_text(encoding="utf-8")
    inno = (ROOT / "installer" / "prm_billing_inventory.iss").read_text(encoding="utf-8")
    smoke_source = (ROOT / "tools" / "smoke_installed_ui.py").read_text(encoding="utf-8")

    assert '#define MyAppName "PRM BILLING INVENTORY"' in inno
    assert '#define MyAppVersion "1.0.0"' in inno
    assert '#define MyAppDisplayVersion "V1.0"' in inno
    for packaged_folder in ("themes", "assets", "print_templates"):
        assert f'root / "{packaged_folder}"' in spec
    assert 'root / "docs"' not in spec
    assert 'root / "audit"' not in spec
    assert 'excludes=["numpy", "lxml"]' in spec
    for runtime_file in (
        ROOT / "widgets" / "action_toolbar.py",
        ROOT / "widgets" / "widget_values.py",
        ROOT / "widgets" / "erp_components.py",
        ROOT / "widgets" / "company_branding.py",
        ROOT / "widgets" / "product_branding.py",
        ROOT / "widgets" / "navigation.py",
        ROOT / "widgets" / "smart_combo.py",
        ROOT / "views" / "product_master_view.py",
        ROOT / "views" / "sales_bill_view.py",
        ROOT / "views" / "purchase_entry_view.py",
        ROOT / "themes" / "light.qss",
        ROOT / "themes" / "dark.qss",
        ROOT / "tools" / "smoke_installed_ui.py",
    ):
        assert runtime_file.is_file(), runtime_file
    assert "TemporaryDirectory" in smoke_source
    assert "shutil.copy2(installed_db_path, db_path)" in smoke_source
    assert 'result["installed_database_unchanged"] = True' in smoke_source
    assert "SetupIconFile=..\\assets\\PRM_SoftSolutions.ico" in inno
    assert "UninstallDisplayIcon={app}\\{#MyAppExeName}" in inno
    assert "ClientCompanyIdentityCard" not in inno
    assert "Installed shell is missing the official V1.0 display version" in smoke_source
    assert "Installed window has unexpected release title" in smoke_source
    assert inno.count("[InstallDelete]") == 1
    install_delete_section = inno.split("[InstallDelete]", 1)[1].split("[Icons]", 1)[0]
    install_delete_entries = {
        line.strip()
        for line in install_delete_section.splitlines()
        if line.strip().startswith("Type:")
    }
    assert install_delete_entries == {
        'Type: filesandordirs; Name: "{app}\\_internal\\numpy"',
        'Type: filesandordirs; Name: "{app}\\_internal\\numpy.libs"',
        'Type: filesandordirs; Name: "{app}\\_internal\\numpy-*.dist-info"',
        'Type: filesandordirs; Name: "{app}\\_internal\\lxml"',
        'Type: filesandordirs; Name: "{app}\\_internal\\lxml-*.dist-info"',
        'Type: filesandordirs; Name: "{app}\\_internal\\docs"',
        'Type: files; Name: "{app}\\_internal\\requirements.txt"',
    }
    protected_client_data = {
        "prm_billing_inventory.db",
        ".prmlic",
        "settings",
        "company_logo",
        "smtp",
        "communication",
        "backup",
    }
    install_delete_paths = "\n".join(install_delete_entries).lower()
    assert not any(item in install_delete_paths for item in protected_client_data)


def test_official_v1_installer_identity_and_internal_upgrade_contract() -> None:
    inno = (ROOT / "installer" / "prm_billing_inventory.iss").read_text(encoding="utf-8")
    build_script = (ROOT / "tools" / "build_installer.ps1").read_text(encoding="utf-8")

    assert "AppId={{7E5E6B90-836B-4D97-B252-7C08A6BE1001}" in inno
    assert "Official V1.0 intentionally supersedes the internal 1.7.8 prerelease" in inno
    assert "AppVerName={#MyAppName} {#MyAppDisplayVersion}" in inno
    assert "UninstallDisplayName={#MyAppName} {#MyAppDisplayVersion}" in inno
    assert "OutputBaseFilename=PRM_Billing_Inventory_V1.0_Setup" in inno
    assert '#define MyAppExeName "PRM_Billing_Inventory.exe"' in inno
    runtime_line = next(
        line
        for line in inno.splitlines()
        if line.startswith('Source: "..\\dist\\PRM_Billing_Inventory\\*"')
    )
    assert "ignoreversion" in runtime_line
    assert "$InternalPrereleaseSetup" in build_script
    assert "$InternalPrereleaseHash" in build_script
    assert "Get-FileHash" in build_script
    assert "Remove-Item" not in build_script


def test_windows_executable_and_setup_have_v1_metadata() -> None:
    spec = (ROOT / "PRM_Billing_Inventory.spec").read_text(encoding="utf-8")
    inno = (ROOT / "installer" / "prm_billing_inventory.iss").read_text(encoding="utf-8")
    version_info = (ROOT / "installer" / "windows_version_info.txt").read_text(encoding="utf-8")

    assert 'version=str(root / "installer" / "windows_version_info.txt")' in spec
    assert "VersionInfoVersion=1.0.0.0" in inno
    assert "VersionInfoProductVersion=1.0.0.0" in inno
    assert "VersionInfoTextVersion={#MyAppVersion}" in inno
    assert "VersionInfoProductTextVersion={#MyAppVersion}" in inno
    assert "filevers=(1, 0, 0, 0)" in version_info
    assert "prodvers=(1, 0, 0, 0)" in version_info
    assert "StringStruct(u'ProductName', u'PRM BILLING INVENTORY')" in version_info
    assert "StringStruct(u'ProductVersion', u'1.0.0')" in version_info
    assert "StringStruct(u'OriginalFilename', u'PRM_Billing_Inventory.exe')" in version_info


def test_installer_browse_accepts_any_valid_client_prmlic_filename() -> None:
    inno = (ROOT / "installer" / "prm_billing_inventory.iss").read_text(encoding="utf-8")
    assert "CreateInputFilePage" in inno
    assert "Browse and select client .prmlic file:" in inno
    assert "PRM license files (*.prmlic)|*.prmlic" in inno
    assert "ExtractFileExt(FileName)" in inno
    assert "CopyFile(ClientLicenseFile, DestFile, False)" in inno
    assert "DestFile := DestDir + '\\client.prmlic'" in inno
    assert "lakshmi.prmlic" not in inno.lower()


def test_startup_log_does_not_expose_the_client_license_key() -> None:
    app_source = (ROOT / "app.py").read_text(encoding="utf-8")

    assert "license_context.license_key" not in app_source
    assert "status={license_context.status}" in app_source
    main_source = (ROOT / "views" / "main_window.py").read_text(encoding="utf-8")
    assert 'f"company={self.company_profile}"' not in main_source
