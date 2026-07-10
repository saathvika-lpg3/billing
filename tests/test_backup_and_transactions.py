from __future__ import annotations

import os
import shutil
import sqlite3
from pathlib import Path

import pytest

from config.app_config import AppConfig
from services.backup_service import BackupService
from services.gst_payload_service import GstPayloadService
from services.import_service import ImportService
from services.mysql_source import MySqlSource
from services.order_conversion_service import OrderConversionService
from services.pdf_print import write_report_pdf
from services.sales_calculator import SalesCalculator, SalesLine
from services.transaction_repository import TransactionRepository


SOURCE_DB = Path(r"D:\PRM_GST_DESKTOP\database\prm_billing_inventory.db")


def copy_db(tmp_path: Path) -> Path:
    target = tmp_path / "prm_billing_inventory.db"
    shutil.copy2(SOURCE_DB, target)
    return target


def test_backup_service_creates_plain_and_encrypted_backups(tmp_path: Path) -> None:
    db_path = copy_db(tmp_path)
    config = AppConfig(project_root=tmp_path, source_root=Path(r"D:\PRM_GST_DESKTOP"))
    service = BackupService(config, db_path=db_path)

    plain = service.create_backup(tag="test")
    encrypted = service.create_backup(password="secret1", tag="test")

    assert plain.exists()
    assert plain.suffix == ".json"
    assert encrypted.exists()
    assert encrypted.suffix == ".pgst"
    payload = service._read_payload(encrypted, "secret1")
    assert payload["format"] == "PRM_BILLING_INVENTORY_BACKUP"
    assert "sales" in payload["tables"]


def test_sales_transaction_posts_bill_stock_gst_and_ledger(tmp_path: Path) -> None:
    db_path = copy_db(tmp_path)
    repository = TransactionRepository(db_path=db_path)
    line = SalesLine(
        item_name="Test Item",
        pack_name="1 PCS",
        hsn="1905",
        unit="PCS",
        qty=2,
        free_qty=0,
        mrp=25,
        rate=20,
        scheme=0,
        discount_amount=0,
        gst_rate=18,
    )
    computed = SalesCalculator("Tamil Nadu").compute_line(line)
    totals = SalesCalculator("Tamil Nadu").totals([computed])
    header = {
        "bill_no": "TEST-POST-001",
        "bill_date": "2026-07-02",
        "customer_id": 0,
        "customer_name": "Test Customer",
        "customer_area": "",
        "payment": "Cash",
        "party_type": "customer",
        "party_id": 0,
        "party_name": "Test Customer",
        "price_level": "Retail",
        "employee": "Admin",
        "warehouse_id": 0,
        "branch": "Main",
        "cost_center": "",
        "shipping": "",
        "po_no": "",
        "transport": "",
        "credit_terms": "",
    }

    sale_id = repository.save_sales(header, [computed], totals)

    with sqlite3.connect(db_path) as conn:
        sale_count = conn.execute("SELECT COUNT(*) FROM sales WHERE id=?", (sale_id,)).fetchone()[0]
        item_count = conn.execute("SELECT COUNT(*) FROM sales_items WHERE sale_id=?", (sale_id,)).fetchone()[0]
        gst_count = conn.execute("SELECT COUNT(*) FROM gst_postings WHERE source_table='sales' AND source_id=?", (sale_id,)).fetchone()[0]
        ledger_count = conn.execute("SELECT COUNT(*) FROM ledger_postings WHERE source_table='sales' AND source_id=?", (sale_id,)).fetchone()[0]

    assert sale_count == 1
    assert item_count == 1
    assert gst_count == 1
    assert ledger_count == 3


def test_sales_calculator_uses_billable_quantity_after_free_qty() -> None:
    line = SalesLine(
        item_name="Scheme Item",
        pack_name="1 PCS",
        hsn="1905",
        unit="PCS",
        qty=10,
        free_qty=2,
        mrp=100,
        rate=100,
        scheme=0,
        discount_amount=0,
        gst_rate=18,
    )

    computed = SalesCalculator("Tamil Nadu").compute_line(line)

    assert computed.taxable == 800
    assert computed.gst_total == 144
    assert computed.line_total == 944


