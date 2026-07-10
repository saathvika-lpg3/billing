from __future__ import annotations

import re
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from pypdf import PdfReader

from services.mysql_source import MySqlSource
from services.pdf_print import (
    _company_address,
    _company_contact_line,
    _company_name,
    _report_template_row,
    _resolve_report_print_options,
    amount_in_words,
    normalize_transaction_header,
    _normalize_voucher_entry,
    resolve_print_options,
    write_report_pdf,
    write_statement_pdf,
    write_transaction_pdf,
    write_voucher_pdf,
)
from services.print_preview import PrintPreviewDialog
from views.document_center_view import PRINT_DOC_META


SOURCE_DB = Path(r"D:\PRM_GST_DESKTOP\database\prm_billing_inventory.db")


def _company() -> dict:
    with sqlite3.connect(SOURCE_DB) as conn:
        conn.row_factory = sqlite3.Row
        return dict(conn.execute("SELECT * FROM company LIMIT 1").fetchone())


def _media_box(path: Path) -> tuple[float, float]:
    data = path.read_bytes()
    match = re.search(rb"/MediaBox\s*\[\s*0\s+0\s+([0-9.]+)\s+([0-9.]+)\s*\]", data)
    assert match, "PDF MediaBox was not found"
    return float(match.group(1)), float(match.group(2))


def _page_count(path: Path) -> int:
    return len(re.findall(rb"/Type\s*/Page\b", path.read_bytes()))


def _pdf_text(path: Path) -> str:
    return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)


def _flat_pdf_text(path: Path) -> str:
    return re.sub(r"\s+", " ", _pdf_text(path)).strip()


def _detected_preview_layout(path: Path) -> tuple[str, str]:
    probe = type("PreviewProbe", (), {"pdf_path": path})()
    return PrintPreviewDialog._detect_pdf_layout(probe)


def _heavy_lines(count: int = 80) -> tuple[list[dict], dict]:
    rows: list[dict] = []
    totals = {"taxable": 0.0, "discount": 0.0, "cgst": 0.0, "sgst": 0.0, "igst": 0.0, "gst_total": 0.0}
    rates = [5, 12, 18, 0]
    for index in range(1, count + 1):
        rate = rates[index % len(rates)]
        qty = float((index % 4) + 1)
        taxable = round(qty * (18 + index), 2)
        gst_total = round(taxable * rate / 100, 2)
        cgst = round(gst_total / 2, 2)
        sgst = round(gst_total - cgst, 2)
        rows.append(
            {
                "item": f"QA Bulk FMCG Item {index:02d} / 1 Box",
                "hsn": "1905",
                "qty": qty,
                "unit": "Box",
                "mrp": taxable + 10,
                "rate": taxable / qty,
                "free": 1 if index % 10 == 0 else 0,
                "disc": 0,
                "taxable": taxable,
                "gst": rate,
                "cgst": cgst,
                "sgst": sgst,
                "igst": 0,
                "amount": taxable + gst_total,
            }
        )
        totals["taxable"] += taxable
        totals["cgst"] += cgst
        totals["sgst"] += sgst
        totals["gst_total"] += gst_total
    gross = totals["taxable"] + totals["gst_total"]
    rounded = round(gross)
    totals["round_off"] = round(rounded - gross, 2)
    totals["grand_total"] = rounded
    return rows, totals


