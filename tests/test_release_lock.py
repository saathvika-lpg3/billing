from __future__ import annotations

from pathlib import Path

from config.product_version import DISPLAY_VERSION, PRODUCT_NAME, PRODUCT_VERSION, RELEASE_NAME
from services.dashboard_service import DashboardService


ROOT = Path(__file__).resolve().parents[1]


def test_official_product_version_has_one_runtime_authority() -> None:
    assert PRODUCT_NAME == "PRM BILLING INVENTORY"
    assert PRODUCT_VERSION == "1.0.0"
    assert DISPLAY_VERSION == "V1.0"
    assert RELEASE_NAME == "PRM BILLING INVENTORY V1.0"


def test_release_lock_contains_the_required_non_regression_contract() -> None:
    text = (ROOT / "RELEASE_LOCK.md").read_text(encoding="utf-8")
    required_contracts = (
        "annotated tag `v1.0.0`",
        "Database and licensing lock",
        "Installer and upgrade lock",
        "Product and client branding lock",
        "UI layout and framework lock",
        "Keyboard, focus and smart-dropdown lock",
        "Navigation lock",
        "Transaction and posting lock",
        "GST lock",
        "Print, PDF and report lock",
        "Email and WhatsApp communication lock",
        "Regression gate",
        "Change-control process",
        "Rollback procedure",
        "1366x768, 1440x900 and 1920x1080",
        "A4 Portrait, A4 Landscape, A2 Portrait",
        "Profit & Loss",
        "Balance Sheet",
        "reports:daily_dispatch_summary",
    )
    for contract in required_contracts:
        assert contract in text
    assert "TO_BE_RECORDED" not in text


def test_current_release_documentation_uses_v1_identity() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    current = (ROOT / "CURRENT_STATUS.md").read_text(encoding="utf-8")
    prm_current = (ROOT / "PRM_CURRENT_STATUS.md").read_text(encoding="utf-8")

    assert "V1.0" in readme and "1.0.0" in readme
    assert "V1.0" in current and "1.0.0" in current
    assert "V1.0" in prm_current and "1.0.0" in prm_current


def test_dashboard_separates_runtime_identity_from_schema_history() -> None:
    service = object.__new__(DashboardService)
    service._rows = lambda _sql: [
        {
            "component": "schema_version",
            "version": "20260701_pdf_archive_speed_cache",
            "notes": "Migration order",
            "updated_at": "2026-07-01",
        }
    ]

    rows = service._application_version()

    assert rows[0]["component"] == "Desktop Runtime"
    assert rows[0]["version"] == "V1.0"
    assert rows[1]["component"] == "History: schema_version"
    assert rows[1]["version"] == "20260701_pdf_archive_speed_cache"
