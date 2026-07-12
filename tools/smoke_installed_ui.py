from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_smoke(install_root: Path) -> dict[str, object]:
    install_root = install_root.resolve()
    installed_db_path = install_root / "_internal" / "database" / "prm_billing_inventory.db"
    license_path = install_root / "license" / "client.prmlic"
    if not (install_root / "PRM_Billing_Inventory.exe").is_file():
        raise FileNotFoundError("Installed executable is missing")
    if not installed_db_path.is_file() or not license_path.is_file():
        raise FileNotFoundError("Installed database or client license is missing")

    installed_hash_before = _sha256(installed_db_path)
    with tempfile.TemporaryDirectory(prefix="prm_installed_ui_smoke_") as temp_dir:
        db_path = Path(temp_dir) / "prm_billing_inventory.db"
        shutil.copy2(installed_db_path, db_path)
        result = _run_smoke_on_database(install_root, db_path, license_path)
        gc.collect()
    installed_hash_after = _sha256(installed_db_path)
    if installed_hash_after != installed_hash_before:
        raise RuntimeError("Installed database changed during the disposable-copy UI smoke")
    result["database_mode"] = "disposable-copy"
    result["installed_database_unchanged"] = True
    result["installed_database_sha256"] = installed_hash_after
    return result


def _run_smoke_on_database(
    install_root: Path,
    db_path: Path,
    license_path: Path,
) -> dict[str, object]:

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ["PRM_SQLITE_DB"] = str(db_path)
    os.environ["PRM_CLIENT_LICENSE_FILE"] = str(license_path)
    os.environ["PRM_USE_SQLITE"] = "0"

    from PyQt6.QtCore import QCoreApplication, QEvent
    from PyQt6.QtWidgets import QApplication, QFrame, QMessageBox

    from config.app_config import AppConfig
    from config.product_version import DISPLAY_VERSION, RELEASE_NAME
    from services.license_service import LicenseService
    from services.master_repository import MasterRepository
    from views.main_window import MainWindow
    from widgets.action_toolbar import CompactActionToolbar
    from widgets.company_branding import ClientCompanyIdentityCard
    from widgets.erp_components import TransactionTotalsPanel
    from widgets.product_branding import PRODUCT_NAME, ProductBrandHeader

    config = AppConfig(install_root, install_root)
    license_service = LicenseService(config, db_path=db_path)
    context = license_service.require_license()
    license_service.apply_to_database(context)
    session = license_service.authenticate_user(
        context.super_admin_username,
        context.super_admin_password,
        context,
    )
    if not session:
        raise RuntimeError("Installed QA administrator could not authenticate")

    repository = MasterRepository(db_path)
    repository.ensure_schema()
    category_name = "Installer QA Category"
    with sqlite3.connect(db_path) as conn:
        category_exists = conn.execute(
            "SELECT 1 FROM item_categories WHERE name=? LIMIT 1",
            (category_name,),
        ).fetchone()
    if not category_exists:
        repository.save_simple(
            "category",
            0,
            {"code": "INSTALL-QA", "name": category_name, "default_gst": 18, "is_active": True},
        )

    application = QApplication.instance() or QApplication([])
    QMessageBox.information = lambda *args, **kwargs: None
    QMessageBox.warning = lambda *args, **kwargs: None
    QMessageBox.critical = lambda *args, **kwargs: None
    window = MainWindow(
        config,
        start_page="dashboard",
        license_context=context,
        license_service=license_service,
        session=session,
    )
    window.resize(1366, 768)
    window.show()
    application.processEvents()

    product_brand = window.findChild(ProductBrandHeader, "productBrandHeader")
    if product_brand is None or product_brand.title_label.text() != PRODUCT_NAME:
        raise RuntimeError("Installed shell is missing PRM product branding")
    if product_brand.version_label.text() != DISPLAY_VERSION:
        raise RuntimeError("Installed shell is missing the official V1.0 display version")
    if window.windowTitle() != RELEASE_NAME:
        raise RuntimeError(f"Installed window has unexpected release title: {window.windowTitle()}")
    if product_brand.logo.pixmap() is None or product_brand.logo.pixmap().isNull():
        raise RuntimeError("Installed PRM product logo did not load")
    top_bar = window.findChild(QFrame, "topBar")
    if top_bar is None or top_bar.findChildren(ClientCompanyIdentityCard):
        raise RuntimeError("Installed shell incorrectly contains client branding in the product header")
    dashboard_brand = window.pages["dashboard"].company_brand
    if dashboard_brand.logo.width() < 120 or dashboard_brand.logo.height() < 80:
        raise RuntimeError("Installed dashboard client logo area is not professionally sized")
    if "reports:daily_dispatch_summary" not in window.sidebar_buttons:
        raise RuntimeError("Installed sidebar is missing Dispatch Summary")

    route_results: dict[str, str] = {}
    for route in ("product_master", "sales_bill", "purchase_entry", "sales", "reports"):
        window.open_page(route, remember=False)
        application.processEvents()
        application.processEvents()
        page = window.pages[route]
        if page.property("factoryFallback") is True:
            raise RuntimeError(f"Installed route opened fallback page: {route}")
        route_results[route] = type(page).__name__

    window.open_page("reports:daily_dispatch_summary", remember=False)
    application.processEvents()
    report_view = window.pages["reports"]
    if window.current_route != "reports:daily_dispatch_summary" or report_view.report.currentData() != "daily_dispatch_summary":
        raise RuntimeError("Installed Dispatch Summary route did not open the canonical report")
    dispatch_summary_route = window.current_route
    route_results["reports:daily_dispatch_summary"] = type(report_view).__name__

    product_view = window.pages["product_master"]
    unique = str(int(time.time() * 1000))
    product_code = f"INSTALL-SMOKE-{unique}"
    product_view.code.setText(product_code)
    product_view.name.setText("Installer Smoke Product")
    product_view.category.setCurrentText(category_name)
    product_view.hsn.setText("1234")
    if product_view.gst.findText("18.00") >= 0:
        product_view.gst.setCurrentText("18.00")
    unit = product_view.sale_unit.itemText(0) or "PCS"
    product_view.sale_unit.setCurrentText(unit)
    product_view.purchase_unit.setCurrentText(unit)
    product_view.pack_table.cellWidget(0, 1).setCurrentText(unit)
    product_view.pack_table.item(0, 2).setText(f"1 {unit}")
    product_view.pack_table.item(0, 3).setText(f"INSTALL-{unique}")
    product_view.pack_table.item(0, 6).setText("100")
    product_view.pack_table.item(0, 9).setText("70")
    product_view.pack_table.item(0, 10).setText("90")
    product_view.add_pack_row(
        {
            "pack_size": 10,
            "pack_unit": unit,
            "display_name": f"Box of 10 {unit}",
            "barcode": f"INSTALL-BOX-{unique}",
            "mrp": 950,
            "purchase_rate": 650,
            "sale_rate": 850,
            "current_stock_qty": 3,
            "is_default": 0,
            "is_active": 1,
        }
    )
    product_view.save_draft()
    if product_view.product_id <= 0:
        raise RuntimeError("Installed Product Master did not save the QA product")
    saved_id = int(product_view.product_id)
    saved_product = product_view.product_by_id.get(saved_id)
    if not saved_product:
        raise RuntimeError("Saved QA product was not returned by Product Master refresh")
    product_view.clear_form()
    product_view.load_product(saved_product)
    if product_view.product_id != saved_id or product_view.pack_table.rowCount() != 2:
        raise RuntimeError("Installed Product Master did not reload both QA package rows")

    viewport = window.content_scroll.viewport()
    grand_total_routes: dict[str, bool] = {}
    for route in ("sales_bill", "purchase_entry"):
        window.open_page(route, remember=False)
        application.processEvents()
        application.processEvents()
        panel = window.pages[route].findChild(TransactionTotalsPanel)
        if panel is None:
            raise RuntimeError(f"Installed route has no shared totals panel: {route}")
        grand = panel.labels["grand_total"]
        top = grand.mapTo(viewport, grand.rect().topLeft()).y()
        bottom = grand.mapTo(viewport, grand.rect().bottomLeft()).y()
        visible = 0 <= top < bottom <= viewport.height()
        grand_total_routes[route] = visible
        if not visible:
            raise RuntimeError(f"Installed Grand Total is outside viewport: {route}")

    window.open_page("sales", remember=False)
    application.processEvents()
    list_toolbar = window.pages["sales"].findChild(CompactActionToolbar)
    horizontal_toolbar = bool(list_toolbar and list_toolbar.property("actionLayout") == "horizontal-wrap")
    if not horizontal_toolbar:
        raise RuntimeError("Installed Sales list is missing the horizontal action toolbar")

    window.apply_theme("dark")
    window.apply_theme("light")
    application.processEvents()

    # Capture Qt-owned values before closing/deleting the window. Accessing a
    # wrapped child widget after DeferredDelete raises and can also skip the
    # outer smoke cleanup, leaving the disposable database locked on Windows.
    product_name = product_brand.title_label.text()
    dashboard_client_logo_area = [dashboard_brand.logo.width(), dashboard_brand.logo.height()]
    product_reloaded = product_view.product_id == saved_id

    for page in window.pages.values():
        source = getattr(page, "source", None)
        closer = getattr(source, "close_database_resources", None)
        if callable(closer):
            closer()
    window.close()
    window.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    application.processEvents()

    with sqlite3.connect(db_path) as conn:
        integrity = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
        saved_count = int(conn.execute("SELECT COUNT(*) FROM items WHERE code=?", (product_code,)).fetchone()[0])
        saved_pack_count = int(
            conn.execute("SELECT COUNT(*) FROM product_packs WHERE product_id=?", (saved_id,)).fetchone()[0]
        )
        activation_rows = int(conn.execute("SELECT COUNT(*) FROM license_activation").fetchone()[0])
        user_rows = int(conn.execute("SELECT COUNT(*) FROM users").fetchone()[0])
    if integrity != "ok" or saved_count != 1 or saved_pack_count != 2:
        raise RuntimeError("Installed database integrity or Product Master persistence check failed")

    return {
        "install_root": str(install_root),
        "working_database": str(db_path),
        "integrity": integrity,
        "authenticated_role": str(session.get("role") or ""),
        "routes": route_results,
        "product_save_rows": saved_count,
        "product_pack_rows": saved_pack_count,
        "product_reloaded": product_reloaded,
        "product_id": saved_id,
        "grand_total_visible": grand_total_routes,
        "horizontal_list_toolbar": horizontal_toolbar,
        "product_branding": {
            "product_name": product_name,
            "display_version": DISPLAY_VERSION,
            "window_title": RELEASE_NAME,
            "product_logo_loaded": True,
            "client_identity_in_top_bar": False,
        },
        "dashboard_client_logo_area": dashboard_client_logo_area,
        "dispatch_summary_route": dispatch_summary_route,
        "themes_loaded": ["dark", "light"],
        "license_activation_rows": activation_rows,
        "user_rows": user_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Smoke-test installed PRM resources using a disposable database copy."
    )
    parser.add_argument("--install-root", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = run_smoke(args.install_root)
    output = json.dumps(result, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
