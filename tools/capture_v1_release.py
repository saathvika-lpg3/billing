from __future__ import annotations

import argparse
import gc
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QFrame

from config.app_config import AppConfig
from config.product_version import DISPLAY_VERSION, PRODUCT_VERSION, RELEASE_NAME
from config.qt_fonts import ensure_application_font
from services.license_service import LicenseContext
from services.pdf_print import write_statement_pdf, write_transaction_pdf
from views.login_dialog import LoginDialog
from views.main_window import MainWindow


SYNTHETIC_COMPANY = {
    "name": "V1 Release Validation Company",
    "business_name": "V1 Release Validation Company",
    "gstin": "36ABCDE1234F1Z5",
    "phone": "9000000000",
    "email": "operator@example.test",
    "address": "Release Validation Road",
    "city": "Hyderabad",
    "state": "Telangana",
    "country": "India",
    "pincode": "500001",
    "business_type_code": "distributor_wholesale",
    "invoice_template_code": "",
    "subscription_plan_code": "premium",
}


def _prepare_database(target: Path) -> None:
    seed = PROJECT_ROOT / "database" / "prm_billing_inventory_seed.db"
    if not seed.is_file():
        raise FileNotFoundError(f"Product-owned sanitized seed is missing: {seed}")
    shutil.copy2(seed, target)
    with sqlite3.connect(target) as conn:
        runtime_tables = (
            "company",
            "license",
            "license_activation",
            "users",
            "customers",
            "suppliers",
            "items",
            "sales",
            "purchases",
        )
        for table in runtime_tables:
            count = int(conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])
            if count:
                raise RuntimeError(f"Sanitized release seed unexpectedly contains {table} rows")
        columns = {str(row[1]) for row in conn.execute("PRAGMA table_info(company)")}
        values = {key: value for key, value in SYNTHETIC_COMPANY.items() if key in columns}
        names = ",".join(f'"{name}"' for name in values)
        placeholders = ",".join("?" for _ in values)
        conn.execute(
            f"INSERT INTO company ({names}) VALUES ({placeholders})",
            tuple(values.values()),
        )
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def _license_context(temp_dir: Path) -> LicenseContext:
    return LicenseContext(
        source_path=temp_dir / "synthetic-release.prmlic",
        company_name=SYNTHETIC_COMPANY["name"],
        phone_number=SYNTHETIC_COMPANY["phone"],
        area=SYNTHETIC_COMPANY["city"],
        license_key="PRM-V1-RELEASE-VALIDATION",
        installation_key="INSTALL-V1-RELEASE-VALIDATION",
        super_admin_username="operator@example.test",
        super_admin_password="test-only",
        developer_login_key="test-only",
        plan="premium",
        expiry_date="2099-12-31",
        status="active",
        business_type_code="distributor_wholesale",
        payload={},
        raw_text="synthetic-test-only",
    )


def _settle(application: QApplication) -> None:
    for _ in range(5):
        QApplication.sendPostedEvents()
        application.processEvents()
        QTest.qWait(120)


def _capture_ui(output: Path, db_path: Path, temp_dir: Path) -> list[Path]:
    os.environ["PRM_SQLITE_DB"] = str(db_path)
    os.environ["PRM_USE_SQLITE"] = "0"
    application = QApplication.instance() or QApplication([])
    ensure_application_font()
    config = AppConfig(PROJECT_ROOT, PROJECT_ROOT)
    paths: list[Path] = []

    context = _license_context(temp_dir)
    login = LoginDialog(config, context, SimpleNamespace(db_path=db_path))
    login.show()
    login.resize(max(login.width(), 760), max(login.height(), 700))
    _settle(application)
    login_path = output / "v1_login_version.png"
    if not login.grab().save(str(login_path)):
        raise RuntimeError("Could not capture V1.0 login evidence")
    paths.append(login_path)
    login.close()

    window = MainWindow(config, start_page="dashboard", license_context=context, session={"role": "admin"})
    window.resize(1366, 768)
    window.show()
    _settle(application)
    if window.windowTitle() != RELEASE_NAME:
        raise RuntimeError(f"Unexpected V1.0 window title: {window.windowTitle()}")
    if window.product_brand.version_label.text() != DISPLAY_VERSION:
        raise RuntimeError("The fixed product header is missing V1.0")
    dashboard_path = output / "v1_dashboard_1366x768.png"
    if not window.grab().save(str(dashboard_path)):
        raise RuntimeError("Could not capture V1.0 dashboard evidence")
    paths.append(dashboard_path)
    top_bar = window.findChild(QFrame, "topBar")
    header_path = output / "v1_product_version_header.png"
    if top_bar is None or not top_bar.grab().save(str(header_path)):
        raise RuntimeError("Could not capture V1.0 product-header evidence")
    paths.append(header_path)

    for page in window.pages.values():
        source = getattr(page, "source", None)
        closer = getattr(source, "close_database_resources", None)
        if callable(closer):
            closer()
    window.close()
    application.processEvents()
    gc.collect()
    return paths


def _capture_pdfs(output: Path, db_path: Path) -> list[Path]:
    company = dict(SYNTHETIC_COMPANY)
    invoice = output / "v1_sales_invoice_sample.pdf"
    write_transaction_pdf(
        invoice,
        "Tax Invoice",
        company,
        {
            "bill_no": "V1-VALIDATION-001",
            "bill_date": "2026-07-12",
            "customer_name": "Synthetic Validation Customer",
            "gstin": "29ABCDE1234F1Z5",
            "phone": "9000000001",
            "billing_address": "Bengaluru, Karnataka",
            "pay_mode": "Credit",
        },
        [
            {
                "item_name": "Synthetic Validation Product",
                "hsn": "2106",
                "qty": 2,
                "unit": "PCS",
                "rate": 100,
                "gst_rate": 18,
                "taxable": 200,
                "cgst": 0,
                "sgst": 0,
                "igst": 36,
                "amount": 236,
            }
        ],
        {
            "total_qty": 2,
            "taxable": 200,
            "cgst": 0,
            "sgst": 0,
            "igst": 36,
            "total_tax": 36,
            "grand_total": 236,
        },
        document_type="sales_invoice",
        party_label="Bill To",
        db_path=db_path,
    )

    profit_loss = output / "v1_profit_loss_sample.pdf"
    write_statement_pdf(
        profit_loss,
        "Profit & Loss",
        company,
        {
            "period": "01-04-2026 to 12-07-2026",
            "left_title": "Particulars",
            "right_title": "Particulars",
            "left_groups": [
                {"label": "Opening Stock", "amount": 10000},
                {"label": "Purchases", "amount": 25000},
                {"label": "Indirect Expenses", "amount": 5000},
            ],
            "right_groups": [
                {"label": "Sales", "amount": 50000},
                {"label": "Closing Stock", "amount": 12000},
            ],
            "left_total": 40000,
            "right_total": 62000,
            "difference_label": "Net Profit",
            "difference": 22000,
        },
        db_path=db_path,
    )
    return [invoice, profit_loss]


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture client-safe V1.0 release validation evidence.")
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "release_validation" / "2026-07-12_v1.0",
    )
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="prm-v1-release-") as temp:
        temp_dir = Path(temp)
        db_path = temp_dir / "release_validation.db"
        _prepare_database(db_path)
        artifacts = _capture_ui(output, db_path, temp_dir)
        artifacts.extend(_capture_pdfs(output, db_path))
    result = {
        "release": RELEASE_NAME,
        "technical_version": PRODUCT_VERSION,
        "display_version": DISPLAY_VERSION,
        "data_classification": "synthetic-only",
        "artifacts": [str(path) for path in artifacts],
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