def _db_with_a2_template(tmp_path: Path) -> Path:
    target = tmp_path / "a2_template.db"
    shutil.copy2(SOURCE_DB, target)
    now = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(target) as conn:
        conn.execute(
            """
            INSERT INTO print_template_families(
                business_type,family_code,family_name,description,default_paper_size,
                default_print_mode,supports_thermal,supports_a4,is_default,is_active,created_at,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            ("a2_test", "a2_test_family", "A2 Test Family", "Heavy invoice pagination test", "a2", "laser", 0, 1, 1, 1, now, now),
        )
        family_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            """
            INSERT INTO print_templates(
                family_id,template_code,template_name,document_type,paper_size,print_mode,
                html_template,css_template,is_default,is_active,created_at,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (family_id, "a2_sales_invoice", "A2 Sales Invoice", "sales_invoice", "a2", "laser", "", "", 1, 1, now, now),
        )
    return target


def _ensure_template_orientation_column(conn: sqlite3.Connection) -> None:
    columns = {str(row[1]).lower() for row in conn.execute("PRAGMA table_info(print_templates)").fetchall()}
    if "orientation" not in columns:
        conn.execute("ALTER TABLE print_templates ADD COLUMN orientation TEXT")


def _db_with_transaction_template(tmp_path: Path, paper_size: str, orientation: str, document_type: str = "sales_invoice") -> tuple[Path, str]:
    target = tmp_path / f"{document_type}_{paper_size}_{orientation}.db"
    shutil.copy2(SOURCE_DB, target)
    now = datetime.now().isoformat(timespec="seconds")
    template_code = f"{document_type}_{paper_size}_{orientation}"
    family_code = f"{template_code}_family"
    with sqlite3.connect(target) as conn:
        _ensure_template_orientation_column(conn)
        conn.execute(
            """
            INSERT INTO print_template_families(
                business_type,family_code,family_name,description,default_paper_size,
                default_print_mode,supports_thermal,supports_a4,is_default,is_active,created_at,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            ("matrix_test", family_code, f"{paper_size} {orientation} Family", "Paper/orientation matrix test", paper_size, "laser", 0, 1, 1, 1, now, now),
        )
        family_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            """
            INSERT INTO print_templates(
                family_id,template_code,template_name,document_type,paper_size,orientation,print_mode,
                html_template,css_template,is_default,is_active,created_at,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (family_id, template_code, f"{paper_size.upper()} {orientation.title()} {document_type}", document_type, paper_size, orientation, "laser", "", "", 1, 1, now, now),
        )
    return target, template_code


def test_sales_and_purchase_templates_resolve_to_supported_paper_sizes() -> None:
    company = _company()

    sales = resolve_print_options(company, "sales_invoice", SOURCE_DB)
    purchase = resolve_print_options(company, "purchase_invoice", SOURCE_DB)

    assert company.get("business_type_code") == "distributor_wholesale"
    assert sales.paper_size == "a2"
    assert purchase.paper_size == "a2"
    assert sales.orientation == "landscape"
    assert purchase.orientation == "landscape"


def test_resolve_print_options_supports_restaurant_alias_business_type() -> None:
    company = _company()
    company["business_type_code"] = "hotel_restaurant"
    company["invoice_template_code"] = ""

    options = resolve_print_options(company, "sales_invoice", SOURCE_DB)

    assert options.business_type == "hotel_restaurant"
    assert options.template_code == "restaurant_final_tax_invoice"
    assert options.paper_size == "a4"
    assert options.orientation == "portrait"
    assert options.family_code == "restaurant_pos_kot_family"


def test_resolve_print_options_supports_service_business_alias() -> None:
    company = _company()
    company["business_type_code"] = "service_business"

    options = resolve_print_options(company, "service_invoice", SOURCE_DB)

    assert options.family_code == "service_repair_family"
    assert options.template_code == "service_invoice"
    assert options.paper_size == "a4"
    assert options.orientation == "portrait"


def test_resolve_print_options_supports_warehouse_based_alias() -> None:
    company = _company()
    company["business_type_code"] = "warehouse_based"
    company["invoice_template_code"] = ""

    options = resolve_print_options(company, "sales_invoice", SOURCE_DB)

    assert options.family_code == "warehouse_operations_family"
    assert options.template_code == "warehouse_gst_invoice"
    assert options.paper_size == "a4"
    assert options.orientation == "portrait"


def test_resolve_print_options_uses_company_level_invoice_template_code() -> None:
    company = _company()
    company["invoice_template_code"] = "sales_invoice"
    company["business_type_code"] = "distributor_wholesale"

    options = resolve_print_options(company, "sales_invoice", SOURCE_DB)

    assert options.template_code == "sales_invoice"
    assert options.paper_size == "a4"
    assert options.orientation == "portrait"


def test_normalize_transaction_header_uses_legacy_sales_invoice_aliases() -> None:
    header = {
        "bill_no": "INV-1001",
        "bill_date": "2026-07-06",
        "customer_name": "Legacy Customer",
        "party_gstin": "27AAAA0000A1Z5",
        "phone": "9999999999",
        "billing_address": "Legacy address",
        "shipping_address": "Ship address",
        "pay_mode": "Bank",
        "salesman": "Salesman 1",
        "transport_details": "Truck 42",
        "po_number": "PO-001",
    }

    normalized = normalize_transaction_header(header, "Bill To", "sales_invoice")

    assert normalized["no"] == "INV-1001"
    assert normalized["date"] == "2026-07-06"
    assert normalized["party_name"] == "Legacy Customer"
    assert normalized["party_gstin"] == "27AAAA0000A1Z5"
    assert normalized["address"] == "Legacy address"
    assert normalized["shipping"] == "Ship address"
    assert normalized["payment"] == "Bank"
    assert normalized["employee"] == "Salesman 1"
    assert normalized["transport"] == "Truck 42"
    assert normalized["po_no"] == "PO-001"


def test_normalize_transaction_header_supports_purchase_invoice_payload() -> None:
    header = {
        "bill_no": "PUR-1002",
        "bill_date": "2026-07-06",
        "supplier_name": "Legacy Supplier",
        "party_gstin": "27BBBB0000B1Z5",
        "phone": "8888888888",
        "address": "Supplier address",
        "shipping_address": "Warehouse address",
        "pay_mode": "Credit",
        "warehouse": "Main WH",
        "branch": "Head Office",
    }

    normalized = normalize_transaction_header(header, "Supplier", "purchase_invoice")

    assert normalized["no"] == "PUR-1002"
    assert normalized["date"] == "2026-07-06"
    assert normalized["party_name"] == "Legacy Supplier"
    assert normalized["party_gstin"] == "27BBBB0000B1Z5"
    assert normalized["address"] == "Supplier address"
    assert normalized["shipping"] == "Warehouse address"
    assert normalized["payment"] == "Credit"
    assert normalized["warehouse"] == "Main WH"
    assert normalized["branch"] == "Head Office"


def test_normalize_voucher_entry_receipt_and_payment_aliases() -> None:
    receipt = {
        "voucher_no": "RCPT-200",
        "voucher_date": "2026-07-06",
        "received_from": "Test Customer",
        "amount": 5000,
        "narration": "Received advance",
        "pay_mode": "Cash",
    }
    normalized = _normalize_voucher_entry(receipt, "receipt")
    assert normalized["doc_no"] == "RCPT-200"
    assert normalized["entry_date"] == "2026-07-06"
    assert normalized["party_name"] == "Test Customer"
    assert normalized["amount"] == 5000
    assert normalized["notes"] == "Received advance"

    payment = {
        "no": "PAY-300",
        "date": "2026-07-06",
        "paid_to": "Test Supplier",
        "total": 2250,
        "remarks": "Supplier payment",
        "payment": "Bank",
    }
    normalized_p = _normalize_voucher_entry(payment, "payment")
    assert normalized_p["doc_no"] == "PAY-300"
    assert normalized_p["entry_date"] == "2026-07-06"
    assert normalized_p["party_name"] == "Test Supplier"
    assert normalized_p["amount"] == 2250
    assert normalized_p["notes"] == "Supplier payment"


def test_transaction_pdf_uses_a4_portrait_template_when_configured(tmp_path: Path) -> None:
    output = tmp_path / "sales_a4.pdf"
    company = _company()
    company["business_type_code"] = "common"
    company["invoice_template_code"] = "sales_invoice"
    lines = [
        {"item": "QA Demo Elaichi / 36 GM", "hsn": "1905", "qty": 1, "unit": "Gram", "mrp": 10, "rate": 9, "free": 0, "disc": 0, "taxable": 9, "gst": 5, "cgst": 0.23, "sgst": 0.22, "igst": 0, "amount": 9.45},
        {"item": "DEMO Biscuit Carton 24pcs / 1 Box", "hsn": "1905", "qty": 1, "unit": "Box", "mrp": 420, "rate": 360, "free": 0, "disc": 0, "taxable": 360, "gst": 18, "cgst": 32.4, "sgst": 32.4, "igst": 0, "amount": 424.8},
    ]
    totals = {"taxable": 369, "discount": 0, "cgst": 32.63, "sgst": 32.63, "igst": 0, "gst_total": 65.25, "round_off": -0.25, "grand_total": 434}

    write_transaction_pdf(
        output,
        "Tax Invoice",
        company,
        {"no": "DRC-26-00052", "date": "2026-06-30", "party_name": "QA Dealer Customer", "shipping": "QA Dealer shipping", "payment": "Cash", "employee": "Administrator"},
        lines,
        totals,
        document_type="sales_invoice",
        party_label="Bill To",
        db_path=SOURCE_DB,
    )

    width, height = _media_box(output)
    assert height > width
    assert 560 < width < 620
    assert 800 < height < 860
    assert output.stat().st_size > 5000


def test_transaction_pdf_honors_paper_orientation_matrix_without_changing_structure(tmp_path: Path) -> None:
    expected = {
        ("a4", "portrait"): ("A4", "Portrait"),
        ("a4", "landscape"): ("A4", "Landscape"),
        ("a2", "portrait"): ("A2", "Portrait"),
        ("a2", "landscape"): ("A2", "Landscape"),
    }
    lines, totals = _heavy_lines(6)

    for (paper_size, orientation), detected in expected.items():
        db_path, template_code = _db_with_transaction_template(tmp_path, paper_size, orientation)
        company = _company()
        company["business_type_code"] = "matrix_test"
        company["invoice_template_code"] = template_code
        output = tmp_path / f"sales_{paper_size}_{orientation}.pdf"

        options = resolve_print_options(company, "sales_invoice", db_path)
        assert (options.paper_size, options.orientation) == (paper_size, orientation)

        write_transaction_pdf(
            output,
            "Tax Invoice",
            company,
            {
                "no": f"{paper_size}-{orientation}",
                "date": "2026-07-10",
                "party_name": "QA Matrix Customer",
                "party_gstin": "36AAAAA0000A1Z5",
                "address": "Billing Address",
                "shipping": "Shipping Address",
                "payment": "Credit",
                "employee": "QA User",
            },
            lines,
            totals,
            document_type="sales_invoice",
            party_label="Bill To",
            ship_to="Shipping Address",
            db_path=db_path,
        )

        assert _detected_preview_layout(output) == detected
        text = _flat_pdf_text(output).upper()
        for expected_text in [
            "TAX INVOICE",
            "BILL TO",
            "SHIP TO",
            "ITEM DESCRIPTION",
            "HSN",
            "QTY",
            "GST SUMMARY",
            "GRAND TOTAL",
            "IN WORDS",
            "TERMS",
            "BANK DETAILS",
            "AUTHORISED SIGNATURE",
        ]:
            assert expected_text in text, (paper_size, orientation, expected_text)


def test_heavy_a4_invoice_paginates_with_final_summary(tmp_path: Path) -> None:
    output = tmp_path / "sales_a4_80_rows.pdf"
    lines, totals = _heavy_lines(80)
    company = _company()
    company["business_type_code"] = "common"
    company["invoice_template_code"] = "sales_invoice"
    write_transaction_pdf(
        output,
        "Tax Invoice",
        company,
        {"no": "A4-80", "date": "2026-07-03", "party_name": "QA Dealer Customer", "payment": "Credit", "employee": "Administrator"},
        lines,
        totals,
        document_type="sales_invoice",
        party_label="Bill To",
        db_path=SOURCE_DB,
    )

    width, height = _media_box(output)
    assert height > width
    assert _page_count(output) >= 3
    text = _flat_pdf_text(output).upper()
    assert text.count("ITEM DESCRIPTION") >= 3
    assert "TAX INVOICE - CONTINUED" in text
    assert "GST SUMMARY" in text
    assert "GRAND TOTAL" in text
    assert "IN WORDS" in text
    assert "AUTHORISED SIGNATURE" in text
    assert output.stat().st_size > 10000


def test_heavy_a2_invoice_template_paginates_landscape(tmp_path: Path) -> None:
    output = tmp_path / "sales_a2_80_rows.pdf"
    db_path = _db_with_a2_template(tmp_path)
    company = _company()
    company["business_type_code"] = "a2_test"
    lines, totals = _heavy_lines(80)

    write_transaction_pdf(
        output,
        "Tax Invoice",
        company,
        {"no": "A2-80", "date": "2026-07-03", "party_name": "QA Dealer Customer", "payment": "Credit", "employee": "Administrator"},
        lines,
        totals,
        document_type="sales_invoice",
        party_label="Bill To",
        db_path=db_path,
    )

    width, height = _media_box(output)
    assert width > height
    assert width > 1100
    assert _page_count(output) >= 2
    text = _flat_pdf_text(output).upper()
    assert text.count("ITEM DESCRIPTION") >= 2
    assert "TAX INVOICE - CONTINUED" in text
    assert "GST SUMMARY" in text
    assert "GRAND TOTAL" in text
    assert "IN WORDS" in text
    assert output.stat().st_size > 12000


def test_receipt_payment_voucher_pdf_uses_a2_landscape(tmp_path: Path) -> None:
    output = tmp_path / "receipt.pdf"
    write_voucher_pdf(
        output,
        "Receipt Voucher",
        _company(),
        {"doc_no": "RCPT-001", "entry_date": "2026-07-02", "party_name": "Test Customer", "amount": 1250, "mode": "Cash", "status": "Active", "notes": "Advance receipt"},
        voucher_type="receipt",
        party_label="Received From",
        db_path=SOURCE_DB,
    )

    width, height = _media_box(output)
    assert width > height
    assert width > 1600
    assert height > 1100
    assert output.stat().st_size > 3000

    payment_output = tmp_path / "payment.pdf"
    write_voucher_pdf(
        payment_output,
        "Payment Voucher",
        _company(),
        {"doc_no": "PAY-001", "entry_date": "2026-07-02", "party_name": "Test Supplier", "amount": 2250, "mode": "Bank", "status": "Active", "notes": "Supplier payment"},
        voucher_type="payment_voucher",
        party_label="Paid To",
        db_path=SOURCE_DB,
    )
    payment_width, payment_height = _media_box(payment_output)
    assert payment_width > payment_height
    assert payment_width > 1600


def test_dispatch_report_pdf_repeats_header_across_pages(tmp_path: Path) -> None:
    output = tmp_path / "dispatch_report_160_rows.pdf"
    rows = [
        {
            "challan_no": f"LOAD-{index:04d}",
            "challan_date": "2026-07-03",
            "area": f"Route {index % 9}",
            "vehicle_no": f"TS09AB{index:04d}",
            "driver_name": "Driver Name",
            "salesman_name": "Salesman Name",
            "total_qty": index,
            "dispatch_status": "Pending Dispatch",
        }
        for index in range(1, 161)
    ]

    write_report_pdf(output, "Daily Dispatch Summary", _company(), rows, {"From": "2026-07-01", "To": "2026-07-03", "Rows": len(rows)})

    width, height = _media_box(output)
    assert width > height
    assert _page_count(output) >= 4
    assert output.stat().st_size > 10000


def test_report_pdf_can_force_a2_landscape_and_page_numbers(tmp_path: Path) -> None:
    output = tmp_path / "daily_dispatch_a2.pdf"
    rows = [
        {"challan_no": f"LOAD-{index:04d}", "area": f"Route {index % 9}", "vehicle_no": f"TS09AB{index:04d}", "total_qty": index}
        for index in range(1, 21)
    ]

    write_report_pdf(
        output,
        "Daily Dispatch Summary",
        _company(),
        rows,
        {"Rows": len(rows)},
        paper_size="a2",
        orientation="landscape",
    )

    width, height = _media_box(output)
    assert width > height
    assert width > 1100
    assert _page_count(output) >= 2


def test_print_preview_detects_generated_report_paper_and_orientation(tmp_path: Path) -> None:
    rows = [{"particular": "Preview Probe", "amount": "1.00"}]
    a4_output = tmp_path / "preview_a4_portrait.pdf"
    a2_output = tmp_path / "preview_a2_landscape.pdf"

    write_report_pdf(
        a4_output,
        "Preview Probe",
        _company(),
        rows,
        {"Rows": 1},
        paper_size="a4",
        orientation="portrait",
    )
    write_report_pdf(
        a2_output,
        "Preview Probe",
        _company(),
        rows,
        {"Rows": 1},
        paper_size="a2",
        orientation="landscape",
    )

    assert _detected_preview_layout(a4_output) == ("A4", "Portrait")
    assert _detected_preview_layout(a2_output) == ("A2", "Landscape")


def test_report_pdf_honors_required_paper_orientation_matrix(tmp_path: Path) -> None:
    rows = [{"particular": "Matrix Probe", "amount": "1.00"}]
    expected = {
        ("a4", "portrait"): ("A4", "Portrait"),
        ("a4", "landscape"): ("A4", "Landscape"),
        ("a2", "portrait"): ("A2", "Portrait"),
        ("a2", "landscape"): ("A2", "Landscape"),
    }

    for (paper_size, orientation), detected in expected.items():
        output = tmp_path / f"report_{paper_size}_{orientation}.pdf"
        write_report_pdf(
            output,
            "Preview Probe",
            _company(),
            rows,
            {"Rows": 1},
            paper_size=paper_size,
            orientation=orientation,
        )
        assert _detected_preview_layout(output) == detected


def test_accounting_statement_pdfs_use_locked_two_sided_layout(tmp_path: Path) -> None:
    source = MySqlSource()
    company = source.company()
    profit_loss = tmp_path / "profit_loss_statement.pdf"
    balance_sheet = tmp_path / "balance_sheet_statement.pdf"

    write_statement_pdf(
        profit_loss,
        "Profit & Loss",
        company,
        source.erp_profit_loss_statement("1900-01-01", "2099-12-31"),
        db_path=SOURCE_DB,
    )
    write_statement_pdf(
        balance_sheet,
        "Balance Sheet",
        company,
        source.balance_sheet_statement("2099-12-31"),
        db_path=SOURCE_DB,
    )

    for output in (profit_loss, balance_sheet):
        width, height = _media_box(output)
        assert height > width
        assert 590 <= width <= 600
        assert 835 <= height <= 846

    profit_text = _flat_pdf_text(profit_loss).lower()
    assert "profit & loss" in profit_text
    assert "particulars" in profit_text
    assert "opening stock" in profit_text
    assert "purchase accounts" in profit_text
    assert "sales accounts" in profit_text
    assert "net profit" in profit_text or "net loss" in profit_text
    assert "statement period side" not in profit_text

    balance_text = _flat_pdf_text(balance_sheet).lower()
    assert "balance sheet" in balance_text
    assert "liabilities" in balance_text
    assert "assets" in balance_text
    assert "capital" in balance_text
    assert "total" in balance_text
    assert "statement period side" not in balance_text


def test_receipt_and_payment_voucher_pdfs_keep_identity_and_reference_details(tmp_path: Path) -> None:
    company = _company()
    receipt_pdf = tmp_path / "receipt_voucher.pdf"
    payment_pdf = tmp_path / "payment_voucher.pdf"
    base_entry = {
        "entry_date": "2026-07-10",
        "party_name": "QA Ledger Party",
        "amount": 1250.75,
        "mode": "UPI",
        "reference": "REF-20260710",
        "instrument_no": "UPI-778899",
        "notes": "Voucher parity smoke check",
        "employee": "QA User",
    }

    write_voucher_pdf(
        receipt_pdf,
        "Receipt Voucher",
        company,
        {"doc_no": "RV-LOCK-1", **base_entry},
        voucher_type="receipt",
        party_label="Received From",
        db_path=SOURCE_DB,
    )
    write_voucher_pdf(
        payment_pdf,
        "Payment Voucher",
        company,
        {"doc_no": "PV-LOCK-1", **base_entry},
        voucher_type="payment",
        party_label="Paid To",
        db_path=SOURCE_DB,
    )

    receipt_text = _flat_pdf_text(receipt_pdf)
    payment_text = _flat_pdf_text(payment_pdf)
    assert "RECEIPT VOUCHER" in receipt_text.upper()
    assert "Received From" in receipt_text
    assert "Reference: REF-20260710" in receipt_text
    assert "Instrument: UPI-778899" in receipt_text
    assert "PAYMENT VOUCHER" not in receipt_text.upper()

    assert "PAYMENT VOUCHER" in payment_text.upper()
    assert "Paid To" in payment_text
    assert "Reference: REF-20260710" in payment_text
    assert "Instrument: UPI-778899" in payment_text
    assert "RECEIPT VOUCHER" not in payment_text.upper()


def test_report_title_resolves_report_template_by_normalized_code(tmp_path: Path) -> None:
    report_db = tmp_path / "report_template.db"
    shutil.copy2(SOURCE_DB, report_db)
    now = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(report_db) as conn:
        conn.execute(
            "INSERT INTO print_template_families(business_type,family_code,family_name,description,default_paper_size,default_print_mode,supports_thermal,supports_a4,is_default,is_active,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                "common",
                "common_report_family",
                "Report Family",
                "Report family for dispatch PDFs",
                "a4",
                "laser",
                0,
                1,
                0,
                1,
                now,
                now,
            ),
        )
        family_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            "INSERT INTO print_templates(family_id,template_code,template_name,document_type,paper_size,print_mode,html_template,css_template,is_default,is_active,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                family_id,
                "loading_sheet",
                "Loading Sheet",
                "report",
                "a4",
                "laser",
                "",
                "",
                1,
                1,
                now,
                now,
            ),
        )
    rows = [
        {"id": 1, "challan_no": "LOAD-0001", "area": "Route 1", "vehicle_no": "TS09AB0001", "driver_name": "Driver", "total_qty": 10, "total_free": 0, "dispatch_status": "Pending"}
    ]
    output = tmp_path / "loading_sheet_template.pdf"
    write_report_pdf(
        output,
        "Loading Sheet",
        _company(),
        rows,
        {"From": "2026-07-01", "To": "2026-07-06"},
        db_path=report_db,
    )

    assert output.exists()
    width, height = _media_box(output)
    assert height > width


