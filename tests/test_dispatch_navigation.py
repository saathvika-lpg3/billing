from __future__ import annotations

import os
import shutil
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QApplication, QMessageBox

from config.app_config import AppConfig
from services.license_service import LicenseContext
from services.mysql_source import MySqlSource
from views.global_search_view import GlobalSearchView
from views.main_window import MainWindow
from views.module_hub_view import REPORTS_OPERATIONS
from views.report_center_view import REPORT_CATALOG


ROOT = Path(__file__).resolve().parents[1]
ROUTE = "reports:daily_dispatch_summary"
_APP: QApplication | None = None


def _app() -> QApplication:
    global _APP
    _APP = QApplication.instance() or _APP or QApplication([])
    return _APP


def _config() -> AppConfig:
    return AppConfig(ROOT, ROOT)


def _isolate_database(tmp_path: Path, monkeypatch) -> None:
    isolated = tmp_path / "dispatch_navigation_test.db"
    shutil.copy2(ROOT / "database" / "prm_billing_inventory.db", isolated)
    monkeypatch.setenv("PRM_SQLITE_DB", str(isolated))
    monkeypatch.setenv("PRM_USE_SQLITE", "0")


def _license(plan: str) -> LicenseContext:
    return LicenseContext(
        source_path=ROOT / "license" / "client.prmlic",
        company_name="Navigation QA",
        phone_number="9000000000",
        area="QA",
        license_key="PRM-QA-2026-NAV",
        installation_key="INSTALL-NAV",
        super_admin_username="admin@example.test",
        super_admin_password="test-only",
        developer_login_key="test-only",
        plan=plan,
        expiry_date="2027-12-31",
        status="active",
        business_type_code="distributor_wholesale",
        payload={},
        raw_text="test-only",
    )


def test_dispatch_summary_uses_one_canonical_route_everywhere(monkeypatch, tmp_path: Path) -> None:
    _isolate_database(tmp_path, monkeypatch)
    _app()
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)
    window = MainWindow(_config(), license_context=_license("premium"), session={"role": "admin"})
    try:
        assert list(window.sidebar_buttons).count(ROUTE) == 1
        window.sidebar_buttons[ROUTE].click()
        QApplication.processEvents()
        assert window.current_route == ROUTE
        assert window.current_page == "reports"
        assert window.pages["reports"].report.currentData() == "daily_dispatch_summary"
        assert window.sidebar_buttons[ROUTE].property("active") is True
        assert window.pages["dashboard"].dispatch_summary_button is not None
        assert sum(operation.key == "daily_dispatch_summary" for operation in REPORTS_OPERATIONS) == 1
        assert sum(key == "daily_dispatch_summary" for _group, _label, key in REPORT_CATALOG) == 1
        window.go_back()
        assert window.current_route == "dashboard"
    finally:
        window.close()


def test_dispatch_summary_search_aliases_and_enter_activation(monkeypatch, tmp_path: Path) -> None:
    _isolate_database(tmp_path, monkeypatch)
    _app()
    source = MySqlSource()
    for query in ("Dispatch", "Dispatch Summary", "Loading", "Loading Sheet"):
        targets = {str(row.get("target_page")) for row in source.global_search(query, 100, 0)["rows"]}
        assert ROUTE in targets, query

    opened: list[str] = []
    view = GlobalSearchView(_config(), opened.append, lambda route: route == ROUTE)
    try:
        view.open_search("Dispatch Summary")
        assert view.rows and view.rows[0]["target_page"] == ROUTE
        view.table.setCurrentCell(0, 0)
        view.table.itemActivated.emit(view.table.item(0, 0))
        assert opened == [ROUTE]
    finally:
        view.close()


def test_dispatch_navigation_keyboard_and_basic_plan_permission(monkeypatch, tmp_path: Path) -> None:
    _isolate_database(tmp_path, monkeypatch)
    _app()
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)
    premium = MainWindow(_config(), license_context=_license("premium"), session={"role": "admin"})
    try:
        premium.show()
        QApplication.processEvents()
        first = premium.sidebar_buttons["dashboard"]
        second = premium.sidebar_buttons["sales"]
        first.setFocus()
        QApplication.processEvents()
        first.keyPressEvent(QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Down, Qt.KeyboardModifier.NoModifier))
        QApplication.processEvents()
        assert second.hasFocus()
        second.keyPressEvent(QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier))
        assert premium.current_route == "sales"
        assert "Up/Down" in second.toolTip()
        assert second.accessibleName() == "Open Sales"
    finally:
        premium.close()

    basic = MainWindow(_config(), license_context=_license("basic"), session={"role": "admin"})
    try:
        assert ROUTE not in basic.sidebar_buttons
        assert basic.can_open_route(ROUTE) is False
        basic.open_page(ROUTE)
        assert basic.current_route == "dashboard"
    finally:
        basic.close()
