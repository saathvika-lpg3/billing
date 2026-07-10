from __future__ import annotations

import shutil
import sqlite3
import os
from pathlib import Path

import pytest

from services.sales_calculator import SalesCalculator, SalesLine
from services.mysql_source import MySqlSource
from services.transaction_repository import TransactionRepository


SOURCE_DB = Path(r"D:\PRM_GST_DESKTOP\database\prm_billing_inventory.db")


def copy_db(tmp_path: Path) -> Path:
    target = tmp_path / "business_flow.db"
    shutil.copy2(SOURCE_DB, target)
    return target


def add_customer_and_item(db_path: Path, *, stock: float = 20) -> tuple[int, int]:
    with sqlite3.connect(db_path) as conn:
        customer_id = int(
            conn.execute(
                "INSERT INTO customers(name,balance,status) VALUES('Lifecycle Customer',0,'Active')"
            ).lastrowid
        )
        item_id = int(
            conn.execute(
                "INSERT INTO items(code,name,unit,gst,stock,standard_cost,status) VALUES('LIFE-ITEM','Lifecycle Item','PCS',5,?,?, 'Active')",
                (stock, 12.5),
            ).lastrowid
        )
    return customer_id, item_id


def add_supplier_item_and_warehouse(
    db_path: Path,
    *,
    stock: float = 5,
) -> tuple[int, int, int]:
    with sqlite3.connect(db_path) as conn:
        supplier_id = int(
            conn.execute(
                "INSERT INTO suppliers(name,balance,status) VALUES('Lifecycle Supplier',0,'Active')"
            ).lastrowid
        )
        item_id = int(
            conn.execute(
                "INSERT INTO items(code,name,unit,gst,stock,standard_cost,status) VALUES('LIFE-PUR-ITEM','Lifecycle Purchase Item','PCS',18,?,?, 'Active')",
                (stock, 25),
            ).lastrowid
        )
        warehouse_id = int(
            conn.execute(
                "INSERT INTO warehouses(code,name,is_default,is_active) VALUES('LIFE-WH','Lifecycle Warehouse',0,1)"
            ).lastrowid
        )
        conn.execute(
            "INSERT INTO warehouse_stock(warehouse_id,item_id,stock) VALUES(?,?,?)",
            (warehouse_id, item_id, stock),
        )
    return supplier_id, item_id, warehouse_id


def sale_payload(customer_id: int, item_id: int, *, qty: float = 3) -> tuple[dict, list, dict]:
    line = SalesLine(
        item_name="Lifecycle Item",
        pack_name="1 PCS",
        hsn="1905",
        unit="PCS",
        qty=qty,
        free_qty=1,
        mrp=40,
        rate=33.33,
        scheme=0,
        discount_amount=0,
        gst_rate=5,
        item_id=item_id,
    )
    computed = SalesCalculator("Tamil Nadu").compute_line(line)
    totals = SalesCalculator("Tamil Nadu").totals([computed])
    header = {
        "bill_no": "LIFE-SALE-001",
        "bill_date": "2026-07-10",
        "customer_id": customer_id,
        "customer_name": "Lifecycle Customer",
        "customer_area": "",
        "payment": "Credit",
        "party_type": "customer",
        "party_id": customer_id,
        "party_name": "Lifecycle Customer",
        "price_level": "Retail",
        "employee": "QA",
        "warehouse_id": 0,
        "branch": "Main",
        "cost_center": "",
        "shipping": "",
        "po_no": "",
        "transport": "",
        "credit_terms": "",
    }
    return header, [computed], totals


def purchase_payload(
    supplier_id: int,
    item_id: int,
    warehouse_id: int,
    *,
    qty: float = 4,
    free_qty: float = 1,
    bill_no: str = "LIFE-PUR-001",
) -> tuple[dict, list, dict]:
    line = SalesLine(
        item_name="Lifecycle Purchase Item",
        pack_name="1 PCS",
        hsn="1905",
        unit="PCS",
        qty=qty,
        free_qty=free_qty,
        mrp=75,
        rate=50,
        scheme=0,
        discount_amount=0,
        gst_rate=18,
        item_id=item_id,
    )
    computed = SalesCalculator("Tamil Nadu").compute_line(line)
    totals = SalesCalculator("Tamil Nadu").totals([computed])
    header = {
        "bill_no": bill_no,
        "bill_date": "2026-07-10",
        "supplier_id": supplier_id,
        "supplier_name": "Lifecycle Supplier",
        "payment": "Credit",
        "party_type": "supplier",
        "party_id": supplier_id,
        "party_name": "Lifecycle Supplier",
        "price_level": "Purchase",
        "employee": "QA",
        "warehouse_id": warehouse_id,
        "branch": "Main",
        "cost_center": "",
    }
    return header, [computed], totals