def test_order_document_and_sales_return_save_to_expected_tables(tmp_path: Path) -> None:
    db_path = copy_db(tmp_path)
    repository = TransactionRepository(db_path=db_path)
    line = SalesLine(
        item_name="Return Item",
        pack_name="1 PCS",
        hsn="1905",
        unit="PCS",
        qty=1,
        free_qty=0,
        mrp=50,
        rate=40,
        scheme=0,
        discount_amount=0,
        gst_rate=5,
    )
    computed = SalesCalculator("Tamil Nadu").compute_line(line)
    totals = SalesCalculator("Tamil Nadu").totals([computed])
    order_header = {
        "doc_no": "Q-TEST-001",
        "doc_date": "2026-07-02",
        "doc_type": "quotation",
        "party_type": "customer",
        "party_id": 0,
        "party_name": "Test Customer",
        "area": "",
        "warehouse_id": 0,
        "payment": "Credit",
        "valid_until": "2026-07-09",
        "delivery_date": "2026-07-09",
        "status": "Open",
        "notes": "",
        "price_level": "Retail",
        "employee": "Admin",
    }
    return_header = order_header | {"doc_no": "SR-TEST-001", "doc_type": "sales_return"}

    order_id = repository.save_order_document(order_header, [computed], totals)
    return_id = repository.save_sales_return(return_header, [computed], totals)

    with sqlite3.connect(db_path) as conn:
        order_count = conn.execute("SELECT COUNT(*) FROM order_document_items WHERE order_document_id=?", (order_id,)).fetchone()[0]
        return_count = conn.execute("SELECT COUNT(*) FROM sales_return_items WHERE return_id=?", (return_id,)).fetchone()[0]
        return_ledger = conn.execute("SELECT COUNT(*) FROM ledger_postings WHERE source_table='sales_returns' AND source_id=?", (return_id,)).fetchone()[0]

    assert order_count == 1
    assert return_count == 1
    assert return_ledger == 3


def test_sales_and_purchase_return_stock_uses_return_qty_not_free_qty(tmp_path: Path) -> None:
    db_path = copy_db(tmp_path)
    repository = TransactionRepository(db_path=db_path)
    calculator = SalesCalculator("Tamil Nadu")
    line = SalesLine(
        item_name="Free Return Item",
        pack_name="1 PCS",
        hsn="1905",
        unit="PCS",
        qty=3,
        free_qty=1,
        mrp=100,
        rate=100,
        scheme=0,
        discount_amount=0,
        gst_rate=18,
    )
    computed = calculator.compute_line(line)
    totals = calculator.totals([computed])
    sales_header = {
        "doc_no": "RET-FREE-STOCK-001",
        "doc_date": "2026-07-02",
        "party_type": "customer",
        "party_id": 0,
        "party_name": "Free Customer",
        "warehouse_id": 0,
        "payment": "Credit",
        "status": "Active",
        "notes": "Free quantity stock check",
        "branch": "Main",
        "cost_center": "",
    }
    purchase_header = sales_header | {
        "doc_no": "DNT-FREE-STOCK-001",
        "party_type": "supplier",
        "party_name": "Free Supplier",
    }

    sales_return_id = repository.save_sales_return(sales_header, [computed], totals)
    purchase_return_id = repository.save_purchase_return(purchase_header, [computed], totals)

    with sqlite3.connect(db_path) as conn:
        sale_stock = conn.execute("SELECT qty_in FROM stock_log WHERE ref_no='RET-FREE-STOCK-001'").fetchone()[0]
        purchase_stock = conn.execute("SELECT qty_out FROM stock_log WHERE ref_no='DNT-FREE-STOCK-001'").fetchone()[0]
        stock_qty = conn.execute("SELECT stock_qty FROM sales_return_items WHERE return_id=?", (sales_return_id,)).fetchone()[0]
        purchase_item_qty = conn.execute("SELECT qty,free_qty FROM purchase_return_items WHERE return_id=?", (purchase_return_id,)).fetchone()

    assert sale_stock == 3
    assert stock_qty == 3
    assert purchase_stock == 3
    assert purchase_item_qty == (3, 1)


