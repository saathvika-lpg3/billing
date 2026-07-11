from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from config.app_config import AppConfig
from services.license_service import LicenseError, LicenseService
from tools.prepare_installer_database import build_installer_database


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DB = ROOT / "database" / "prm_billing_inventory.db"


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
    assert build_script.count("$LASTEXITCODE -ne 0") >= 2
    assert "stale output" in build_script
    assert "$LASTEXITCODE -ne 0" in installer_script
    assert "stale PRM_Billing_Inventory_Setup.exe" in installer_script
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

    assert '#define MyAppVersion "1.7.5"' in inno
    for packaged_folder in ("themes", "assets", "docs", "print_templates"):
        assert f'root / "{packaged_folder}"' in spec
    assert 'root / "audit"' not in spec
    for runtime_file in (
        ROOT / "widgets" / "action_toolbar.py",
        ROOT / "widgets" / "widget_values.py",
        ROOT / "widgets" / "erp_components.py",
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


def test_startup_log_does_not_expose_the_client_license_key() -> None:
    app_source = (ROOT / "app.py").read_text(encoding="utf-8")

    assert "license_context.license_key" not in app_source
    assert "status={license_context.status}" in app_source