def test_credit_sale_free_quantity_roundoff_and_cancel_reconcile(tmp_path: Path) -> None:
    db_path = copy_db(tmp_path)
    customer_id, item_id = add_customer_and_item(db_path, stock=10)
    repository = TransactionRepository(db_path)
    header, lines, totals = sale_payload(customer_id, item_id)

    sale_id = repository.save_sales(header, lines, totals)

    with sqlite3.connect(db_path) as conn:
        stock = conn.execute("SELECT stock FROM items WHERE id=?", (item_id,)).fetchone()[0]
        balance = conn.execute("SELECT balance FROM customers WHERE id=?", (customer_id,)).fetchone()[0]
        debit, credit = conn.execute(
            "SELECT ROUND(SUM(debit),2),ROUND(SUM(credit),2) FROM ledger_postings WHERE source_table='sales' AND source_id=? AND status='Active'",
            (sale_id,),
        ).fetchone()
        round_off = conn.execute(
            "SELECT debit,credit FROM ledger_postings WHERE source_table='sales' AND source_id=? AND ledger_name='Round Off'",
            (sale_id,),
        ).fetchone()

    assert stock == 7
    assert balance == totals["grand_total"]
    assert debit == credit == totals["grand_total"]
    assert round_off == (0, totals["round_off"])

    repository.cancel_transaction("sales", sale_id, "Customer order cancelled")

    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT stock FROM items WHERE id=?", (item_id,)).fetchone()[0] == 10
        assert conn.execute("SELECT balance FROM customers WHERE id=?", (customer_id,)).fetchone()[0] == 0
        assert conn.execute("SELECT status FROM sales WHERE id=?", (sale_id,)).fetchone()[0] == "Cancelled"
        assert conn.execute(
            "SELECT COUNT(*) FROM ledger_postings WHERE source_table='sales' AND source_id=? AND status<>'Cancelled'",
            (sale_id,),
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM gst_postings WHERE source_table='sales' AND source_id=? AND status<>'Cancelled'",
            (sale_id,),
        ).fetchone()[0] == 0
        movement = conn.execute(
            "SELECT ROUND(SUM(qty_in),3),ROUND(SUM(qty_out),3) FROM stock_log WHERE ref_no='LIFE-SALE-001'"
        ).fetchone()
        assert movement == (3, 3)

    with pytest.raises(ValueError, match="already cancelled"):
        repository.cancel_transaction("sales", sale_id, "Duplicate cancellation")


def test_sales_edit_reverses_old_effects_without_active_duplicates(tmp_path: Path) -> None:
    db_path = copy_db(tmp_path)
    customer_id, item_id = add_customer_and_item(db_path, stock=20)
    repository = TransactionRepository(db_path)
    header, lines, totals = sale_payload(customer_id, item_id)
    sale_id = repository.save_sales(header, lines, totals)

    edited_header, edited_lines, edited_totals = sale_payload(customer_id, item_id, qty=4)
    edited_header["bill_no"] = "LIFE-SALE-001"
    assert repository.edit_sales(sale_id, edited_header, edited_lines, edited_totals) == sale_id

    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT stock FROM items WHERE id=?", (item_id,)).fetchone()[0] == 16
        assert conn.execute("SELECT balance FROM customers WHERE id=?", (customer_id,)).fetchone()[0] == edited_totals["grand_total"]
        assert conn.execute("SELECT COUNT(*) FROM sales_items WHERE sale_id=?", (sale_id,)).fetchone()[0] == 1
        assert conn.execute(
            "SELECT COUNT(*) FROM voucher_headers WHERE source_table='sales' AND source_id=? AND status='Active'",
            (sale_id,),
        ).fetchone()[0] == 1
        assert conn.execute(
            "SELECT COUNT(*) FROM voucher_headers WHERE source_table='sales' AND source_id=? AND status='Superseded'",
            (sale_id,),
        ).fetchone()[0] == 1
        debit, credit = conn.execute(
            "SELECT ROUND(SUM(debit),2),ROUND(SUM(credit),2) FROM ledger_postings WHERE source_table='sales' AND source_id=? AND status='Active'",
            (sale_id,),
        ).fetchone()
        assert debit == credit == edited_totals["grand_total"]