def test_sales_return_loads_original_bill_and_rejects_over_return(tmp_path: Path) -> None:
    db_path = copy_db(tmp_path)
    repository = TransactionRepository(db_path=db_path)
    calculator = SalesCalculator("Tamil Nadu")
    source_line = SalesLine(
        item_name="Original Sale Item",
        pack_name="1 PCS",
        hsn="1905",
        unit="PCS",
        qty=2,
        free_qty=0,
        mrp=50,
        rate=40,
        scheme=0,
        discount_amount=0,
        gst_rate=5,
    )
    computed = calculator.compute_line(source_line)
    totals = calculator.totals([computed])
    header = {
        "bill_no": "SRC-SALE-001",
        "bill_date": "2026-07-02",
        "customer_id": 0,
        "customer_name": "Source Customer",
        "customer_area": "",
        "payment": "Credit",
        "party_type": "customer",
        "party_id": 0,
        "party_name": "Source Customer",
        "price_level": "Retail",
        "employee": "Admin",
        "warehouse_id": 0,
        "branch": "Main",
        "cost_center": "",
        "shipping": "",
        "po_no": "",
        "transport": "",
        "credit_terms": "",
    }
    sale_id = repository.save_sales(header, [computed], totals)

    old_db = os.environ.get("PRM_SQLITE_DB")
    os.environ["PRM_SQLITE_DB"] = str(db_path)
    try:
        source = MySqlSource()
        rows = source.sales_return_source_lines(sale_id)
    finally:
        if old_db is None:
            os.environ.pop("PRM_SQLITE_DB", None)
        else:
            os.environ["PRM_SQLITE_DB"] = old_db
    assert rows
    row = rows[0]
    assert row["remaining_qty"] == 2
    return_line = SalesLine(
        item_name=row["item_name"],
        pack_name=row["pack_name"],
        hsn=row["hsn"],
        unit=row["unit"],
        qty=1,
        free_qty=0,
        mrp=row["mrp"],
        rate=row["rate"],
        scheme=0,
        discount_amount=row["discount"] or 0,
        gst_rate=row["gst"],
        source_item_id=row["source_item_id"],
        source_doc_id=sale_id,
        source_doc_no=row["source_doc_no"],
        max_qty=row["remaining_qty"],
    )
    return_computed = calculator.compute_line(return_line)
    return_totals = calculator.totals([return_computed])
    return_header = {
        "doc_no": "RET-SRC-001",
        "doc_date": "2026-07-02",
        "source_doc_id": sale_id,
        "sale_id": sale_id,
        "party_type": "customer",
        "party_id": 0,
        "party_name": "Source Customer",
        "warehouse_id": 0,
        "payment": "Credit",
        "status": "Active",
        "notes": "Test source return",
        "branch": "Main",
        "cost_center": "",
    }

    return_id = repository.save_sales_return(return_header, [return_computed], return_totals)

    over_line = SalesLine(
        item_name=row["item_name"],
        pack_name=row["pack_name"],
        hsn=row["hsn"],
        unit=row["unit"],
        qty=2,
        free_qty=0,
        mrp=row["mrp"],
        rate=row["rate"],
        scheme=0,
        discount_amount=0,
        gst_rate=row["gst"],
        source_item_id=row["source_item_id"],
        source_doc_id=sale_id,
        source_doc_no=row["source_doc_no"],
        max_qty=1,
    )
    over_computed = calculator.compute_line(over_line)
    with pytest.raises(ValueError):
        repository.save_sales_return(return_header | {"doc_no": "RET-SRC-002"}, [over_computed], calculator.totals([over_computed]))

    with sqlite3.connect(db_path) as conn:
        saved = conn.execute("SELECT sale_id FROM sales_returns WHERE id=?", (return_id,)).fetchone()[0]
        saved_item = conn.execute("SELECT sale_item_id FROM sales_return_items WHERE return_id=?", (return_id,)).fetchone()[0]

    assert saved == sale_id
    assert saved_item == row["source_item_id"]