def test_report_title_falls_back_to_default_report_template_when_missing(tmp_path: Path) -> None:
    report_db = tmp_path / "report_template_fallback.db"
    shutil.copy2(SOURCE_DB, report_db)

    options = _resolve_report_print_options(_company(), "Loading Sheet", report_db)

    assert options.document_type == "report"
    assert options.template_code == "daily_sales_report"
    assert options.family_code == "common_report_family"
    assert options.paper_size == "a4"
    assert options.orientation == "landscape"


def test_list_report_print_options_use_transaction_templates() -> None:
    company = _company()

    expected_sales = resolve_print_options(company, "sales_invoice", SOURCE_DB)
    actual_sales = _resolve_report_print_options(company, "Sales List", SOURCE_DB, document_type="sales_invoice")
    assert actual_sales == expected_sales

    expected_purchase = resolve_print_options(company, "purchase_invoice", SOURCE_DB)
    actual_purchase = _resolve_report_print_options(company, "Purchase List", SOURCE_DB, document_type="purchase_invoice")
    assert actual_purchase == expected_purchase

    expected_quotation = resolve_print_options(company, "quotation", SOURCE_DB)
    actual_quotation = _resolve_report_print_options(company, "Quotation List", SOURCE_DB, document_type="quotation")
    assert actual_quotation == expected_quotation

    expected_order = resolve_print_options(company, "sales_order", SOURCE_DB)
    actual_order = _resolve_report_print_options(company, "Order List", SOURCE_DB, document_type="sales_order")
    assert actual_order == expected_order

    expected_dc = resolve_print_options(company, "delivery_challan", SOURCE_DB)
    actual_dc = _resolve_report_print_options(company, "DC List", SOURCE_DB, document_type="delivery_challan")
    assert actual_dc == expected_dc