def test_receipt_updates_outstanding_and_cancel_restores_it(tmp_path: Path) -> None:
    db_path = copy_db(tmp_path)
    with sqlite3.connect(db_path) as conn:
        customer_id = int(conn.execute("INSERT INTO customers(name,balance,status) VALUES('Receipt Customer',500,'Active')").lastrowid)
    repository = TransactionRepository(db_path)
    receipt_id = repository.save_account_entry(
        "receipt",
        {
            "doc_no": "LIFE-REC-001",
            "entry_date": "2026-07-10",
            "party_id": customer_id,
            "party_name": "Receipt Customer",
            "party_type": "customer",
            "amount": 125,
            "mode": "Bank",
            "notes": "Partial allocation",
            "status": "Active",
            "branch": "Main",
            "cost_center": "",
        },
    )
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT balance FROM customers WHERE id=?", (customer_id,)).fetchone()[0] == 375
    repository.cancel_transaction("receipts", receipt_id, "Receipt entered twice")
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT balance FROM customers WHERE id=?", (customer_id,)).fetchone()[0] == 500
        assert conn.execute(
            "SELECT COUNT(*) FROM ledger_postings WHERE source_table='receipts' AND source_id=? AND status='Cancelled'",
            (receipt_id,),
        ).fetchone()[0] == 2


def test_stock_transfer_has_equal_out_and_in_and_preserves_global_stock(tmp_path: Path) -> None:
    db_path = copy_db(tmp_path)
    with sqlite3.connect(db_path) as conn:
        item_id = int(conn.execute("INSERT INTO items(code,name,unit,stock,status) VALUES('TRANSFER-ITEM','Transfer Item','PCS',10,'Active')").lastrowid)
        from_id = int(conn.execute("INSERT INTO warehouses(code,name,is_default,is_active) VALUES('FROM-QA','From QA',0,1)").lastrowid)
        to_id = int(conn.execute("INSERT INTO warehouses(code,name,is_default,is_active) VALUES('TO-QA','To QA',0,1)").lastrowid)
        conn.execute("INSERT INTO warehouse_stock(warehouse_id,item_id,stock) VALUES(?,?,10)", (from_id, item_id))
    repository = TransactionRepository(db_path)
    repository.save_inventory_entry(
        "transfer",
        {"doc_no": "LIFE-TRF-001", "doc_date": "2026-07-10", "from_warehouse_id": from_id, "to_warehouse_id": to_id, "status": "Active", "notes": ""},
        [{"item_id": item_id, "pack_id": 0, "item_name": "Transfer Item", "pack_name": "1 PCS", "pack_size": 1, "hsn": "", "unit": "PCS", "qty": 4, "mrp": 0}],
    )
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT stock FROM items WHERE id=?", (item_id,)).fetchone()[0] == 10
        assert conn.execute("SELECT stock FROM warehouse_stock WHERE warehouse_id=? AND item_id=?", (from_id, item_id)).fetchone()[0] == 6
        assert conn.execute("SELECT stock FROM warehouse_stock WHERE warehouse_id=? AND item_id=?", (to_id, item_id)).fetchone()[0] == 4
        movement = conn.execute(
            "SELECT SUM(qty_in),SUM(qty_out) FROM stock_log WHERE ref_no='LIFE-TRF-001'"
        ).fetchone()
        assert movement == (4, 4)

    with sqlite3.connect(db_path) as conn:
        saved_transfer_id = conn.execute(
            "SELECT id FROM stock_transfers WHERE transfer_no='LIFE-TRF-001'"
        ).fetchone()[0]
    repository.cancel_transaction("stock_transfers", saved_transfer_id, "Transfer entered for wrong warehouse")
    with sqlite3.connect(db_path) as conn:
        assert conn.execute(
            "SELECT stock FROM warehouse_stock WHERE warehouse_id=? AND item_id=?",
            (from_id, item_id),
        ).fetchone()[0] == 10
        assert conn.execute(
            "SELECT stock FROM warehouse_stock WHERE warehouse_id=? AND item_id=?",
            (to_id, item_id),
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT status FROM stock_transfers WHERE id=?", (saved_transfer_id,)
        ).fetchone()[0] == "Cancelled"
        assert conn.execute(
            "SELECT SUM(qty_in),SUM(qty_out) FROM stock_log WHERE ref_no='LIFE-TRF-001'"
        ).fetchone() == (8, 8)