def test_dispatch_return_from_sales_creates_credit_note_with_accepted_stock(tmp_path: Path) -> None:
    db_path = copy_db(tmp_path)
    repository = TransactionRepository(db_path=db_path)
    calculator = SalesCalculator("Tamil Nadu")
    source_line = SalesLine(
        item_name="Dispatch Source Item",
        pack_name="1 PCS",
        hsn="1905",
        unit="PCS",
        qty=5,
        free_qty=1,
        mrp=100,
        rate=100,
        scheme=0,
        discount_amount=0,
        gst_rate=18,
    )
    computed = calculator.compute_line(source_line)
    sale_id = repository.save_sales(
        {
            "bill_no": "DISP-SALE-001",
            "bill_date": "2026-07-02",
            "customer_id": 0,
            "customer_name": "Dispatch Customer",
            "customer_area": "Route A",
            "payment": "Credit",
            "party_type": "customer",
            "party_id": 0,
            "party_name": "Dispatch Customer",
            "price_level": "Retail",
            "employee": "Admin",
            "warehouse_id": 0,
            "branch": "Main",
            "cost_center": "",
            "shipping": "",
            "po_no": "",
            "transport": "Vehicle 1",
            "credit_terms": "",
        },
        [computed],
        calculator.totals([computed]),
    )
    with sqlite3.connect(db_path) as conn:
        sale_item_id = conn.execute("SELECT id FROM sales_items WHERE sale_id=?", (sale_id,)).fetchone()[0]

    dispatch_return_id = repository.save_dispatch_return(
        {
            "return_no": "DRTN-TEST-001",
            "return_date": "2026-07-03",
            "source_table": "sales",
            "source_id": sale_id,
            "reason": "Returned from route",
            "notes": "One damaged",
        },
        [{"source_item_id": sale_item_id, "return_qty": 3, "return_free_qty": 1, "damaged_qty": 1, "remarks": "Box damaged"}],
    )

    with sqlite3.connect(db_path) as conn:
        dispatch_row = conn.execute(
            "SELECT sale_return_id,total_returned_qty,total_accepted_qty,damaged_qty,dispatch_status_after FROM dispatch_returns WHERE id=?",
            (dispatch_return_id,),
        ).fetchone()
        return_item = conn.execute(
            "SELECT qty,free_qty,stock_qty,taxable FROM sales_return_items WHERE return_id=?",
            (dispatch_row[0],),
        ).fetchone()
        stock_log = conn.execute("SELECT qty_in FROM stock_log WHERE kind='sales_return' AND ref_no=(SELECT return_no FROM sales_returns WHERE id=?)", (dispatch_row[0],)).fetchone()[0]
        sale_status = conn.execute("SELECT dispatch_status FROM sales WHERE id=?", (sale_id,)).fetchone()[0]

    assert dispatch_row == (dispatch_row[0], 3, 2, 1, "Partially Returned")
    assert return_item == (3, 1, 2, 200)
    assert stock_log == 2
    assert sale_status == "Partially Returned"


def test_purchase_return_loads_original_purchase_and_rejects_over_return(tmp_path: Path) -> None:
    db_path = copy_db(tmp_path)
    repository = TransactionRepository(db_path=db_path)
    calculator = SalesCalculator("Tamil Nadu")
    purchase_line = SalesLine(
        item_name="Original Purchase Item",
        pack_name="1 PCS",
        hsn="1905",
        unit="PCS",
        qty=3,
        free_qty=0,
        mrp=75,
        rate=60,
        scheme=0,
        discount_amount=0,
        gst_rate=18,
    )
    computed = calculator.compute_line(purchase_line)
    totals = calculator.totals([computed])
    purchase_id = repository.save_purchase(
        {
            "bill_no": "SRC-PUR-001",
            "bill_date": "2026-07-02",
            "supplier_id": 0,
            "supplier_name": "Source Supplier",
            "payment": "Credit",
            "party_type": "supplier",
            "party_id": 0,
            "party_name": "Source Supplier",
            "price_level": "Purchase",
            "employee": "Admin",
            "warehouse_id": 0,
            "branch": "Main",
            "cost_center": "",
        },
        [computed],
        totals,
    )

    old_db = os.environ.get("PRM_SQLITE_DB")
    os.environ["PRM_SQLITE_DB"] = str(db_path)
    try:
        source = MySqlSource()
        rows = source.purchase_return_source_lines(purchase_id)
    finally:
        if old_db is None:
            os.environ.pop("PRM_SQLITE_DB", None)
        else:
            os.environ["PRM_SQLITE_DB"] = old_db
    assert rows
    row = rows[0]
    return_line = SalesLine(
        item_name=row["item_name"],
        pack_name=row["pack_name"],
        hsn=row["hsn"],
        unit=row["unit"],
        qty=1,
        free_qty=0,
        mrp=row["mrp"],
        rate=row["rate"],
        scheme=0,
        discount_amount=0,
        gst_rate=row["gst"],
        source_item_id=row["source_item_id"],
        source_doc_id=purchase_id,
        source_doc_no=row["source_doc_no"],
        max_qty=row["remaining_qty"],
    )
    return_computed = calculator.compute_line(return_line)
    return_header = {
        "doc_no": "DNT-SRC-001",
        "doc_date": "2026-07-02",
        "source_doc_id": purchase_id,
        "purchase_id": purchase_id,
        "party_type": "supplier",
        "party_id": 0,
        "party_name": "Source Supplier",
        "warehouse_id": 0,
        "payment": "Credit",
        "status": "Active",
        "notes": "Test source purchase return",
        "branch": "Main",
        "cost_center": "",
    }

    return_id = repository.save_purchase_return(return_header, [return_computed], calculator.totals([return_computed]))

    over_line = SalesLine(
        item_name=row["item_name"],
        pack_name=row["pack_name"],
        hsn=row["hsn"],
        unit=row["unit"],
        qty=3,
        free_qty=0,
        mrp=row["mrp"],
        rate=row["rate"],
        scheme=0,
        discount_amount=0,
        gst_rate=row["gst"],
        source_item_id=row["source_item_id"],
        source_doc_id=purchase_id,
        source_doc_no=row["source_doc_no"],
        max_qty=2,
    )
    over_computed = calculator.compute_line(over_line)
    with pytest.raises(ValueError):
        repository.save_purchase_return(return_header | {"doc_no": "DNT-SRC-002"}, [over_computed], calculator.totals([over_computed]))

    with sqlite3.connect(db_path) as conn:
        saved = conn.execute("SELECT purchase_id FROM purchase_returns WHERE id=?", (return_id,)).fetchone()[0]
        saved_item = conn.execute("SELECT purchase_item_id FROM purchase_return_items WHERE return_id=?", (return_id,)).fetchone()[0]

    assert saved == purchase_id
    assert saved_item == row["source_item_id"]


