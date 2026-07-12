from __future__ import annotations

import os
import shutil
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QImage
from PyQt6.QtWidgets import QApplication, QFrame, QLabel

from config.app_config import AppConfig
from services.license_service import LicenseContext
from views.login_dialog import LoginDialog
from views.main_window import MainWindow
from widgets.company_branding import ClientCompanyIdentityCard, resolve_client_company_logo
from widgets.product_branding import PRODUCT_NAME, PRODUCT_TAGLINE, ProductBrandHeader, resolve_product_logo


ROOT = Path(__file__).resolve().parents[1]
_APP: QApplication | None = None


def _app() -> QApplication:
    global _APP
    _APP = QApplication.instance() or _APP or QApplication([])
    return _APP


def _config(root: Path = ROOT) -> AppConfig:
    return AppConfig(root, root)


def _isolate_database(tmp_path: Path, monkeypatch) -> Path:
    isolated = tmp_path / "branding_test.db"
    shutil.copy2(ROOT / "database" / "prm_billing_inventory.db", isolated)
    monkeypatch.setenv("PRM_SQLITE_DB", str(isolated))
    monkeypatch.setenv("PRM_USE_SQLITE", "0")
    return isolated


def _company(**overrides: str) -> dict[str, str]:
    company = {
        "company_name": "Licensed Sample Enterprise",
        "business_type_code": "distributor_wholesale",
        "phone": "9000000000",
        "email": "accounts@example.test",
        "address": "Test Market Road",
        "city": "Hyderabad",
        "state": "Telangana",
    }
    company.update(overrides)
    return company


def _license_context(tmp_path: Path) -> LicenseContext:
    return LicenseContext(
        source_path=tmp_path / "lakshmi.prmlic",
        company_name="Licensed Sample Enterprise",
        phone_number="9000000000",
        area="Hyderabad",
        license_key="PRM-QA-2026-BRAND",
        installation_key="INSTALL-BRAND",
        super_admin_username="admin@example.test",
        super_admin_password="test-only",
        developer_login_key="test-only",
        plan="premium",
        expiry_date="2027-12-31",
        status="active",
        business_type_code="distributor_wholesale",
        payload={},
        raw_text="test-only",
    )


def test_main_shell_uses_prm_product_brand_and_never_client_identity(monkeypatch, tmp_path: Path) -> None:
    _isolate_database(tmp_path, monkeypatch)
    _app()
    company = _company()
    monkeypatch.setattr(
        "views.main_window.CompanyProfileService.current_profile",
        lambda _service: dict(company),
    )
    monkeypatch.setattr(
        "views.dashboard_view.DashboardService.snapshot",
        lambda _service: {"company": dict(company)},
    )
    window = MainWindow(_config())
    try:
        window.resize(1366, 768)
        window.show()
        QApplication.processEvents()
        top_bar = window.findChild(QFrame, "topBar")
        product = top_bar.findChild(ProductBrandHeader, "productBrandHeader")
        assert product is window.product_brand
        assert product.title_label.text() == PRODUCT_NAME
        assert product.tagline_label.text() == PRODUCT_TAGLINE
        assert product.logo.pixmap() is not None and not product.logo.pixmap().isNull()
        assert not top_bar.findChildren(ClientCompanyIdentityCard)
        top_text = " | ".join(label.text() for label in top_bar.findChildren(QLabel))
        assert company["company_name"] not in top_text

        dashboard = window.pages["dashboard"]
        assert dashboard.company_brand.name_label.text() == company["company_name"]
        assert dashboard.company_brand.logo.width() == 144
        assert dashboard.company_brand.logo.height() == 96
        assert dashboard.cards["company"].minimumHeight() >= 300
        assert dashboard.company_brand.name_label.geometry().top() >= dashboard.company_brand.logo.geometry().bottom()
    finally:
        window.close()


def test_client_logo_keeps_aspect_ratio_and_invalid_path_never_falls_back_to_product(tmp_path: Path) -> None:
    _app()
    logo_path = tmp_path / "client-wide.png"
    image = QImage(240, 80, QImage.Format.Format_ARGB32)
    image.fill(QColor(10, 120, 210, 180))
    assert image.save(str(logo_path))

    card = ClientCompanyIdentityCard(_config(tmp_path), _company(logo_path=str(logo_path)))
    try:
        displayed = card.logo.pixmap()
        assert displayed is not None and not displayed.isNull()
        assert card.logo.width() == 144 and card.logo.height() == 96
        assert abs((displayed.width() / displayed.height()) - 3.0) < 0.08
        assert card.logo.property("clientLogoPlaceholder") is False
    finally:
        card.close()

    invalid = ClientCompanyIdentityCard(
        _config(ROOT),
        _company(logo_path="missing/PRM_SoftSolutions.jpg"),
    )
    try:
        assert invalid.logo.property("clientLogoPlaceholder") is True
        assert invalid.logo.text() == "LSE"
        assert resolve_client_company_logo(_config(ROOT), _company(logo_path="missing/PRM_SoftSolutions.jpg")) is None
        assert resolve_product_logo(_config(ROOT)) is not None
    finally:
        invalid.close()


def test_switching_client_identity_does_not_change_product_logo() -> None:
    _app()
    product = ProductBrandHeader(_config())
    client = ClientCompanyIdentityCard(_config(), _company())
    try:
        before = product.logo.pixmap().cacheKey()
        client.set_company(_company(company_name="Second Sample Distributors"))
        assert client.name_label.text() == "Second Sample Distributors"
        assert product.logo.pixmap().cacheKey() == before
        assert product.title_label.text() == PRODUCT_NAME
    finally:
        product.close()
        client.close()


def test_login_keeps_product_and_client_branding_in_separate_components(tmp_path: Path) -> None:
    _app()
    context = _license_context(tmp_path)
    isolated = tmp_path / "login_test.db"
    shutil.copy2(ROOT / "database" / "prm_billing_inventory.db", isolated)
    license_service = SimpleNamespace(db_path=isolated)
    dialog = LoginDialog(_config(), context, license_service)
    try:
        assert dialog.product_brand.title_label.text() == PRODUCT_NAME
        assert dialog.product_brand.logo.pixmap() is not None
        assert dialog.client_company_identity.name_label.text()
        assert dialog.product_brand.findChild(QLabel, "clientLogo") is None
    finally:
        dialog.close()