def test_credit_purchase_edit_return_payment_and_cancel_reconcile(tmp_path: Path) -> None:
    db_path = copy_db(tmp_path)
    supplier_id, item_id, warehouse_id = add_supplier_item_and_warehouse(db_path, stock=5)
    repository = TransactionRepository(db_path)
    header, lines, totals = purchase_payload(supplier_id, item_id, warehouse_id)

    purchase_id = repository.save_purchase(header, lines, totals)
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT stock FROM items WHERE id=?", (item_id,)).fetchone()[0] == 9
        assert conn.execute("SELECT balance FROM suppliers WHERE id=?", (supplier_id,)).fetchone()[0] == totals["grand_total"]
        assert conn.execute(
            "SELECT stock FROM warehouse_stock WHERE warehouse_id=? AND item_id=?",
            (warehouse_id, item_id),
        ).fetchone()[0] == 9

    edited_header, edited_lines, edited_totals = purchase_payload(
        supplier_id,
        item_id,
        warehouse_id,
        qty=2,
        free_qty=0,
    )
    repository.edit_purchase(purchase_id, edited_header, edited_lines, edited_totals)
    loaded = repository.load_document_for_edit("purchases", purchase_id)
    assert loaded["header"]["bill_no"] == "LIFE-PUR-001"
    assert loaded["lines"][0]["qty"] == 2
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT stock FROM items WHERE id=?", (item_id,)).fetchone()[0] == 7
        assert conn.execute("SELECT balance FROM suppliers WHERE id=?", (supplier_id,)).fetchone()[0] == edited_totals["grand_total"]
        assert conn.execute(
            "SELECT COUNT(*) FROM voucher_headers WHERE source_table='purchases' AND source_id=? AND status='Active'",
            (purchase_id,),
        ).fetchone()[0] == 1
        assert conn.execute(
            "SELECT COUNT(*) FROM voucher_headers WHERE source_table='purchases' AND source_id=? AND status='Superseded'",
            (purchase_id,),
        ).fetchone()[0] == 1

    purchase_item_id = loaded["lines"][0]["id"]
    return_line = SalesLine(
        item_name="Lifecycle Purchase Item",
        pack_name="1 PCS",
        hsn="1905",
        unit="PCS",
        qty=1,
        free_qty=0,
        mrp=75,
        rate=50,
        scheme=0,
        discount_amount=0,
        gst_rate=18,
        item_id=item_id,
        source_item_id=purchase_item_id,
        source_doc_id=purchase_id,
    )
    computed_return = SalesCalculator("Tamil Nadu").compute_line(return_line)
    return_totals = SalesCalculator("Tamil Nadu").totals([computed_return])
    return_id = repository.save_purchase_return(
        {
            "doc_no": "LIFE-DN-001",
            "doc_date": "2026-07-10",
            "source_doc_id": purchase_id,
            "purchase_id": purchase_id,
            "party_type": "supplier",
            "party_id": supplier_id,
            "party_name": "Lifecycle Supplier",
            "warehouse_id": warehouse_id,
            "payment": "Credit",
            "status": "Active",
            "notes": "One item returned",
            "branch": "Main",
            "cost_center": "",
        },
        [computed_return],
        return_totals,
    )
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT stock FROM items WHERE id=?", (item_id,)).fetchone()[0] == 6
        assert conn.execute("SELECT balance FROM suppliers WHERE id=?", (supplier_id,)).fetchone()[0] == edited_totals["grand_total"] - return_totals["grand_total"]
    repository.cancel_transaction("purchase_returns", return_id, "Supplier accepted corrected delivery")

    payment_id = repository.save_account_entry(
        "payment",
        {
            "doc_no": "LIFE-PAY-001",
            "entry_date": "2026-07-10",
            "party_id": supplier_id,
            "party_name": "Lifecycle Supplier",
            "party_type": "supplier",
            "amount": 50,
            "mode": "Bank",
            "notes": "Partial payment",
            "status": "Active",
            "branch": "Main",
            "cost_center": "",
        },
    )
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT balance FROM suppliers WHERE id=?", (supplier_id,)).fetchone()[0] == edited_totals["grand_total"] - 50
    repository.cancel_transaction("payments", payment_id, "Payment allocation corrected")
    repository.cancel_transaction("purchases", purchase_id, "Purchase cancelled after payment reversal")
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT stock FROM items WHERE id=?", (item_id,)).fetchone()[0] == 5
        assert conn.execute("SELECT balance FROM suppliers WHERE id=?", (supplier_id,)).fetchone()[0] == 0