def test_order_conversion_service_converts_sales_and_purchase_orders(tmp_path: Path) -> None:
    db_path = copy_db(tmp_path)
    repository = TransactionRepository(db_path=db_path)
    service = OrderConversionService(db_path=db_path)
    calculator = SalesCalculator("Tamil Nadu")
    line = SalesLine(
        item_name="Convert Item",
        pack_name="1 PCS",
        hsn="1905",
        unit="PCS",
        qty=1,
        free_qty=0,
        mrp=100,
        rate=80,
        scheme=0,
        discount_amount=0,
        gst_rate=18,
    )
    computed = calculator.compute_line(line)
    totals = calculator.totals([computed])

    def save_flow_doc(
        doc_no: str,
        doc_type: str,
        *,
        party_type: str = "customer",
        party_name: str = "Convert Customer",
        status: str = "Open",
        price_level: str = "Retail",
    ) -> int:
        return repository.save_order_document(
            {
                "doc_no": doc_no,
                "doc_date": "2026-07-02",
                "doc_type": doc_type,
                "party_type": party_type,
                "party_id": 0,
                "party_name": party_name,
                "area": "",
                "warehouse_id": 0,
                "payment": "Credit",
                "valid_until": "2026-07-09",
                "delivery_date": "2026-07-09",
                "status": status,
                "notes": "",
                "price_level": price_level,
                "employee": "Admin",
            },
            [computed],
            totals,
        )

    quotation_id = save_flow_doc("QT-CONV-001", "quotation")
    sales_order_id = save_flow_doc("SO-CONV-001", "sales_order")
    purchase_order_id = save_flow_doc(
        "PO-CONV-001",
        "purchase_order",
        party_type="supplier",
        party_name="Convert Supplier",
        price_level="Purchase",
    )
    delivery_challan_id = save_flow_doc("DC-FLOW-001", "delivery_challan")
    closed_order_id = save_flow_doc("SO-CLOSED-001", "sales_order", status="Closed")

    candidates = service.candidates(50)
    candidate_ids = {int(row["id"]) for row in candidates}
    assert quotation_id in candidate_ids
    assert sales_order_id in candidate_ids
    assert purchase_order_id in candidate_ids
    assert delivery_challan_id not in candidate_ids
    assert closed_order_id not in candidate_ids
    assert next(row for row in candidates if int(row["id"]) == quotation_id)["next_action"] == "Make Sales Bill"
    assert next(row for row in candidates if int(row["id"]) == purchase_order_id)["next_action"] == "Make Purchase"

    service.set_status(quotation_id, "Accepted")
    with pytest.raises(ValueError, match="Only quotation or sales order"):
        service.convert_to_sales(delivery_challan_id, "BAD-DC-CONV")

    sales_result = service.convert_to_sales(sales_order_id, "SALE-CONV-001")
    purchase_result = service.convert_to_purchase(purchase_order_id, "PUR-CONV-001")

    with sqlite3.connect(db_path) as conn:
        sale_count = conn.execute("SELECT COUNT(*) FROM sales WHERE id=? AND bill_no='SALE-CONV-001'", (sales_result["id"],)).fetchone()[0]
        purchase_count = conn.execute("SELECT COUNT(*) FROM purchases WHERE id=? AND bill_no='PUR-CONV-001'", (purchase_result["id"],)).fetchone()[0]
        converted_count = conn.execute("SELECT COUNT(*) FROM order_documents WHERE status='Converted' AND converted_ref IN ('SALE-CONV-001','PUR-CONV-001')").fetchone()[0]
        quotation_status = conn.execute("SELECT status FROM order_documents WHERE id=?", (quotation_id,)).fetchone()[0]

    assert sale_count == 1
    assert purchase_count == 1
    assert converted_count == 2
    assert quotation_status == "Accepted"