def test_document_center_print_meta_resolves_configured_templates() -> None:
    company = _company()
    expected_document_types = {
        "sales": "sales_invoice",
        "purchases": "purchase_invoice",
        "quotation": "quotation",
        "sales_order": "sales_order",
        "purchase_order": "purchase_order",
        "delivery_challan": "delivery_challan",
        "sales_return": "sales_return",
        "purchase_return": "purchase_return",
    }

    assert {key: meta["document_type"] for key, meta in PRINT_DOC_META.items()} == expected_document_types

    for key, document_type in expected_document_types.items():
        options = resolve_print_options(company, document_type, SOURCE_DB)
        assert options.document_type == document_type, key
        assert options.template_code, key
        assert options.template_name, key
        assert options.paper_size in {"a2", "a3", "a4", "a5", "half_page", "thermal_80"}, key
        assert options.orientation in {"portrait", "landscape"}, key


def test_amount_in_words_uses_rupee_words() -> None:
    assert amount_in_words(434) == "Four Hundred Thirty Four Rupees Only"
    assert amount_in_words(125000) == "One Lakh Twenty Five Thousand Rupees Only"


def test_print_header_company_lines_are_dynamic() -> None:
    company = {
        "name": "QA Dynamic Header Company",
        "business_name": "",
        "address": "",
        "city": "Hyderabad",
        "state": "Telangana",
        "pincode": "500001",
        "gstin": "36ABCDE1234F1Z5",
        "fssai_no": "12345678901234",
        "phone": "9000000000",
        "email": "qa@example.com",
    }

    assert _company_name(company) == "QA Dynamic Header Company"
    assert _company_address(company) == "Hyderabad, Telangana, 500001"
    assert _company_contact_line(company) == (
        "GSTIN: 36ABCDE1234F1Z5 | FSSAI: 12345678901234 | "
        "Phone: 9000000000 | Email: qa@example.com"
    )