def test_sales_return_cancel_restores_sale_effects(tmp_path: Path) -> None:
    db_path = copy_db(tmp_path)
    customer_id, item_id = add_customer_and_item(db_path, stock=20)
    repository = TransactionRepository(db_path)
    header, lines, totals = sale_payload(customer_id, item_id, qty=5)
    sale_id = repository.save_sales(header, lines, totals)
    with sqlite3.connect(db_path) as conn:
        sale_item_id = conn.execute("SELECT id FROM sales_items WHERE sale_id=?", (sale_id,)).fetchone()[0]
    source = SalesLine(
        item_name="Lifecycle Item",
        pack_name="1 PCS",
        hsn="1905",
        unit="PCS",
        qty=2,
        free_qty=0,
        mrp=40,
        rate=33.33,
        scheme=0,
        discount_amount=0,
        gst_rate=5,
        item_id=item_id,
        source_item_id=sale_item_id,
        source_doc_id=sale_id,
    )
    computed = SalesCalculator("Tamil Nadu").compute_line(source)
    return_totals = SalesCalculator("Tamil Nadu").totals([computed])
    return_id = repository.save_sales_return(
        {
            "doc_no": "LIFE-SR-001",
            "doc_date": "2026-07-10",
            "source_doc_id": sale_id,
            "sale_id": sale_id,
            "party_type": "customer",
            "party_id": customer_id,
            "party_name": "Lifecycle Customer",
            "warehouse_id": 0,
            "payment": "Credit",
            "status": "Active",
            "notes": "Customer return",
            "branch": "Main",
            "cost_center": "",
        },
        [computed],
        return_totals,
    )
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT stock FROM items WHERE id=?", (item_id,)).fetchone()[0] == 17
        assert conn.execute("SELECT balance FROM customers WHERE id=?", (customer_id,)).fetchone()[0] == totals["grand_total"] - return_totals["grand_total"]
    repository.cancel_transaction("sales_returns", return_id, "Return withdrawn")
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT stock FROM items WHERE id=?", (item_id,)).fetchone()[0] == 15
        assert conn.execute("SELECT balance FROM customers WHERE id=?", (customer_id,)).fetchone()[0] == totals["grand_total"]
        assert conn.execute(
            "SELECT COUNT(*) FROM gst_postings WHERE source_table='sales_returns' AND source_id=? AND status='Active'",
            (return_id,),
        ).fetchone()[0] == 0


