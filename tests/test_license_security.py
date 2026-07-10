from __future__ import annotations

import json
import shutil
from pathlib import Path

from config.app_config import AppConfig
from services.license_service import LicenseService


SOURCE_DB = Path(r"D:\PRM_GST_DESKTOP\database\prm_billing_inventory.db")


def test_prmlic_json_applies_license_and_authenticates_super_admin(tmp_path: Path) -> None:
    db_path = tmp_path / "prm_billing_inventory.db"
    shutil.copy2(SOURCE_DB, db_path)
    license_path = tmp_path / "client.prmlic"
    license_path.write_text(
        json.dumps(
            {
                "format": "PRM_CLIENT_LICENSE",
                "version": "2026-06-28",
                "client_company_name": "QA Client",
                "phone_number": "9000000000",
                "area": "QA Area",
                "license_key": "PRM-QA-2026-ABC123",
                "installation_key": "INST-QA-2026-ABC123",
                "super_admin_username": "admin@qa.local",
                "super_admin_password": "Admin@123",
                "developer_login_key": "DEV-QA-2026-ABC123",
                "plan": "Premium",
                "expiry_date": "2027-06-28",
                "status": "Active",
                "business_type_code": "distributor_wholesale",
            }
        ),
        encoding="utf-8",
    )
    config = AppConfig(project_root=tmp_path, source_root=tmp_path)
    (tmp_path / "license").mkdir()
    shutil.copy2(license_path, tmp_path / "license" / "client.prmlic")

    service = LicenseService(config, db_path)
    context = service.require_license()
    service.apply_to_database(context)

    session = service.authenticate_user("admin@qa.local", "Admin@123", context)

    assert context.company_name == "QA Client"
    assert context.plan_code == "premium"
    assert session is not None
    assert session["role"] == "admin"
    assert service.validate_developer_key("DEV-QA-2026-ABC123", context)