def test_report_rows_match_migrated_database_totals() -> None:
    source = MySqlSource()
    with sqlite3.connect(SOURCE_DB) as conn:
        sales_count, sales_total, sales_taxable, sales_gst = conn.execute("SELECT COUNT(*),COALESCE(SUM(grand_total),0),COALESCE(SUM(taxable),0),COALESCE(SUM(gst_total),0) FROM sales").fetchone()
        purchase_count, purchase_total, purchase_taxable, purchase_gst = conn.execute("SELECT COUNT(*),COALESCE(SUM(grand_total),0),COALESCE(SUM(taxable),0),COALESCE(SUM(gst_total),0) FROM purchases").fetchone()
        gst_taxable, gst_cgst, gst_sgst, gst_igst = conn.execute("SELECT COALESCE(SUM(taxable),0),COALESCE(SUM(cgst),0),COALESCE(SUM(sgst),0),COALESCE(SUM(igst),0) FROM gst_postings").fetchone()
        inv_value = conn.execute("SELECT ROUND(COALESCE(SUM(COALESCE(stock,0)*COALESCE(standard_cost,0)),0),2) FROM items").fetchone()[0]
        ledger_debit, ledger_credit = conn.execute("SELECT ROUND(COALESCE(SUM(debit),0),2),ROUND(COALESCE(SUM(credit),0),2) FROM ledger_postings").fetchone()

    sales_rows = source.operation_rows("sales_list", 100000)
    purchase_rows = source.operation_rows("purchase_list", 100000)
    gst_rows = source.operation_rows("gst_reports", 100000)
    inventory_rows = source.operation_rows("inventory_valuation", 100000)
    trial_rows = source.operation_rows("trial_balance", 100000)

    assert len(sales_rows) == sales_count
    assert round(sum(float(row["grand_total"] or 0) for row in sales_rows), 2) == round(float(sales_total), 2)
    assert round(sum(float(row["taxable"] or 0) for row in sales_rows), 2) == round(float(sales_taxable), 2)
    assert round(sum(float(row["gst_total"] or 0) for row in sales_rows), 2) == round(float(sales_gst), 2)

    assert len(purchase_rows) == purchase_count
    assert round(sum(float(row["grand_total"] or 0) for row in purchase_rows), 2) == round(float(purchase_total), 2)
    assert round(sum(float(row["taxable"] or 0) for row in purchase_rows), 2) == round(float(purchase_taxable), 2)
    assert round(sum(float(row["gst_total"] or 0) for row in purchase_rows), 2) == round(float(purchase_gst), 2)

    assert round(sum(float(row["taxable"] or 0) for row in gst_rows), 2) == round(float(gst_taxable), 2)
    assert round(sum(float(row["cgst"] or 0) for row in gst_rows), 2) == round(float(gst_cgst), 2)
    assert round(sum(float(row["sgst"] or 0) for row in gst_rows), 2) == round(float(gst_sgst), 2)
    assert round(sum(float(row["igst"] or 0) for row in gst_rows), 2) == round(float(gst_igst), 2)

    assert round(sum(float(row["stock_value"] or 0) for row in inventory_rows), 2) == round(float(inv_value), 2)
    assert round(sum(float(row["debit"] or 0) for row in trial_rows), 2) == round(float(ledger_debit), 2)
    assert round(sum(float(row["credit"] or 0) for row in trial_rows), 2) == round(float(ledger_credit), 2)