def test_interstate_multi_rate_discount_gst_matches_document_and_reports(tmp_path: Path) -> None:
    db_path = copy_db(tmp_path)
    customer_id, first_item = add_customer_and_item(db_path, stock=20)
    with sqlite3.connect(db_path) as conn:
        second_item = int(
            conn.execute(
                "INSERT INTO items(code,name,unit,gst,stock,standard_cost,status) VALUES('LIFE-GST-2','Lifecycle GST Item','PCS',18,20,20,'Active')"
            ).lastrowid
        )
    calculator = SalesCalculator("Tamil Nadu")
    raw_lines = [
        SalesLine("Lifecycle Item", "1 PCS", "1905", "PCS", 1, 0, 110, 100, 0, 0, 5, item_id=first_item),
        SalesLine("Lifecycle GST Item", "1 PCS", "2106", "PCS", 2, 0, 60, 50, 0, 10, 18, item_id=second_item),
    ]
    lines = [calculator.compute_line(line, "Karnataka") for line in raw_lines]
    totals = calculator.totals(lines)
    repository = TransactionRepository(db_path)
    sale_id = repository.save_sales(
        {
            "bill_no": "LIFE-GST-001",
            "bill_date": "2026-07-10",
            "customer_id": customer_id,
            "customer_name": "Lifecycle Customer",
            "customer_area": "",
            "payment": "Credit",
            "party_type": "customer",
            "party_id": customer_id,
            "party_name": "Lifecycle Customer",
            "price_level": "Retail",
            "employee": "QA",
            "warehouse_id": 0,
            "branch": "Main",
            "cost_center": "",
            "shipping": "",
            "po_no": "",
            "transport": "",
            "credit_terms": "",
        },
        lines,
        totals,
    )
    with sqlite3.connect(db_path) as conn:
        document = conn.execute(
            "SELECT taxable,gst_total,cgst_total,sgst_total,igst_total FROM sales WHERE id=?",
            (sale_id,),
        ).fetchone()
        posting = conn.execute(
            "SELECT ROUND(SUM(taxable),2),ROUND(SUM(cgst),2),ROUND(SUM(sgst),2),ROUND(SUM(igst),2) FROM gst_postings WHERE source_table='sales' AND source_id=? AND status='Active'",
            (sale_id,),
        ).fetchone()
    assert document == (totals["taxable"], totals["gst_total"], 0, 0, totals["igst"])
    assert posting == (totals["taxable"], 0, 0, totals["igst"])

    previous = os.environ.get("PRM_SQLITE_DB")
    os.environ["PRM_SQLITE_DB"] = str(db_path)
    try:
        source = MySqlSource()
        sales_rows = source.operation_rows("sales_list", 1000)
        gst_rows = source.operation_rows("gst_reports", 1000)
        trial_rows = source.operation_rows("trial_balance", 1000)
    finally:
        if previous is None:
            os.environ.pop("PRM_SQLITE_DB", None)
        else:
            os.environ["PRM_SQLITE_DB"] = previous
    assert any(row.get("bill_no") == "LIFE-GST-001" for row in sales_rows)
    report_gst = [row for row in gst_rows if row.get("source_ref") == "LIFE-GST-001"]
    assert round(sum(float(row["igst"] or 0) for row in report_gst), 2) == totals["igst"]
    with sqlite3.connect(db_path) as conn:
        active_debit, active_credit = conn.execute(
            """
            SELECT ROUND(SUM(debit),2),ROUND(SUM(credit),2)
            FROM ledger_postings
            WHERE LOWER(COALESCE(status,'active')) NOT IN ('cancelled','void','deleted','superseded')
            """
        ).fetchone()
        sale_debit, sale_credit = conn.execute(
            "SELECT ROUND(SUM(debit),2),ROUND(SUM(credit),2) FROM ledger_postings WHERE source_table='sales' AND source_id=? AND status='Active'",
            (sale_id,),
        ).fetchone()
    assert sale_debit == sale_credit
    assert round(sum(float(row["debit"] or 0) for row in trial_rows), 2) == active_debit
    assert round(sum(float(row["credit"] or 0) for row in trial_rows), 2) == active_credit


def test_validation_failures_are_atomic_and_locked_year_is_blocked(tmp_path: Path) -> None:
    db_path = copy_db(tmp_path)
    customer_id, item_id = add_customer_and_item(db_path, stock=1)
    repository = TransactionRepository(db_path)
    header, lines, totals = sale_payload(customer_id, item_id, qty=2)
    header["bill_no"] = "LIFE-FAIL-STOCK"
    with pytest.raises(ValueError, match="Stock is not available"):
        repository.save_sales(header, lines, totals)
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM sales WHERE bill_no='LIFE-FAIL-STOCK'").fetchone()[0] == 0
        assert conn.execute("SELECT stock FROM items WHERE id=?", (item_id,)).fetchone()[0] == 1

    valid_header, valid_lines, valid_totals = sale_payload(customer_id, item_id, qty=1)
    repository.save_sales(valid_header, valid_lines, valid_totals)
    with pytest.raises(ValueError, match="already exists"):
        repository.save_sales(valid_header, valid_lines, valid_totals)
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM sales WHERE bill_no='LIFE-SALE-001'").fetchone()[0] == 1
        conn.execute("UPDATE financial_years SET is_locked=1 WHERE start_date<='2026-07-10' AND end_date>='2026-07-10'")

    locked_header, locked_lines, locked_totals = sale_payload(customer_id, item_id, qty=1)
    locked_header["bill_no"] = "LIFE-LOCKED-001"
    with pytest.raises(ValueError, match="closed for posting"):
        repository.save_sales(locked_header, locked_lines, locked_totals)
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM sales WHERE bill_no='LIFE-LOCKED-001'").fetchone()[0] == 0


