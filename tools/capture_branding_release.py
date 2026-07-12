from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QFrame

from config.app_config import AppConfig
from services.company_profile_service import CompanyProfileService
from services.mysql_source import MySqlSource
from services.pdf_print import write_statement_pdf, write_transaction_pdf
from views.main_window import MainWindow


STAMP = "20260712"


def _settle(application: QApplication) -> None:
    # Page changes rebuild several responsive cards asynchronously. Force the
    # off-screen backing store through multiple complete paint cycles so the
    # captured evidence never contains first-paint black/transparent regions.
    for _ in range(8):
        QApplication.sendPostedEvents()
        for widget in application.topLevelWidgets():
            widget.update()
            widget.repaint()
        application.processEvents()
        QTest.qWait(250)


def main() -> int:
    output = PROJECT_ROOT / "screenshots"
    output.mkdir(parents=True, exist_ok=True)
    source_db = PROJECT_ROOT / "database" / "prm_billing_inventory.db"
    with tempfile.TemporaryDirectory(prefix="prm-branding-capture-", ignore_cleanup_errors=True) as temp_dir:
        capture_db = Path(temp_dir) / "capture.db"
        shutil.copy2(source_db, capture_db)
        os.environ["PRM_SQLITE_DB"] = str(capture_db)
        os.environ["PRM_USE_SQLITE"] = "0"
        return _capture(output)


def _capture(output: Path) -> int:
    config = AppConfig(PROJECT_ROOT, PROJECT_ROOT)
    application = QApplication([])
    window = MainWindow(config)
    window.show()

    for width, height in ((1366, 768), (1440, 900), (1920, 1080)):
        window.resize(width, height)
        window.open_page("dashboard", remember=False)
        _settle(application)
        window.grab().save(str(output / f"branding_after_dashboard_{width}x{height}_{STAMP}.png"))

    window.resize(1366, 768)
    window.open_page("dashboard", remember=False)
    _settle(application)
    top_bar = window.findChild(QFrame, "topBar")
    top_bar.grab().save(str(output / f"branding_after_main_product_header_1366x768_{STAMP}.png"))
    window.pages["dashboard"].cards["company"].grab().save(
        str(output / f"branding_after_client_company_card_1366x768_{STAMP}.png")
    )

    window.open_page("company_settings", remember=False)
    _settle(application)
    window.grab().save(str(output / f"branding_after_company_profile_1366x768_{STAMP}.png"))

    window.open_page("reports:daily_dispatch_summary", remember=False)
    _settle(application)
    window.grab().save(str(output / f"branding_after_dispatch_summary_1366x768_{STAMP}.png"))

    source = MySqlSource()
    company = CompanyProfileService(source.sqlite_path).current_profile()
    invoice_pdf = output / f"branding_after_sales_invoice_preview_{STAMP}.pdf"
    write_transaction_pdf(
        invoice_pdf,
        "Tax Invoice",
        company,
        {
            "bill_no": "BRAND-QA-001",
            "bill_date": "2026-07-12",
            "customer_name": "Branding QA Customer",
            "gstin": "36ABCDE1234F1Z5",
            "phone": "9000000000",
            "billing_address": "Hyderabad, Telangana",
            "pay_mode": "Credit",
        },
        [
            {
                "item_name": "Branding Validation Product",
                "hsn": "2106",
                "qty": 2,
                "unit": "PCS",
                "rate": 100,
                "gst_rate": 18,
                "taxable": 200,
                "cgst": 18,
                "sgst": 18,
                "igst": 0,
                "amount": 236,
            }
        ],
        {
            "total_qty": 2,
            "taxable": 200,
            "cgst": 18,
            "sgst": 18,
            "igst": 0,
            "total_tax": 36,
            "grand_total": 236,
        },
        document_type="sales_invoice",
        party_label="Bill To",
        db_path=source.sqlite_path,
    )
    profit_pdf = output / f"branding_after_profit_loss_preview_{STAMP}.pdf"
    write_statement_pdf(
        profit_pdf,
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
                {"label": "Sales", "amount": 52000},
                {"label": "Closing Stock", "amount": 8000},
                {"label": "Net Profit", "amount": 20000},
            ],
            "left_total": 40000,
            "right_total": 80000,
        },
        db_path=source.sqlite_path,
    )

    window.close()
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