def test_receipt_entry_posts_receipt_voucher_and_ledger(tmp_path: Path) -> None:
    db_path = copy_db(tmp_path)
    repository = TransactionRepository(db_path=db_path)
    entry = {
        "doc_no": "RCPT-TEST-001",
        "entry_date": "2026-07-02",
        "party_id": 0,
        "party_name": "Test Customer",
        "party_type": "customer",
        "amount": 125.0,
        "mode": "Cash",
        "branch": "Main",
        "cost_center": "",
        "status": "Active",
        "notes": "Test receipt",
    }

    receipt_id = repository.save_account_entry("receipt", entry)

    with sqlite3.connect(db_path) as conn:
        receipt_count = conn.execute("SELECT COUNT(*) FROM receipts WHERE id=?", (receipt_id,)).fetchone()[0]
        voucher_count = conn.execute("SELECT COUNT(*) FROM voucher_headers WHERE source_table='receipts' AND source_id=?", (receipt_id,)).fetchone()[0]
        ledger_count = conn.execute("SELECT COUNT(*) FROM ledger_postings WHERE source_table='receipts' AND source_id=?", (receipt_id,)).fetchone()[0]

    assert receipt_count == 1
    assert voucher_count == 1
    assert ledger_count == 2


def test_payment_entry_posts_payment_voucher_and_ledger(tmp_path: Path) -> None:
    db_path = copy_db(tmp_path)
    repository = TransactionRepository(db_path=db_path)
    entry = {
        "doc_no": "PAY-TEST-001",
        "entry_date": "2026-07-02",
        "party_id": 0,
        "party_name": "Test Supplier",
        "party_type": "supplier",
        "amount": 225.0,
        "mode": "Bank",
        "branch": "Main",
        "cost_center": "",
        "status": "Active",
        "notes": "Test payment",
    }

    payment_id = repository.save_account_entry("payment", entry)

    with sqlite3.connect(db_path) as conn:
        payment_count = conn.execute("SELECT COUNT(*) FROM payments WHERE id=?", (payment_id,)).fetchone()[0]
        voucher_count = conn.execute("SELECT COUNT(*) FROM voucher_headers WHERE source_table='payments' AND source_id=?", (payment_id,)).fetchone()[0]
        ledger_count = conn.execute("SELECT COUNT(*) FROM ledger_postings WHERE source_table='payments' AND source_id=?", (payment_id,)).fetchone()[0]

    assert payment_count == 1
    assert voucher_count == 1
    assert ledger_count == 2


def test_inventory_stock_entry_creates_stock_log(tmp_path: Path) -> None:
    db_path = copy_db(tmp_path)
    repository = TransactionRepository(db_path=db_path)
    header = {
        "doc_no": "STK-TEST-001",
        "doc_date": "2026-07-02",
        "from_warehouse_id": 0,
        "status": "Active",
        "notes": "",
    }
    rows = [
        {
            "item_id": 0,
            "pack_id": 0,
            "item_name": "Stock Test",
            "pack_name": "1 PCS",
            "pack_size": 1,
            "hsn": "1905",
            "unit": "PCS",
            "mrp": 0,
            "current": 0,
            "qty": 3,
            "difference": 3,
            "reason": "Opening",
        }
    ]

    repository.save_inventory_entry("stock_entry", header, rows)

    with sqlite3.connect(db_path) as conn:
        stock_count = conn.execute("SELECT COUNT(*) FROM stock_log WHERE ref_no='STK-TEST-001' AND kind='stock_entry'").fetchone()[0]

    assert stock_count == 1