def test_draft_voucher_does_not_post_and_journal_cancel_is_balanced(tmp_path: Path) -> None:
    db_path = copy_db(tmp_path)
    with sqlite3.connect(db_path) as conn:
        customer_id = int(conn.execute("INSERT INTO customers(name,balance,status) VALUES('Draft Customer',100,'Active')").lastrowid)
    repository = TransactionRepository(db_path)
    draft_id = repository.save_account_entry(
        "receipt",
        {
            "doc_no": "LIFE-DRAFT-REC",
            "entry_date": "2026-07-10",
            "party_id": customer_id,
            "party_name": "Draft Customer",
            "party_type": "customer",
            "amount": 25,
            "mode": "Cash",
            "status": "Draft",
            "notes": "Not posted",
            "branch": "Main",
            "cost_center": "",
        },
    )
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT balance FROM customers WHERE id=?", (customer_id,)).fetchone()[0] == 100
        assert conn.execute("SELECT COUNT(*) FROM voucher_headers WHERE source_table='receipts' AND source_id=?", (draft_id,)).fetchone()[0] == 0
    repository.cancel_transaction("receipts", draft_id, "Draft abandoned")

    journal_id = repository.save_account_entry(
        "journal",
        {
            "doc_no": "LIFE-CONTRA-001",
            "entry_date": "2026-07-10",
            "party_id": 0,
            "party_name": "Cash",
            "party_type": "ledger",
            "credit_ledger": "Bank",
            "voucher_type": "Contra",
            "amount": 75,
            "mode": "Adjustment",
            "status": "Active",
            "notes": "Cash deposited",
            "branch": "Main",
            "cost_center": "",
        },
    )
    with sqlite3.connect(db_path) as conn:
        debit, credit = conn.execute(
            "SELECT SUM(debit),SUM(credit) FROM ledger_postings WHERE source_table='journal_entries' AND source_id=? AND status='Active'",
            (journal_id,),
        ).fetchone()
        assert debit == credit == 75
    repository.cancel_transaction("journal_entries", journal_id, "Contra entered twice")
    with sqlite3.connect(db_path) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM ledger_postings WHERE source_table='journal_entries' AND source_id=? AND status='Cancelled'",
            (journal_id,),
        ).fetchone()[0] == 2


def test_stock_adjustment_prevents_negative_and_rolls_back(tmp_path: Path) -> None:
    db_path = copy_db(tmp_path)
    _, item_id, warehouse_id = add_supplier_item_and_warehouse(db_path, stock=10)
    repository = TransactionRepository(db_path)
    repository.save_inventory_entry(
        "adjustment",
        {
            "doc_no": "LIFE-ADJ-001",
            "doc_date": "2026-07-10",
            "from_warehouse_id": warehouse_id,
            "status": "Active",
            "notes": "Physical count",
        },
        [{"item_id": item_id, "pack_id": 0, "item_name": "Lifecycle Purchase Item", "pack_name": "1 PCS", "pack_size": 1, "hsn": "1905", "unit": "PCS", "qty": 7, "current": 10, "difference": -3, "reason": "Counted"}],
    )
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT stock FROM items WHERE id=?", (item_id,)).fetchone()[0] == 7
        assert conn.execute("SELECT stock FROM warehouse_stock WHERE warehouse_id=? AND item_id=?", (warehouse_id, item_id)).fetchone()[0] == 7
    with pytest.raises(ValueError, match="Stock is not available"):
        repository.save_inventory_entry(
            "adjustment",
            {"doc_no": "LIFE-ADJ-002", "doc_date": "2026-07-10", "from_warehouse_id": warehouse_id, "status": "Active", "notes": "Invalid negative"},
            [{"item_id": item_id, "pack_id": 0, "item_name": "Lifecycle Purchase Item", "pack_name": "1 PCS", "pack_size": 1, "hsn": "1905", "unit": "PCS", "qty": 1, "current": 7, "difference": -8, "reason": "Invalid"}],
        )
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT stock FROM items WHERE id=?", (item_id,)).fetchone()[0] == 7
        assert conn.execute("SELECT COUNT(*) FROM stock_adjustments WHERE adj_no='LIFE-ADJ-002'").fetchone()[0] == 0