def test_global_search_and_accounting_statement_rows_are_available() -> None:
    source = MySqlSource()

    search = source.global_search("DRC", limit=5, offset=0)
    assert search["total"] >= len(search["rows"]) > 0
    assert {"type", "reference", "target_page"}.issubset(search["rows"][0])

    profit_loss = source.operation_rows("erp_profit_loss", 500, "1900-01-01", "2099-12-31")
    balance_sheet = source.operation_rows("balance_sheet", 500, None, "2099-12-31")

    assert any(row.get("statement") == "Profit & Loss A/c" for row in profit_loss)
    assert any(row.get("particulars") == "Debit Total" for row in profit_loss)
    assert any(row.get("statement") == "Balance Sheet" for row in balance_sheet)
    assert any(row.get("particulars") == "Total Assets" for row in balance_sheet)

    profit_statement = source.erp_profit_loss_statement("1900-01-01", "2099-12-31")
    balance_statement = source.balance_sheet_statement("2099-12-31")

    assert profit_statement["title"] == "Profit & Loss A/c"
    assert any(group["label"] == "Sales Accounts" for group in profit_statement["right_groups"])
    assert any(group["label"] == "Purchase Accounts" for group in profit_statement["left_groups"])
    assert balance_statement["title"] == "Balance Sheet"
    assert balance_statement["left_heading"] == "Liabilities"
    assert balance_statement["right_heading"] == "Assets"
    assert any(row["label"] == "Stock Adjustment Needed" for row in balance_statement["controls"])