def test_import_service_posts_products_and_customers_with_updates(tmp_path: Path) -> None:
    db_path = copy_db(tmp_path)
    service = ImportService(db_path=db_path)

    products = [
        {"code": "IMP-001", "name": "Imported Product", "unit": "PCS", "gst": "18", "mrp": "10", "stock": "5"},
        {"code": "IMP-001", "name": "Imported Product", "unit": "PCS", "gst": "18", "mrp": "12", "stock": "7"},
    ]
    customers = [
        {"name": "Imported Customer", "phone": "9000000000", "area": "Test", "balance": "25"},
    ]

    product_result = service.post_rows("Products", products)
    customer_result = service.post_rows("Customers", customers)

    with sqlite3.connect(db_path) as conn:
        product = conn.execute("SELECT mrp,stock FROM items WHERE code='IMP-001'").fetchone()
        customer_count = conn.execute("SELECT COUNT(*) FROM customers WHERE phone='9000000000'").fetchone()[0]

    assert product_result["inserted"] == 1
    assert product_result["updated"] == 1
    assert customer_result["inserted"] == 1
    assert product == (12, 7)
    assert customer_count == 1


def test_report_pdf_export_creates_readable_file(tmp_path: Path) -> None:
    output = tmp_path / "sales_report.pdf"

    write_report_pdf(
        output,
        "Sales List",
        {"business_name": "PRM Test Company", "gstin": "33ABCDE1234F1Z5"},
        [
            {"bill_no": "TEST-001", "bill_date": "2026-07-02", "customer_name": "Test Customer", "grand_total": 236.0},
            {"bill_no": "TEST-002", "bill_date": "2026-07-02", "customer_name": "Second Customer", "grand_total": 118.0},
        ],
        {"From": "2026-07-01", "To": "2026-07-02"},
    )

    assert output.exists()
    assert output.stat().st_size > 1000


def test_gst_payload_service_prepares_einvoice_and_eway_json(tmp_path: Path) -> None:
    db_path = copy_db(tmp_path)
    repository = TransactionRepository(db_path=db_path)
    line = SalesLine(
        item_name="GST Payload Item",
        pack_name="1 PCS",
        hsn="1905",
        unit="PCS",
        qty=1,
        free_qty=0,
        mrp=118,
        rate=100,
        scheme=0,
        discount_amount=0,
        gst_rate=18,
    )
    computed = SalesCalculator("Tamil Nadu").compute_line(line)
    totals = SalesCalculator("Tamil Nadu").totals([computed])
    sale_id = repository.save_sales(
        {
            "bill_no": "GST-PREP-001",
            "bill_date": "2099-01-01",
            "customer_id": 0,
            "customer_name": "GST Draft Customer",
            "customer_area": "",
            "payment": "Credit",
            "party_type": "customer",
            "party_id": 0,
            "party_name": "GST Draft Customer",
            "price_level": "Retail",
            "employee": "Admin",
            "warehouse_id": 0,
            "branch": "Main",
            "cost_center": "",
            "shipping": "",
            "po_no": "",
            "transport": "Local Transport",
            "credit_terms": "",
        },
        [computed],
        totals,
    )
    service = GstPayloadService(db_path)
    output_dir = tmp_path / "gst_payloads"

    einvoice_result = service.prepare_pending("einvoice", output_dir, limit=100)
    eway_result = service.prepare_pending("eway_bill", output_dir, limit=100)

    with sqlite3.connect(db_path) as conn:
        einvoice_count = conn.execute("SELECT COUNT(*) FROM einvoices WHERE sale_id=? AND status='Prepared'", (sale_id,)).fetchone()[0]
        eway_count = conn.execute("SELECT COUNT(*) FROM eway_bills WHERE sale_id=? AND status='Prepared'", (sale_id,)).fetchone()[0]

    assert einvoice_result["prepared"] >= 1
    assert eway_result["prepared"] >= 1
    assert (output_dir / "einvoice_{}_GST-PREP-001.json".format(sale_id)).exists()
    assert (output_dir / "eway_bill_{}_GST-PREP-001.json".format(sale_id)).exists()
    assert einvoice_count == 1
    assert eway_count == 1
