from __future__ import annotations

import re
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
import json
from dataclasses import asdict

from reportlab.lib import colors
from reportlab.lib.pagesizes import A2, A3, A4, A5, landscape, portrait
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from services.business_rules import equivalent_business_type_codes, normalize_business_type


DISTRIBUTOR_A2_TYPES = {
    "sales_invoice",
    "purchase_invoice",
    "quotation",
    "sales_order",
    "purchase_order",
}

VOUCHER_A2_TYPES = {
    "receipt",
    "payment",
    "payment_voucher",
}

DOCUMENT_PRINT_FALLBACKS = {
    "sales_invoice": ("sales_invoice", "Sales Invoice", "common_invoice_family", "a4", "portrait"),
    "purchase_invoice": ("purchase_invoice", "Purchase Invoice", "common_purchase_family", "a4", "portrait"),
    "quotation": ("quotation", "Quotation", "common_invoice_family", "a4", "portrait"),
    "sales_order": ("sales_order", "Sales Order", "common_invoice_family", "a4", "portrait"),
    "purchase_order": ("purchase_order", "Purchase Order", "common_purchase_family", "a4", "portrait"),
    "delivery_challan": ("delivery_challan", "Delivery Challan", "common_inventory_family", "a4", "portrait"),
    "sales_return": ("sales_return", "Sales Return / Credit Note", "common_invoice_family", "a4", "portrait"),
    "purchase_return": ("purchase_return", "Purchase Return / Debit Note", "common_purchase_family", "a4", "portrait"),
    "receipt": ("receipt_voucher", "Receipt Voucher", "common_receipt_payment_family", "a4", "portrait"),
    "payment": ("payment_voucher", "Payment Voucher", "common_receipt_payment_family", "a4", "portrait"),
    "payment_voucher": ("payment_voucher", "Payment Voucher", "common_receipt_payment_family", "a4", "portrait"),
    "expense": ("expense_voucher", "Expense Voucher", "common_receipt_payment_family", "a4", "portrait"),
    "journal": ("journal_voucher", "Journal Voucher", "common_receipt_payment_family", "a4", "portrait"),
}


@dataclass(frozen=True)
class PrintOptions:
    document_type: str
    template_code: str = ""
    template_name: str = ""
    family_code: str = ""
    business_type: str = ""
    paper_size: str = "a4"
    orientation: str = "portrait"
    print_mode: str = "laser"

    @property
    def page_size(self) -> tuple[float, float]:
        base = {
            "a2": A2,
            "a3": A3,
            "a4": A4,
            "a5": A5,
            "half_page": (A4[0], A4[1] / 2),
            "thermal_80": (80 * mm, 220 * mm),
        }.get(_norm(self.paper_size), A4)
        return landscape(base) if _norm(self.orientation) == "landscape" else portrait(base)

    @property
    def is_large_invoice(self) -> bool:
        return _norm(self.paper_size) in {"a2", "a3"} and _norm(self.orientation) == "landscape"


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states: list[dict[str, Any]] = []
        # guard to prevent drawing the same header multiple times on a page
        self._header_drawn: bool = False

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        # reset header flag for the new page
        try:
            self._header_drawn = False
        except Exception:
            pass
        self._startPage()

    def save(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        page_count = len(self._saved_page_states)
        for page_number, state in enumerate(self._saved_page_states, start=1):
            self.__dict__.update(state)
            _draw_page_count(self, self._pagesize[0], 9 * mm, page_number, page_count)
            canvas.Canvas.showPage(self)
        super().save()


def normalize_transaction_header(header: dict[str, Any], party_label: str, document_type: str = "sales_invoice") -> dict[str, Any]:
    normalized = dict(header or {})
    if _norm(document_type) == "sales_invoice":
        normalized.setdefault("no", normalized.get("bill_no") or normalized.get("doc_no") or normalized.get("invoice_no") or "")
        normalized.setdefault("date", normalized.get("bill_date") or normalized.get("doc_date") or normalized.get("entry_date") or "")
        normalized.setdefault("party_name", normalized.get("customer_name") or normalized.get("party") or normalized.get("supplier_name") or "")
        normalized.setdefault("party_gstin", normalized.get("gstin") or normalized.get("party_gstin") or "")
        normalized.setdefault("party_phone", normalized.get("phone") or normalized.get("party_phone") or "")
        normalized.setdefault("address", normalized.get("billing_address") or normalized.get("address") or normalized.get("party_address") or "")
        normalized.setdefault("shipping", normalized.get("shipping_address") or normalized.get("shipping") or normalized.get("ship_to") or "")
        normalized.setdefault("payment", normalized.get("pay_mode") or normalized.get("payment") or normalized.get("mode") or "")
        normalized.setdefault("employee", normalized.get("salesman") or normalized.get("employee") or normalized.get("prepared_by") or "")
        normalized.setdefault("transport", normalized.get("transport_details") or normalized.get("transport") or "")
        normalized.setdefault("po_no", normalized.get("po_number") or normalized.get("po_no") or "")
    elif _norm(document_type) == "purchase_invoice":
        normalized.setdefault("no", normalized.get("bill_no") or normalized.get("doc_no") or normalized.get("invoice_no") or "")
        normalized.setdefault("date", normalized.get("bill_date") or normalized.get("doc_date") or normalized.get("entry_date") or "")
        normalized.setdefault("party_name", normalized.get("supplier_name") or normalized.get("party") or "")
        normalized.setdefault("party_gstin", normalized.get("gstin") or normalized.get("party_gstin") or "")
        normalized.setdefault("party_phone", normalized.get("phone") or normalized.get("party_phone") or "")
        normalized.setdefault("address", normalized.get("billing_address") or normalized.get("address") or "")
        normalized.setdefault("shipping", normalized.get("shipping_address") or normalized.get("shipping") or "")
        normalized.setdefault("payment", normalized.get("pay_mode") or normalized.get("payment") or normalized.get("mode") or "")
        normalized.setdefault("warehouse", normalized.get("warehouse") or normalized.get("store_name") or "")
        normalized.setdefault("branch", normalized.get("branch") or normalized.get("branch_name") or "")
    normalized.setdefault("party", normalized.get("party_name") or "")
    normalized.setdefault("customer_name", normalized.get("party_name") or "")
    normalized.setdefault("supplier_name", normalized.get("party_name") or "")
    normalized.setdefault("party_label", party_label)
    return normalized


def _draw_page_count(pdf: canvas.Canvas, page_width: float, margin: float, page_number: int, page_count: int) -> None:
    _right_text(pdf, f"Page {page_number} of {page_count}", page_width - margin, margin + 8, size=6.2, color="#94A3B8")


def resolve_print_options(
    company: dict[str, Any],
    document_type: str,
    db_path: Path | None = None,
) -> PrintOptions:
    doc_type = _norm(document_type or "sales_invoice")
    business_type = _norm(company.get("business_type_code") or company.get("business_type") or "")
    if doc_type in VOUCHER_A2_TYPES:
        template_code, template_name, family_code, _, _ = DOCUMENT_PRINT_FALLBACKS.get(
            doc_type,
            (doc_type, _title(document_type), "common_receipt_payment_family", "a4", "portrait"),
        )
        return PrintOptions(
            document_type=doc_type,
            template_code=template_code,
            template_name=template_name,
            family_code=family_code,
            business_type=business_type,
            paper_size="a2",
            orientation="landscape",
            print_mode="laser",
        )
    template = _template_row(company, doc_type, db_path)
    if template:
        paper_size = _norm(template.get("paper_size") or template.get("default_paper_size") or "a4")
        if paper_size in {"thermal_58mm", "thermal_58"}:
            paper_size = "thermal_80"
        if paper_size == "thermal_80mm":
            paper_size = "thermal_80"
        orientation = _norm(template.get("orientation") or "")
        if not orientation:
            orientation = "landscape" if paper_size in {"a2", "a3"} and doc_type in DISTRIBUTOR_A2_TYPES else "portrait"
        # If company is a distributor and document is a distributor A2 type,
        # prefer an A2 landscape layout only when the company has not explicitly
        # selected a template. If company provided a template (but no matching
        # template row was found above), allow the family/default to decide
        # paper size rather than unconditionally forcing A2. This avoids
        # changing the paper size for companies that explicitly set a template
        # but the template row is inactive or missing.
        if _norm(business_type) == "distributor_wholesale" and doc_type in DISTRIBUTOR_A2_TYPES:
            # Only force A2 when there's no explicit company template code.
            if not company.get("invoice_template_code"):
                paper_size = "a2"
                orientation = "landscape"
        return PrintOptions(
            document_type=doc_type,
            template_code=str(template.get("template_code") or ""),
            template_name=str(template.get("template_name") or template.get("family_name") or _title(document_type)),
            family_code=str(template.get("family_code") or ""),
            business_type=business_type,
            paper_size=paper_size or "a4",
            orientation=orientation or "portrait",
            print_mode=str(template.get("print_mode") or template.get("default_print_mode") or "laser"),
        )

    if _is_distributor_a2(business_type, doc_type):
        fallback = DOCUMENT_PRINT_FALLBACKS.get(doc_type)
        return PrintOptions(
            document_type=doc_type,
            template_code=str(company.get("invoice_template_code") or (fallback[0] if fallback else "")),
            template_name=fallback[1] if fallback else "Wholesale A2 Tax Invoice",
            family_code=fallback[2] if fallback else "distributor_wholesale",
            business_type=business_type,
            paper_size="a2",
            orientation="landscape",
            print_mode="laser",
        )

    fallback = DOCUMENT_PRINT_FALLBACKS.get(doc_type)
    if fallback:
        template_code, template_name, family_code, paper_size, orientation = fallback
        return PrintOptions(
            document_type=doc_type,
            template_code=template_code,
            template_name=template_name,
            family_code=family_code,
            business_type=business_type,
            paper_size=paper_size,
            orientation=orientation,
            print_mode="laser",
        )

    return PrintOptions(
        document_type=doc_type,
        template_name=_title(document_type),
        business_type=business_type,
    )


def write_transaction_pdf(
    path: Path,
    title: str,
    company: dict[str, Any],
    header: dict[str, Any],
    lines: list[dict[str, Any]],
    totals: dict[str, Any],
    *,
    document_type: str = "sales_invoice",
    party_label: str = "Bill To",
    ship_to: str | None = None,
    db_path: Path | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized_header = normalize_transaction_header(header, party_label, document_type)
    options = resolve_print_options(company, document_type, db_path)
    pdf = NumberedCanvas(str(path), pagesize=options.page_size)
    if options.is_large_invoice:
        _draw_large_transaction(pdf, title, company, normalized_header, lines, totals, options, party_label, ship_to)
    else:
        _draw_standard_transaction(pdf, title, company, normalized_header, lines, totals, options, party_label, ship_to)
    pdf.save()


def write_voucher_pdf(
    path: Path,
    title: str,
    company: dict[str, Any],
    entry: dict[str, Any],
    *,
    voucher_type: str = "receipt",
    party_label: str = "Party",
    prepared_by: str = "",
    db_path: Path | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized_entry = _normalize_voucher_entry(entry or {}, voucher_type)
    options = resolve_print_options(company, voucher_type, db_path)
    pdf = NumberedCanvas(str(path), pagesize=options.page_size)
    _draw_voucher(pdf, title, company, normalized_entry, party_label, prepared_by, options)
    pdf.save()


def _normalize_voucher_entry(entry: dict[str, Any], voucher_type: str) -> dict[str, Any]:
    """Normalize common voucher entry keys from legacy payloads.

    Ensures `doc_no`, `entry_date`, `party_name`, `amount`, `mode`, `status`,
    `notes` are present using common legacy aliases.
    """
    normalized = dict(entry or {})
    normalized.setdefault("doc_no", normalized.get("doc_no") or normalized.get("voucher_no") or normalized.get("no") or "")
    normalized.setdefault("entry_date", normalized.get("entry_date") or normalized.get("date") or normalized.get("voucher_date") or "")
    # party/supplier/customer naming
    normalized.setdefault("party_name", normalized.get("party_name") or normalized.get("party") or normalized.get("paid_to") or normalized.get("received_from") or "")
    normalized.setdefault("amount", normalized.get("amount") or normalized.get("total") or normalized.get("grand_total") or 0)
    normalized.setdefault("mode", normalized.get("mode") or normalized.get("pay_mode") or normalized.get("payment") or "")
    normalized.setdefault("status", normalized.get("status") or "Active")
    normalized.setdefault("notes", normalized.get("notes") or normalized.get("narration") or normalized.get("remarks") or "")
    normalized.setdefault("employee", normalized.get("employee") or normalized.get("prepared_by") or "")
    normalized.setdefault(
        "reference",
        normalized.get("reference")
        or normalized.get("ref_no")
        or normalized.get("bank_reference")
        or normalized.get("transaction_id")
        or normalized.get("upi_ref")
        or "",
    )
    normalized.setdefault(
        "instrument_no",
        normalized.get("instrument_no")
        or normalized.get("cheque_no")
        or normalized.get("bank_reference")
        or normalized.get("transaction_id")
        or normalized.get("upi_ref")
        or "",
    )
    return normalized


def document_share_caption(
    title: str,
    doc_no: str,
    party_name: str,
    amount: Any,
    company: dict[str, Any],
    pdf_path: Path | None = None,
) -> str:
    company_name = _company_name(company)
    lines = [
        f"{title}: {doc_no}",
        f"Party: {party_name or '-'}",
        f"Amount: Rs {_money_plain(amount)}",
        f"- {company_name}",
    ]
    if pdf_path:
        lines.append(f"PDF: {pdf_path}")
    return "\n".join(lines)


def _normalize_report_template_code(title: str) -> str:
    code = str(title or "").strip().lower()
    code = re.sub(r"[^a-z0-9]+", "_", code)
    return code.strip("_")


def _report_template_row(title: str, db_path: Path | None) -> dict[str, Any]:
    if not title:
        return {}
    normalized_code = _normalize_report_template_code(title)
    if normalized_code:
        row = _template_row_by_code(normalized_code, "report", db_path)
        if row:
            return row
    db = Path(db_path) if db_path else _default_db_path()
    if not db.exists():
        return {}
    try:
        with sqlite3.connect(db) as conn:
            conn.row_factory = sqlite3.Row
            orientation_col = _print_template_orientation_select(conn)
            row = conn.execute(
                f"""
                SELECT pt.template_code,pt.template_name,pt.document_type,pt.paper_size,{orientation_col},pt.print_mode,
                       tf.family_code,tf.family_name,tf.business_type,tf.default_paper_size,tf.default_print_mode
                FROM print_templates pt
                LEFT JOIN print_template_families tf ON tf.id=pt.family_id
                WHERE LOWER(pt.document_type)=LOWER(?) AND LOWER(pt.template_name)=LOWER(?) AND COALESCE(pt.is_active,1)=1
                LIMIT 1
                """,
                ("report", str(title).strip().lower()),
            ).fetchone()
            return dict(row) if row else {}
    except sqlite3.Error:
        return {}


def _default_report_template_row(db_path: Path | None) -> dict[str, Any]:
    db = Path(db_path) if db_path else _default_db_path()
    if not db.exists():
        return {}
    try:
        with sqlite3.connect(db) as conn:
            conn.row_factory = sqlite3.Row
            orientation_col = _print_template_orientation_select(conn)
            row = conn.execute(
                f"""
                SELECT pt.template_code,pt.template_name,pt.document_type,pt.paper_size,{orientation_col},pt.print_mode,
                       tf.family_code,tf.family_name,tf.business_type,tf.default_paper_size,tf.default_print_mode
                FROM print_templates pt
                LEFT JOIN print_template_families tf ON tf.id=pt.family_id
                WHERE LOWER(pt.document_type)=LOWER(?)
                  AND LOWER(tf.family_code)=LOWER(?)
                  AND COALESCE(pt.is_active,1)=1
                ORDER BY COALESCE(pt.is_default,0) DESC, pt.id
                LIMIT 1
                """,
                ("report", "common_report_family"),
            ).fetchone()
            return dict(row) if row else {}
    except sqlite3.Error:
        return {}


def _resolve_report_print_options(
    company: dict[str, Any],
    title: str,
    db_path: Path | None = None,
    paper_size: str = "a4",
    orientation: str = "landscape",
    document_type: str | None = None,
) -> PrintOptions:
    if document_type and _norm(document_type) != "report":
        return resolve_print_options(company, document_type, db_path)
    template = _report_template_row(title, db_path)
    # (no special-case list-report handling here) -- use template/fallback defaults
    if template:
        paper_size = _norm(template.get("paper_size") or template.get("default_paper_size") or paper_size)
        if paper_size in {"thermal_58mm", "thermal_58"}:
            paper_size = "thermal_80"
        if paper_size == "thermal_80mm":
            paper_size = "thermal_80"
        orientation = _norm(str(template.get("orientation") or ""))
        if not orientation:
            orientation = "landscape" if paper_size in {"a2", "a3"} else "portrait"
        return PrintOptions(
            document_type="report",
            template_code=str(template.get("template_code") or ""),
            template_name=str(template.get("template_name") or ""),
            family_code=str(template.get("family_code") or ""),
            business_type=str(template.get("business_type") or ""),
            paper_size=paper_size or "a4",
            orientation=orientation or "portrait",
            print_mode=str(template.get("print_mode") or template.get("default_print_mode") or "laser"),
        )
    fallback = _default_report_template_row(db_path)
    if fallback:
        return PrintOptions(
            document_type="report",
            template_code=str(fallback.get("template_code") or ""),
            template_name=str(fallback.get("template_name") or ""),
            family_code=str(fallback.get("family_code") or ""),
            business_type=str(fallback.get("business_type") or ""),
            paper_size=_norm(paper_size) or "a4",
            orientation=_norm(orientation) or "portrait",
            print_mode=str(fallback.get("print_mode") or fallback.get("default_print_mode") or "laser"),
        )
    return PrintOptions(document_type="report", paper_size=_norm(paper_size) or "a4", orientation=_norm(orientation) or "portrait")


def write_report_pdf(
    path: Path,
    title: str,
    company: dict[str, Any],
    rows: list[dict[str, Any]],
    filters: dict[str, Any] | None = None,
    paper_size: str = "a4",
    orientation: str = "landscape",
    db_path: Path | None = None,
    document_type: str | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    filter_text = ""
    if filters:
        filter_text = " | ".join(f"{_text(key)}: {_text(value)}" for key, value in filters.items() if str(value).strip())
    options = _resolve_report_print_options(company, title, db_path, paper_size, orientation, document_type)
    doc = SimpleDocTemplate(
        str(path),
        pagesize=options.page_size,
        rightMargin=9 * mm,
        leftMargin=9 * mm,
        topMargin=39 * mm,
        bottomMargin=13 * mm,
    )
    story = []
    cell_style = ParagraphStyle("ReportCell", parent=styles["Normal"], fontName="Helvetica", fontSize=6.8, leading=8)
    header_style = ParagraphStyle("ReportHeader", parent=cell_style, fontName="Helvetica-Bold", textColor=colors.white)
    story.append(Spacer(1, 1 * mm))

    if not rows:
        rows = [{"Status": "No rows found"}]
    headers = list(rows[0].keys())[:12]
    table_rows = [[Paragraph(_text(header).replace("_", " ").title(), header_style) for header in headers]]
    for row in rows[:1000]:
        table_rows.append([Paragraph(_text(row.get(header, "")), cell_style) for header in headers])

    page_width = doc.pagesize[0] - (18 * mm)
    first_width = 38 * mm if len(headers) > 1 else page_width
    remaining_width = max(page_width - first_width, 40 * mm)
    col_widths = [first_width] + [remaining_width / max(len(headers) - 1, 1)] * (len(headers) - 1)
    report_table = Table(table_rows, colWidths=col_widths, repeatRows=1)
    report_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(report_table)
    header_title = _text(title)
    header_filters = _text(filter_text)
    generated_at = f"Generated {datetime.now():%d-%m-%Y %I:%M %p}"

    def on_page(pdf: canvas.Canvas, document: SimpleDocTemplate) -> None:
        _draw_report_page_header(pdf, document, header_title, company, header_filters, generated_at)

    # No list-specific GST spacer inserted here; report layout follows resolved template/fallback

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page, canvasmaker=NumberedCanvas)


def write_statement_pdf(
    path: Path,
    title: str,
    company: dict[str, Any],
    statement: dict[str, Any],
    *,
    db_path: Path | None = None,
) -> None:
    """Write locked two-sided accounting statements from prepared statement data."""
    path.parent.mkdir(parents=True, exist_ok=True)
    options = PrintOptions(document_type="accounting_statement", paper_size="a4", orientation="portrait")
    pdf = NumberedCanvas(str(path), pagesize=options.page_size)
    _draw_statement_pdf(pdf, title, company, statement or {}, options)
    pdf.save()


def _draw_statement_pdf(
    pdf: canvas.Canvas,
    title: str,
    company: dict[str, Any],
    statement: dict[str, Any],
    options: PrintOptions,
) -> None:
    width, height = options.page_size
    margin = 9 * mm
    content_width = width - (2 * margin)
    gap = 6
    column_width = (content_width - gap) / 2
    left_rows = _statement_pdf_rows(statement.get("left_groups") or [])
    right_rows = _statement_pdf_rows(statement.get("right_groups") or [])
    page_index = 1
    left_index = 0
    right_index = 0
    rendered_statement_page = False

    while left_index < len(left_rows) or right_index < len(right_rows) or not rendered_statement_page:
        body = _draw_statement_page_header(pdf, width, height, margin, title, company, statement, page_index)
        row_top, bottom_y = body
        left_next, left_y = _draw_statement_rows(pdf, margin, row_top, column_width, left_rows, left_index, bottom_y)
        right_next, right_y = _draw_statement_rows(pdf, margin + column_width + gap, row_top, column_width, right_rows, right_index, bottom_y)
        rendered_statement_page = True
        final_page = left_next >= len(left_rows) and right_next >= len(right_rows)
        if final_page:
            total_y = min(left_y, right_y) - 3
            _draw_statement_total_row(pdf, margin, total_y, column_width, "Total", statement.get("left_total"))
            _draw_statement_total_row(pdf, margin + column_width + gap, total_y, column_width, "Total", statement.get("right_total"))
            _draw_statement_footer(pdf, width, margin)
            break
        _draw_statement_footer(pdf, width, margin)
        pdf.showPage()
        page_index += 1
        left_index, right_index = left_next, right_next

    controls = list(statement.get("controls") or [])
    if controls:
        pdf.showPage()
        page_index += 1
        _draw_statement_controls(pdf, width, height, margin, title, company, statement, controls, page_index)


def _draw_statement_page_header(
    pdf: canvas.Canvas,
    width: float,
    height: float,
    margin: float,
    title: str,
    company: dict[str, Any],
    statement: dict[str, Any],
    page_index: int,
) -> tuple[float, float]:
    content_width = width - (2 * margin)
    top = height - margin
    bottom = margin + 20
    _draw_box(pdf, margin, margin, content_width, height - (2 * margin), "#FFFFFF", "#0F172A", radius=6, stroke_width=0.85)
    logo = _resolve_asset(company.get("logo_path"))
    if logo:
        _draw_image(pdf, logo, margin + 8, top - 52, 42, 42)
    _section_company_center_text(pdf, company, margin, top, content_width)
    strip_y = top - 76
    _section_title_strip(pdf, margin + 5, strip_y, content_width - 10, str(statement.get("title") or title).upper(), size=7.6, title_left=8)
    _right_text(pdf, _text(statement.get("period") or ""), width - margin - 12, strip_y + 4, size=6.6, color="#475569")
    caption = "Business Report" if page_index == 1 else "Business Report - Continued"
    _center_text(pdf, caption, margin, strip_y - 15, content_width, font="Helvetica-Bold", size=8, color="#0F172A")

    frame_top = strip_y - 26
    header_h = 22
    gap = 6
    column_width = (content_width - gap) / 2
    headings = [
        str(statement.get("left_heading") or "Particulars"),
        str(statement.get("right_heading") or "Particulars"),
    ]
    for index, heading in enumerate(headings):
        x = margin + index * (column_width + gap)
        _draw_box(pdf, x, frame_top - header_h, column_width, header_h, "#EAF2FF", "#94A3B8", stroke_width=0.5)
        _draw_text(pdf, heading, x + 6, frame_top - 14, font="Helvetica-Bold", size=7.4, color="#0F172A")
        _right_text(pdf, "Amount (Rs)", x + column_width - 6, frame_top - 14, font="Helvetica-Bold", size=7.4, color="#0F172A")
    return frame_top - header_h, bottom


def _statement_pdf_rows(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for group in groups:
        rows.append({"kind": "group", "label": str(group.get("label") or ""), "amount": group.get("amount")})
        details = list(group.get("details") or [])
        if group.get("open") and details:
            for detail in details:
                rows.append(
                    {
                        "kind": "detail",
                        "label": str(detail.get("ledger") or ""),
                        "group_name": str(detail.get("group_name") or ""),
                        "amount": detail.get("amount"),
                    }
                )
        elif group.get("note"):
            rows.append({"kind": "note", "label": str(group.get("note") or ""), "amount": ""})
    return rows


def _draw_statement_rows(
    pdf: canvas.Canvas,
    x: float,
    top_y: float,
    width: float,
    rows: list[dict[str, Any]],
    start_index: int,
    bottom_y: float,
) -> tuple[int, float]:
    y = top_y
    index = start_index
    while index < len(rows):
        row = rows[index]
        row_h = 16 if row.get("kind") == "group" else 13
        if y - row_h < bottom_y:
            break
        fill = "#FFFFFF" if index % 2 else "#F8FAFC"
        pdf.setFillColor(colors.HexColor(fill))
        pdf.rect(x, y - row_h, width, row_h, stroke=0, fill=1)
        pdf.setStrokeColor(colors.HexColor("#CBD5E1"))
        pdf.setLineWidth(0.35)
        pdf.line(x, y - row_h, x + width, y - row_h)
        kind = str(row.get("kind") or "")
        if kind == "group":
            _draw_text(pdf, _fit_text(pdf, row.get("label") or "", width - 86, "Helvetica-Bold", 7.0), x + 6, y - 10.5, font="Helvetica-Bold", size=7.0, color="#0F172A")
            _right_text(pdf, _money_plain(row.get("amount")), x + width - 6, y - 10.5, font="Helvetica-Bold", size=7.0, color="#0F172A")
        elif kind == "note":
            _draw_text(pdf, _fit_text(pdf, row.get("label") or "", width - 12, "Helvetica-Oblique", 6.1), x + 18, y - 9.3, font="Helvetica-Oblique", size=6.1, color="#64748B")
        else:
            label = str(row.get("label") or "")
            group_name = str(row.get("group_name") or "")
            if group_name:
                label = f"{label} ({group_name})"
            _draw_text(pdf, _fit_text(pdf, label, width - 92, "Helvetica", 6.3), x + 18, y - 9.4, size=6.3, color="#334155")
            _right_text(pdf, _money_plain(row.get("amount")), x + width - 6, y - 9.4, size=6.3, color="#334155")
        y -= row_h
        index += 1
    return index, y


def _draw_statement_total_row(pdf: canvas.Canvas, x: float, y: float, width: float, label: str, amount: Any) -> None:
    _draw_box(pdf, x, y - 18, width, 18, "#EAF2FF", "#64748B", stroke_width=0.65)
    _draw_text(pdf, label, x + 6, y - 12, font="Helvetica-Bold", size=7.4, color="#0F172A")
    _right_text(pdf, _money_plain(amount), x + width - 6, y - 12, font="Helvetica-Bold", size=7.4, color="#0F172A")


def _draw_statement_controls(
    pdf: canvas.Canvas,
    width: float,
    height: float,
    margin: float,
    title: str,
    company: dict[str, Any],
    statement: dict[str, Any],
    controls: list[dict[str, Any]],
    page_index: int,
) -> None:
    content_width = width - (2 * margin)
    top = height - margin
    bottom = margin + 20
    _draw_box(pdf, margin, margin, content_width, height - (2 * margin), "#FFFFFF", "#0F172A", radius=6, stroke_width=0.85)
    _section_company_center_text(pdf, company, margin, top, content_width)
    strip_y = top - 76
    support_title = str(statement.get("support_title") or "Supporting Analysis")
    _section_title_strip(pdf, margin + 5, strip_y, content_width - 10, f"{str(statement.get('title') or title).upper()} - {support_title.upper()}", size=7.1, title_left=8)
    y = strip_y - 28
    col_widths = [content_width * 0.34, content_width * 0.45, content_width * 0.21]
    headers = ["Particulars", "Details", "Amount (Rs)"]
    _draw_item_table_header(pdf, margin + 5, y, col_widths, headers, 16)
    y -= 16
    for row in controls:
        if y - 15 < bottom:
            _draw_statement_footer(pdf, width, margin)
            pdf.showPage()
            page_index += 1
            _draw_box(pdf, margin, margin, content_width, height - (2 * margin), "#FFFFFF", "#0F172A", radius=6, stroke_width=0.85)
            _section_company_center_text(pdf, company, margin, top, content_width)
            _section_title_strip(pdf, margin + 5, strip_y, content_width - 10, f"{support_title.upper()} - CONTINUED", size=7.1, title_left=8)
            y = strip_y - 28
            _draw_item_table_header(pdf, margin + 5, y, col_widths, headers, 16)
            y -= 16
        values = [
            str(row.get("label") or ""),
            str(row.get("group_name") or ""),
            _money_plain(row.get("amount")),
        ]
        _draw_mini_row(pdf, margin + 5, y, col_widths, values)
        y -= 12
    _draw_statement_footer(pdf, width, margin)


def _draw_statement_footer(pdf: canvas.Canvas, width: float, margin: float) -> None:
    logo = _resolve_asset("assets/PRM_SoftSolutions.jpg", logo=True)
    y = margin + 10
    if logo:
        _draw_image(pdf, logo, margin + 4, y - 2, 12, 12)
    _center_text(pdf, f"Copyright (c) {datetime.now():%Y} PRM Software Solutions. All rights reserved.", 0, y, width, size=6.2, color="#475569")


def _draw_report_page_header(
    pdf: canvas.Canvas,
    document: SimpleDocTemplate,
    title: str,
    company: dict[str, Any],
    filters: str,
    generated_at: str,
) -> None:
    width, height = document.pagesize
    margin = 9 * mm
    content_width = width - (2 * margin)
    top = height - 6 * mm
    header_height = 31 * mm
    bottom = top - header_height
    _draw_box(pdf, margin, bottom, content_width, header_height, "#FFFFFF", "#CBD5E1", radius=4, stroke_width=0.65)
    # draw header only once per page to avoid duplicates
    if not getattr(pdf, "_header_drawn", False):
        logo = _resolve_asset(company.get("logo_path"))
        if logo:
            _draw_image(pdf, logo, margin + 6, top - 23 * mm, 18 * mm, 18 * mm)
        _section_company_center_text(pdf, company, margin, top, content_width)
        try:
            pdf._header_drawn = True
        except Exception:
            pass
    strip_y = bottom + 4 * mm
    pdf.setFillColor(colors.HexColor("#DFF4FF"))
    pdf.rect(margin + 4, strip_y, content_width - 8, 12, stroke=0, fill=1)
    _section_title_strip(pdf, margin + 4, strip_y, content_width - 8, title.upper(), font="Helvetica-Bold", size=7.2, title_left=8)
    _right_text(pdf, generated_at, width - margin - 8, strip_y + 4, font="Helvetica", size=6.2, color="#475569")
    if filters:
        _draw_text(pdf, _fit_text(pdf, filters, content_width - 16, "Helvetica", 5.8), margin + 8, strip_y - 6, size=5.8, color="#64748B")
    _draw_page_footer(pdf, width, margin, document.page)


def write_template_preview_pdf(
    path: Path,
    company: dict[str, Any],
    template: dict[str, Any],
) -> None:
    sample_rows = [
        {"Field": "Template Code", "Value": template.get("template_code", "")},
        {"Field": "Template Name", "Value": template.get("template_name", "")},
        {"Field": "Document Type", "Value": template.get("document_type", "")},
        {"Field": "Paper Size", "Value": template.get("paper_size", "")},
        {"Field": "Print Mode", "Value": template.get("print_mode", "")},
        {"Field": "Sample Item", "Value": "DEMO FMCG Product | Qty 2 | GST 18% | Rs 236.00"},
        {"Field": "Sample Total", "Value": "Taxable Rs 200.00 | GST Rs 36.00 | Grand Total Rs 236.00"},
        {"Field": "HTML Preview", "Value": str(template.get("html_template", ""))[:500]},
        {"Field": "CSS Preview", "Value": str(template.get("css_template", ""))[:500]},
    ]
    write_report_pdf(path, "Print Template Preview", company, sample_rows, {"Preview": "Desktop PDF"})


def _draw_large_transaction(
    pdf: canvas.Canvas,
    title: str,
    company: dict[str, Any],
    header: dict[str, Any],
    lines: list[dict[str, Any]],
    totals: dict[str, Any],
    options: PrintOptions,
    party_label: str,
    ship_to: str | None,
) -> None:
    width, height = options.page_size
    margin = 18 * mm
    table_header_height = 14
    row_height = 18
    final_reserve = 210
    page_row_bottom = margin + 38
    y = _draw_transaction_header(pdf, width, height, margin, title, company, header, options, party_label, ship_to)
    table_width = width - (2 * margin)
    columns = _scaled_columns(
        [28, 420, 66, 56, 58, 70, 70, 60, 78, 120, 65, 132],
        table_width,
    )
    headers = ["#", "ITEM DESCRIPTION", "HSN", "QTY", "UNIT", "MRP", "RATE", "SCH", "DISC", "TAXABLE", "GST %", "AMOUNT"]
    y = _draw_item_table_header(pdf, margin, y, columns, headers, table_header_height)
    page_index = 1
    for index, row in enumerate(lines, start=1):
        if y - row_height < page_row_bottom:
            _draw_continue_marker(pdf, margin, margin, table_width, page_index)
            _draw_page_footer(pdf, width, margin, page_index)
            pdf.showPage()
            page_index += 1
            y = _draw_transaction_header(pdf, width, height, margin, title, company, header, options, party_label, ship_to, continued=True)
            y = _draw_item_table_header(pdf, margin, y, columns, headers, table_header_height)
        y = _draw_item_row(pdf, margin, y, columns, index, row, row_height)

    total_values = ["", "TOTAL", "", _qty(sum(float(r.get("qty") or 0) for r in lines)), "", "", "", _qty(sum(float(r.get("free") or r.get("scheme") or 0) for r in lines)), _money_plain(totals.get("discount")), _money_plain(totals.get("taxable")), "", _money_plain(totals.get("grand_total"))]
    if y - table_header_height - final_reserve < margin + 18:
        _draw_continue_marker(pdf, margin, margin, table_width, page_index)
        _draw_page_footer(pdf, width, margin, page_index)
        pdf.showPage()
        page_index += 1
        y = _draw_transaction_header(pdf, width, height, margin, title, company, header, options, party_label, ship_to, continued=True)
        y = _draw_item_table_header(pdf, margin, y, columns, headers, table_header_height)
    y = _draw_total_row(pdf, margin, y, columns, total_values, table_header_height)
    if y - final_reserve < margin + 18:
        _draw_page_footer(pdf, width, margin, page_index)
        pdf.showPage()
        page_index += 1
        y = _draw_transaction_header(pdf, width, height, margin, title, company, header, options, party_label, ship_to, continued=True)
    _draw_final_transaction_block(pdf, margin, y - 5, width - (2 * margin), company, lines, totals, options)
    _draw_page_footer(pdf, width, margin, page_index)


def _draw_standard_transaction(
    pdf: canvas.Canvas,
    title: str,
    company: dict[str, Any],
    header: dict[str, Any],
    lines: list[dict[str, Any]],
    totals: dict[str, Any],
    options: PrintOptions,
    party_label: str,
    ship_to: str | None,
) -> None:
    width, height = options.page_size
    margin = 48
    content_width = width - (2 * margin)
    top = height - 58
    bottom = 72
    page_index = 1
    row_height = 23
    total_height = 18
    page_row_bottom = bottom + 34
    final_reserve = 282
    y = _draw_sample_header(pdf, width, top, bottom, margin, content_width, title, company, header, ship_to)
    columns = _scaled_columns([18, 160, 36, 28, 34, 42, 42, 28, 48, 74, 36, 86], content_width)
    y = _draw_sample_item_header(pdf, margin, y, columns)
    for index, row in enumerate(lines, start=1):
        if y - row_height < page_row_bottom:
            _draw_continue_marker(pdf, margin, bottom, content_width, page_index)
            _draw_sample_footer_strip(pdf, width, bottom, page_index)
            pdf.showPage()
            page_index += 1
            y = _draw_sample_header(pdf, width, top, bottom, margin, content_width, title, company, header, ship_to, continued=True)
            y = _draw_sample_item_header(pdf, margin, y, columns)
        y = _draw_sample_item_row(pdf, margin, y, columns, index, row)
    total_values = [
        "",
        "TOTAL",
        "",
        _qty(sum(float(row.get("qty") or 0) for row in lines)),
        "",
        "",
        "",
        _qty(sum(float(row.get("free") or row.get("scheme") or 0) for row in lines)),
        _money_plain(totals.get("discount")),
        _money_plain(totals.get("taxable")),
        "",
        _money_plain(totals.get("grand_total")),
    ]
    if y - total_height - final_reserve < bottom:
        _draw_continue_marker(pdf, margin, bottom, content_width, page_index)
        _draw_sample_footer_strip(pdf, width, bottom, page_index)
        pdf.showPage()
        page_index += 1
        y = _draw_sample_header(pdf, width, top, bottom, margin, content_width, title, company, header, ship_to, continued=True)
        y = _draw_sample_item_header(pdf, margin, y, columns)
    y = _draw_sample_total_row(pdf, margin, y, columns, total_values)
    if y - 222 < bottom:
        _draw_sample_footer_strip(pdf, width, bottom, page_index)
        pdf.showPage()
        page_index += 1
        y = _draw_sample_header(pdf, width, top, bottom, margin, content_width, title, company, header, ship_to, continued=True)
    final_top = min(y - 5, bottom + 286)
    _draw_sample_final_block(pdf, margin, final_top, content_width, company, lines, totals)
    _draw_sample_footer_strip(pdf, width, bottom, page_index)


def _draw_sample_header(
    pdf: canvas.Canvas,
    page_width: float,
    top: float,
    bottom: float,
    x: float,
    width: float,
    title: str,
    company: dict[str, Any],
    header: dict[str, Any],
    ship_to: str | None,
    *,
    continued: bool = False,
) -> float:
    outer_height = top - bottom
    _draw_box(pdf, x, bottom, width, outer_height, "#FFFFFF", "#0F172A", radius=7, stroke_width=1.0)
    pdf.setFillColor(colors.HexColor("#08204A"))
    pdf.rect(x, top - 23, width, 5, stroke=0, fill=1)
    # draw company header only once per page
    if not getattr(pdf, "_header_drawn", False):
        logo = _resolve_asset(company.get("logo_path"))
        if logo:
            _draw_box(pdf, x + 6, top - 86, 62, 62, "#FFFFFF", "#CBD5E1", radius=5)
            _draw_image(pdf, logo, x + 11, top - 81, 52, 52)
        _section_company_center_text(pdf, company, x, top, width)
        try:
            pdf._header_drawn = True
        except Exception:
            pass
    strip_y = top - 102
    pdf.setFillColor(colors.HexColor("#DFF4FF"))
    _section_title_strip(pdf, x, strip_y, width, title.upper() + (" - CONTINUED" if continued else ""), size=6.7, title_left=4)

    party_top = strip_y - 4
    party_h = 124
    left_w = width * 0.45
    mid_w = width * 0.35
    pay_w = width - left_w - mid_w
    _draw_sample_party_block(pdf, x + 4, party_top, left_w - 8, party_h, "BILL TO", _party_lines(header, "Bill To"), size=9.5)
    _draw_sample_party_block(pdf, x + left_w + 4, party_top, mid_w - 8, party_h, "SHIP TO", _ship_lines(header, ship_to), size=9.2)
    _draw_sample_payment_block(pdf, x + left_w + mid_w + 4, party_top, pay_w - 8, party_h, company)
    return party_top - party_h - 3


def _draw_sample_party_block(pdf: canvas.Canvas, x: float, top: float, width: float, height: float, label: str, values: list[str], *, size: float) -> None:
    _draw_text(pdf, label, x, top - 12, font="Helvetica-Bold", size=9.2, color="#0B2A5B")
    y = top - 26
    for index, value in enumerate([v for v in values if str(v).strip()][:8]):
        if ":" in value:
            key, rest = value.split(":", 1)
            if rest.strip():
                _draw_text(pdf, f"{key}:", x, y, font="Helvetica-Bold", size=size, color="#111827")
                _draw_wrapped(pdf, rest.strip(), x + min(72, width * 0.34), y, width - min(72, width * 0.34), size=size, leading=10, max_lines=2)
            else:
                _draw_text(pdf, f"{key}:", x, y, font="Helvetica-Bold", size=size, color="#111827")
        else:
            _draw_wrapped(pdf, value, x, y, width, size=size, leading=10, max_lines=2)
        y -= 12 if index < 5 else 10


def _draw_sample_payment_block(pdf: canvas.Canvas, x: float, top: float, width: float, height: float, company: dict[str, Any]) -> None:
    _center_text(pdf, "PAYMENT", x, top - 12, width, font="Helvetica-Bold", size=9.2, color="#0B2A5B")
    qr = _resolve_asset(company.get("payment_qr_path"))
    if qr:
        qr_size = min(width - 16, height - 26, 80)
        _draw_box(pdf, x + (width / 2) - (qr_size / 2) - 4, top - 89, qr_size + 8, qr_size + 8, "#FFFFFF", "#0F172A", stroke_width=0.7)
        _draw_image(pdf, qr, x + (width / 2) - (qr_size / 2), top - 85, qr_size, qr_size)


def _draw_sample_item_header(pdf: canvas.Canvas, x: float, y: float, columns: list[float]) -> float:
    labels = ["#", "ITEM DESCRIPTION", "HSN", "QTY", "UNIT", "MRP", "RATE", "SCH", "DISC", "TAXABLE", "GST", "AMOUNT"]
    pdf.setFillColor(colors.HexColor("#EAF2FF"))
    pdf.rect(x, y - 17, sum(columns), 17, stroke=0, fill=1)
    cursor = x
    for width, label in zip(columns, labels):
        pdf.setStrokeColor(colors.HexColor("#0F172A"))
        pdf.setLineWidth(0.65)
        pdf.rect(cursor, y - 17, width, 17, stroke=1, fill=0)
        _center_text(pdf, label, cursor, y - 12, width, font="Helvetica-Bold", size=7.2, color="#111827")
        cursor += width
    return y - 17


def _draw_sample_item_row(pdf: canvas.Canvas, x: float, y: float, columns: list[float], index: int, row: dict[str, Any]) -> float:
    height = 23
    values = [
        str(index),
        str(row.get("item") or row.get("item_name") or ""),
        str(row.get("hsn") or ""),
        _qty(row.get("qty")),
        str(row.get("unit") or ""),
        _money_plain(row.get("mrp")),
        _money_plain(row.get("rate")),
        _qty(row.get("free") or row.get("scheme")),
        _money_plain(row.get("disc") or row.get("discount")),
        _money_plain(row.get("taxable")),
        f"{_qty(row.get('gst'))}%",
        _money_plain(row.get("amount") or row.get("total")),
    ]
    cursor = x
    for col, (width, value) in enumerate(zip(columns, values)):
        pdf.setStrokeColor(colors.HexColor("#0F172A"))
        pdf.setLineWidth(0.55)
        pdf.rect(cursor, y - height, width, height, stroke=1, fill=0)
        if col == 1:
            main, sub = _split_item(value)
            _draw_text(pdf, _fit_text(pdf, main.upper(), width - 4, "Helvetica-Bold", 7.1), cursor + 2, y - 8, font="Helvetica-Bold", size=7.1, color="#111827")
            if sub:
                _draw_text(pdf, _fit_text(pdf, sub, width - 4, "Helvetica", 6.5), cursor + 2, y - 18, size=6.5, color="#64748B")
        elif col in {3, 5, 6, 7, 8, 9, 11}:
            _right_text(pdf, value, cursor + width - 2, y - 14, size=7, color="#111827")
        else:
            _center_text(pdf, value, cursor, y - 14, width, size=7, color="#111827")
        cursor += width
    return y - height


def _draw_sample_total_row(pdf: canvas.Canvas, x: float, y: float, columns: list[float], values: list[str]) -> float:
    height = 18
    cursor = x
    for col, (width, value) in enumerate(zip(columns, values)):
        pdf.setFillColor(colors.HexColor("#F8FAFC"))
        pdf.setStrokeColor(colors.HexColor("#0F172A"))
        pdf.setLineWidth(0.65)
        pdf.rect(cursor, y - height, width, height, stroke=1, fill=1)
        if col == 1:
            _draw_text(pdf, "TOTAL", cursor + 2, y - 12, font="Helvetica-Bold", size=8.2, color="#111827")
        elif value:
            _right_text(pdf, value, cursor + width - 2, y - 12, font="Helvetica-Bold", size=6.6, color="#111827")
        cursor += width
    return y - height


def _draw_sample_final_block(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    company: dict[str, Any],
    lines: list[dict[str, Any]],
    totals: dict[str, Any],
) -> None:
    summary = _gst_summary(lines)
    summary_h = max(132, 66 + (17 * (len(summary) + 1)))
    grand_w = 112
    gap = 4
    tax_w = width - grand_w - gap
    _draw_box(pdf, x + 4, y - summary_h, tax_w - 4, summary_h, "#FFFFFF", "#CBD5E1", radius=4, stroke_width=0.8)
    _center_text(pdf, "GST Summary", x + 4, y - 17, tax_w - 4, font="Helvetica-Bold", size=8.4, color="#111827")
    cols = _scaled_columns([58, 80, 40, 80, 50, 50, 50, 82], tax_w - 10)
    gy = y - 43
    _draw_sample_gst_header(pdf, x + 4, gy, cols)
    gy -= 17
    totals_row = {"taxable": 0.0, "free": 0.0, "disc": 0.0, "cgst": 0.0, "sgst": 0.0, "igst": 0.0, "gst": 0.0}
    for rate, values in summary.items():
        for key in totals_row:
            totals_row[key] += values.get(key, 0.0)
        _draw_sample_gst_row(pdf, x + 4, gy, cols, [
            f"GST {_money_plain(rate).rstrip('0').rstrip('.')}",
            _money_plain(values.get("taxable")),
            _qty(values.get("free")),
            _money_plain(values.get("disc")),
            _money_plain(values.get("cgst")),
            _money_plain(values.get("sgst")),
            _money_plain(values.get("igst")),
            _money_plain(values.get("gst")),
        ])
        gy -= 17
    _draw_sample_gst_row(pdf, x + 4, gy, cols, [
        "TOTAL",
        _money_plain(totals_row["taxable"]),
        _qty(totals_row["free"]),
        _money_plain(totals_row["disc"]),
        _money_plain(totals_row["cgst"]),
        _money_plain(totals_row["sgst"]),
        _money_plain(totals_row["igst"]),
        _money_plain(totals_row["gst"]),
    ], bold=True)

    gx = x + tax_w + gap
    _draw_box(pdf, gx, y - summary_h, grand_w, summary_h, "#FFFFFF", "#CBD5E1", radius=4, stroke_width=0.8)
    amount_rows = [
        ("TAXABLE - TOTAL", totals.get("taxable")),
        ("CGST", totals.get("cgst")),
        ("SGST", totals.get("sgst")),
        ("IGST", totals.get("igst")),
        ("ROUND\nOFF", totals.get("round_off")),
        ("GRAND\nTOTAL", totals.get("grand_total")),
    ]
    row_h = summary_h / len(amount_rows)
    row_y = y
    for label, value in amount_rows:
        row_y -= row_h
        pdf.setStrokeColor(colors.HexColor("#CBD5E1"))
        pdf.setLineWidth(0.55)
        pdf.rect(gx, row_y, grand_w, row_h, stroke=1, fill=0)
        label_w = 48
        if "GRAND" in label:
            pdf.setFillColor(colors.HexColor("#DCFCE7"))
            pdf.rect(gx + label_w, row_y + 1, grand_w - label_w - 1, row_h - 2, stroke=0, fill=1)
        for offset, part in enumerate(label.split("\n")):
            _draw_text(pdf, part, gx + 4, row_y + row_h - 9 - (offset * 10), font="Helvetica-Bold", size=8.2, color="#475569")
        _right_text(pdf, f"Rs {_money_plain(value)}" if "GRAND" in label else _money_plain(value), gx + grand_w - 4, row_y + (row_h / 2) - 3, font="Helvetica-Bold" if "GRAND" in label else "Helvetica", size=11 if "GRAND" in label else 7, color="#065F46" if "GRAND" in label else "#111827")

    words_y = y - summary_h - 5
    _draw_box(pdf, x + 4, words_y - 16, width - 8, 16, "#FFFFFF", "#0F172A", radius=2, stroke_width=0.7)
    _draw_text(pdf, f"In Words: {amount_in_words(totals.get('grand_total'))}/-", x + 8, words_y - 11, font="Helvetica-Bold", size=7.2, color="#111827")
    footer_top = words_y - 18
    footer_h = 58
    _draw_box(pdf, x, footer_top - footer_h, width, footer_h, "#FFFFFF", "#0F172A", stroke_width=0.65)
    block_w = width / 3
    blocks = [
        ("Terms", "Order, quotation and challan workflow document. Stock and ledger update only on final bill/purchase entry."),
        ("Bank Details", str(company.get("bank") or "")),
        (_company_name(company), "Authorised Signature"),
    ]
    for idx, (label, value) in enumerate(blocks):
        bx = x + idx * block_w
        if idx > 0:
            pdf.setStrokeColor(colors.HexColor("#0F172A"))
            pdf.line(bx, footer_top - footer_h, bx, footer_top)
        if idx == 2:
            _center_text(pdf, label, bx, footer_top - 13, block_w, font="Helvetica-Bold", size=6.5, color="#111827")
            _center_text(pdf, value, bx, footer_top - 40, block_w, size=6.7, color="#111827")
        else:
            _draw_text(pdf, label, bx + 4, footer_top - 10, font="Helvetica-Bold", size=6.6, color="#111827")
            _draw_wrapped(pdf, value, bx + 4, footer_top - 20, block_w - 8, size=6.2, leading=8, max_lines=5)


def _draw_sample_gst_header(pdf: canvas.Canvas, x: float, y: float, columns: list[float]) -> None:
    labels = ["CLASS", "TAXABLE", "SCH", "DISC (RS)", "CGST", "SGST", "IGST", "GST TOTAL"]
    cursor = x
    for width, label in zip(columns, labels):
        pdf.setFillColor(colors.HexColor("#F8FAFC"))
        pdf.setStrokeColor(colors.HexColor("#CBD5E1"))
        pdf.rect(cursor, y - 16, width, 16, stroke=1, fill=1)
        _center_text(pdf, label, cursor, y - 11, width, font="Helvetica-Bold", size=6.4, color="#475569")
        cursor += width


def _draw_sample_gst_row(pdf: canvas.Canvas, x: float, y: float, columns: list[float], values: list[str], *, bold: bool = False) -> None:
    cursor = x
    for idx, (width, value) in enumerate(zip(columns, values)):
        pdf.setFillColor(colors.HexColor("#F8FAFC") if bold else colors.white)
        pdf.setStrokeColor(colors.HexColor("#CBD5E1"))
        pdf.rect(cursor, y - 16, width, 16, stroke=1, fill=1)
        font = "Helvetica-Bold" if bold else "Helvetica"
        if idx == 0:
            _draw_text(pdf, value, cursor + 4, y - 11, font=font, size=6.6, color="#475569" if bold else "#111827")
        else:
            _right_text(pdf, value, cursor + width - 4, y - 11, font=font, size=6.6, color="#475569" if bold else "#111827")
        cursor += width


def _draw_sample_footer_strip(pdf: canvas.Canvas, page_width: float, bottom: float, page_index: int) -> None:
    logo = _resolve_asset("assets/PRM_SoftSolutions.jpg", logo=True)
    y = bottom + 9
    if logo:
        _draw_image(pdf, logo, 54, y - 5, 18, 18)
    _center_text(pdf, f"Copyright (c) {datetime.now():%Y} PRM Software Solutions. All rights reserved.", 0, y, page_width, size=8, color="#111827")
    _right_text(pdf, f"Page {page_index}", page_width - 52, y - 1, size=5.5, color="#94A3B8")


def _draw_transaction_header(
    pdf: canvas.Canvas,
    width: float,
    height: float,
    margin: float,
    title: str,
    company: dict[str, Any],
    header: dict[str, Any],
    options: PrintOptions,
    party_label: str,
    ship_to: str | None,
    *,
    continued: bool = False,
) -> float:
    top = height - margin
    inner_width = width - (2 * margin)
    pdf.setStrokeColor(colors.HexColor("#0F172A"))
    pdf.setLineWidth(1.4)
    pdf.roundRect(margin, margin, inner_width, height - (2 * margin), 8, stroke=1, fill=0)
    pdf.setStrokeColor(colors.HexColor("#CBD5E1"))
    pdf.roundRect(margin + 6, margin + 8, inner_width - 12, height - (2 * margin) - 16, 5, stroke=1, fill=0)

    # draw company header only once per page
    if not getattr(pdf, "_header_drawn", False):
        logo = _resolve_asset(company.get("logo_path"))
        if logo:
            _draw_image(pdf, logo, margin + 12, top - 45, 45, 45)
        _section_company_center_text(pdf, company, margin, top, inner_width)
        try:
            pdf._header_drawn = True
        except Exception:
            pass

    strip_y = top - 55
    _section_title_strip(pdf, margin + 6, strip_y, inner_width - 12, title.upper() + (" - CONTINUED" if continued else ""), title_left=10)

    party_top = strip_y - 2
    party_height = 72 if options.is_large_invoice else 78
    box_widths = [0.44, 0.34, 0.22]
    x = margin + 6
    available = inner_width - 12
    bill = _party_lines(header, party_label)
    ship = _ship_lines(header, ship_to)
    payment = _payment_lines(header)
    payment_qr = _resolve_asset(company.get("payment_qr_path"))
    blocks = [(party_label.upper(), bill), ("SHIP TO", ship), ("PAYMENT", payment)]
    for idx, (label, values) in enumerate(blocks):
        bw = available * box_widths[idx]
        _draw_box(pdf, x, party_top - party_height, bw, party_height, "#FFFFFF", "#CBD5E1")
        if label == "PAYMENT" and payment_qr:
            qr_size = min(party_height - 12, bw - 12, 64)
            _draw_image(pdf, payment_qr, x + (bw / 2) - (qr_size / 2), party_top - ((party_height + qr_size) / 2), qr_size, qr_size)
        else:
            _section_party_block(pdf, label, values, x, party_top, bw, party_height)
        x += bw
    return party_top - party_height - 6


def _draw_final_transaction_block(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    company: dict[str, Any],
    lines: list[dict[str, Any]],
    totals: dict[str, Any],
    options: PrintOptions,
) -> None:
    large = options.is_large_invoice
    summary = _gst_summary(lines)
    summary_height = max(66 if large else 76, 46 + (12 * (len(summary) + 1)))
    grand_width = 122 if large else 118
    gap = 5
    tax_width = width - grand_width - gap
    _draw_box(pdf, x, y - summary_height, tax_width, summary_height, "#FFFFFF", "#CBD5E1")
    _center_text(pdf, "GST Summary", x, y - 12, tax_width, font="Helvetica-Bold", size=7, color="#0F172A")
    gst_cols = _scaled_columns([70, 105, 70, 105, 105, 105, 105, 120], tax_width - 10)
    gst_headers = ["CLASS", "TAXABLE", "SCH", "DISC (RS)", "CGST", "SGST", "IGST", "GST TOTAL"]
    gy = y - 25
    _draw_mini_header(pdf, x + 5, gy, gst_cols, gst_headers)
    gy -= 13
    totals_row = {"taxable": 0.0, "free": 0.0, "disc": 0.0, "cgst": 0.0, "sgst": 0.0, "igst": 0.0, "gst": 0.0}
    for rate, values in summary.items():
        for key in totals_row:
            totals_row[key] += values.get(key, 0.0)
        row = [
            f"GST {_qty(rate)}",
            _money_plain(values.get("taxable")),
            _qty(values.get("free")),
            _money_plain(values.get("disc")),
            _money_plain(values.get("cgst")),
            _money_plain(values.get("sgst")),
            _money_plain(values.get("igst")),
            _money_plain(values.get("gst")),
        ]
        _draw_mini_row(pdf, x + 5, gy, gst_cols, row)
        gy -= 12
    total_row = [
        "TOTAL",
        _money_plain(totals_row["taxable"]),
        _qty(totals_row["free"]),
        _money_plain(totals_row["disc"]),
        _money_plain(totals_row["cgst"]),
        _money_plain(totals_row["sgst"]),
        _money_plain(totals_row["igst"]),
        _money_plain(totals_row["gst"]),
    ]
    _draw_mini_row(pdf, x + 5, gy, gst_cols, total_row, bold=True)

    gx = x + tax_width + gap
    _draw_box(pdf, gx, y - summary_height, grand_width, summary_height, "#F8FAFC", "#CBD5E1")
    amount_rows = [
        ("TAXABLE TOTAL", totals.get("taxable")),
        ("CGST", totals.get("cgst")),
        ("SGST", totals.get("sgst")),
        ("IGST", totals.get("igst")),
        ("ROUND OFF", totals.get("round_off")),
        ("GRAND TOTAL", totals.get("grand_total")),
    ]
    row_y = y - 12
    for label, value in amount_rows:
        bold = label == "GRAND TOTAL"
        if bold:
            pdf.setFillColor(colors.HexColor("#DCFCE7"))
            pdf.rect(gx + 1, row_y - 8, grand_width - 2, 13, stroke=0, fill=1)
        _draw_text(pdf, label, gx + 5, row_y - 2, font="Helvetica-Bold", size=6.8, color="#475569")
        _right_text(pdf, f"Rs {_money_plain(value)}" if bold else _money_plain(value), gx + grand_width - 5, row_y - 2, font="Helvetica-Bold" if bold else "Helvetica", size=7.2 if bold else 6.8, color="#047857" if bold else "#0F172A")
        row_y -= 10

    words_y = y - summary_height - 10
    _draw_box(pdf, x, words_y - 16, width, 16, "#FFFFFF", "#CBD5E1")
    _draw_text(pdf, f"In Words: {amount_in_words(totals.get('grand_total'))}", x + 5, words_y - 10, font="Helvetica-Bold", size=6.6, color="#0F172A")

    footer_y = words_y - 20
    footer_height = 45 if large else 66
    block_w = width / 3
    footer_blocks = [
        ("Terms", "Goods once sold will not be taken back without approval. Subject to local jurisdiction."),
        ("Bank Details", str(company.get("bank") or "")),
        (_company_name(company), "Authorised Signature"),
    ]
    _draw_box(pdf, x, footer_y - footer_height, width, footer_height, "#FFFFFF", "#CBD5E1")
    for idx, (label, value) in enumerate(footer_blocks):
        bx = x + (idx * block_w)
        if idx > 0:
            pdf.setStrokeColor(colors.HexColor("#94A3B8"))
            pdf.line(bx, footer_y - footer_height, bx, footer_y)
        if idx == 2:
            _center_text(pdf, label, bx, footer_y - 12, block_w, font="Helvetica-Bold", size=6.1, color="#0F172A")
            _center_text(pdf, value, bx, footer_y - footer_height + 10, block_w, size=6.1, color="#0F172A")
        else:
            _draw_text(pdf, label, bx + 5, footer_y - 9, font="Helvetica-Bold", size=6.4, color="#0F172A")
            _draw_wrapped(pdf, value, bx + 5, footer_y - 19, block_w - 10, size=5.7, leading=7.2)


def _draw_voucher(
    pdf: canvas.Canvas,
    title: str,
    company: dict[str, Any],
    entry: dict[str, Any],
    party_label: str,
    prepared_by: str,
    options: PrintOptions,
) -> None:
    width, height = options.page_size
    margin = 12 * mm
    top = height - margin
    inner_width = width - (2 * margin)
    _draw_box(pdf, margin, margin, inner_width, height - (2 * margin), "#FFFFFF", "#0F172A", radius=8, stroke_width=1.2)
    logo = _resolve_asset(company.get("logo_path"))
    if logo:
        _draw_image(pdf, logo, margin + 12, top - 44, 40, 40)
    _center_text(pdf, _company_name(company).upper(), margin, top - 16, inner_width, font="Helvetica-Bold", size=12, color="#0F172A")
    _center_text(pdf, _company_address(company), margin, top - 31, inner_width, size=7.2, color="#475569")
    _center_text(pdf, _company_contact_line(company), margin, top - 43, inner_width, font="Helvetica-Bold", size=7.0, color="#475569")
    strip_y = top - 58
    pdf.setFillColor(colors.HexColor("#DFF4FF"))
    pdf.rect(margin + 6, strip_y, inner_width - 12, 14, stroke=0, fill=1)
    _draw_text(pdf, title.upper(), margin + 12, strip_y + 4, font="Helvetica-Bold", size=8, color="#0F172A")

    box_top = strip_y - 10
    block_w = (inner_width - 18) / 3
    party = str(entry.get("party_name") or entry.get("party") or "")
    amount = entry.get("amount")
    blocks = [
        (party_label, [party, f"Mode: {entry.get('mode') or ''}", f"Status: {entry.get('status') or 'Active'}"]),
        ("Voucher", [f"No: {entry.get('doc_no') or entry.get('no') or ''}", f"Date: {_date_text(entry.get('entry_date') or entry.get('date'))}", f"Prepared: {prepared_by or entry.get('employee') or 'Administrator'}"]),
        ("Amount", [f"Rs {_money_plain(amount)}", f"In Words: {amount_in_words(amount)}"]),
    ]
    for idx, (label, values) in enumerate(blocks):
        bx = margin + 6 + idx * (block_w + 3)
        detail_h = 88
        _draw_box(pdf, bx, box_top - detail_h, block_w, detail_h, "#F8FAFC", "#CBD5E1", radius=5)
        if label == "Voucher":
            _section_document_details(pdf, label, entry, bx, box_top, block_w)
        else:
            _section_party_block(pdf, label, values, bx, box_top, block_w, detail_h)

    narration_y = box_top - 104
    _draw_box(pdf, margin + 6, narration_y - 86, inner_width - 12, 86, "#FFFFFF", "#CBD5E1", radius=5)
    _draw_text(pdf, "Narration / Remarks", margin + 13, narration_y - 14, font="Helvetica-Bold", size=8, color="#0F172A")
    _draw_wrapped(pdf, str(entry.get("notes") or "No remarks"), margin + 13, narration_y - 30, inner_width - 26, size=7.5, leading=11)

    sign_y = narration_y - 105
    sign_w = (inner_width - 12) / 3
    sign_labels = [f"Prepared By\n{prepared_by or 'Administrator'}", "Receiver / Party Signature", "Authorised Signatory"]
    for idx, label in enumerate(sign_labels):
        sx = margin + 6 + idx * sign_w
        _draw_box(pdf, sx, sign_y - 62, sign_w, 62, "#FFFFFF", "#CBD5E1")
        lines = label.split("\n")
        _center_text(pdf, lines[0], sx, sign_y - 18, sign_w, font="Helvetica-Bold", size=7.4, color="#0F172A")
        if len(lines) > 1:
            _center_text(pdf, lines[1], sx, sign_y - 31, sign_w, size=7, color="#334155")
    _draw_page_footer(pdf, width, margin, 1)


def _draw_item_table_header(pdf: canvas.Canvas, x: float, y: float, columns: list[float], labels: list[str], height: float) -> float:
    pdf.setFillColor(colors.HexColor("#EAF2FF"))
    pdf.rect(x, y - height, sum(columns), height, stroke=0, fill=1)
    pdf.setStrokeColor(colors.HexColor("#64748B"))
    pdf.setLineWidth(0.45)
    cursor = x
    for width, label in zip(columns, labels):
        pdf.rect(cursor, y - height, width, height, stroke=1, fill=0)
        _center_text(pdf, label, cursor, y - 10, width, font="Helvetica-Bold", size=6.7, color="#0F172A")
        cursor += width
    return y - height


def _draw_item_row(pdf: canvas.Canvas, x: float, y: float, columns: list[float], index: int, row: dict[str, Any], height: float) -> float:
    values = [
        str(index),
        str(row.get("item") or row.get("item_name") or ""),
        str(row.get("hsn") or ""),
        _qty(row.get("qty")),
        str(row.get("unit") or ""),
        _money_plain(row.get("mrp")),
        _money_plain(row.get("rate")),
        _qty(row.get("free") or row.get("scheme")),
        _money_plain(row.get("disc") or row.get("discount")),
        _money_plain(row.get("taxable")),
        _qty(row.get("gst")),
        _money_plain(row.get("amount") or row.get("total")),
    ]
    pdf.setStrokeColor(colors.HexColor("#CBD5E1"))
    cursor = x
    for col_index, (width, value) in enumerate(zip(columns, values)):
        pdf.rect(cursor, y - height, width, height, stroke=1, fill=0)
        if col_index == 1:
            main, sub = _split_item(value)
            _draw_text(pdf, _fit_text(pdf, main, width - 6, "Helvetica-Bold", 6.3), cursor + 3, y - 7.2, font="Helvetica-Bold", size=6.3, color="#0F172A")
            if sub:
                _draw_text(pdf, _fit_text(pdf, sub, width - 6, "Helvetica", 5.8), cursor + 3, y - 15.1, size=5.8, color="#475569")
        elif col_index in {3, 5, 6, 7, 8, 9, 10, 11}:
            _right_text(pdf, value, cursor + width - 4, y - 12, size=6.5, color="#0F172A")
        else:
            _draw_text(pdf, _fit_text(pdf, value, width - 6, "Helvetica", 6.5), cursor + 3, y - 12, size=6.5, color="#0F172A")
        cursor += width
    return y - height


def _draw_total_row(pdf: canvas.Canvas, x: float, y: float, columns: list[float], values: list[str], height: float) -> float:
    pdf.setFillColor(colors.HexColor("#F8FAFC"))
    pdf.rect(x, y - height, sum(columns), height, stroke=0, fill=1)
    cursor = x
    for idx, (width, value) in enumerate(zip(columns, values)):
        pdf.setStrokeColor(colors.HexColor("#64748B"))
        pdf.rect(cursor, y - height, width, height, stroke=1, fill=0)
        if idx == 1:
            _draw_text(pdf, value, cursor + 3, y - 10, font="Helvetica-Bold", size=6.8, color="#0F172A")
        elif value:
            _right_text(pdf, value, cursor + width - 4, y - 10, font="Helvetica-Bold", size=6.5, color="#0F172A")
        cursor += width
    return y - height


def _draw_mini_header(pdf: canvas.Canvas, x: float, y: float, columns: list[float], labels: list[str]) -> None:
    cursor = x
    for width, label in zip(columns, labels):
        pdf.setFillColor(colors.HexColor("#F8FAFC"))
        pdf.setStrokeColor(colors.HexColor("#94A3B8"))
        pdf.setLineWidth(0.45)
        pdf.rect(cursor, y - 11, width, 12, stroke=1, fill=1)
        _center_text(pdf, _fit_text(pdf, label, width - 4, "Helvetica-Bold", 5.8), cursor, y - 7, width, font="Helvetica-Bold", size=5.8, color="#64748B")
        cursor += width


def _draw_mini_row(pdf: canvas.Canvas, x: float, y: float, columns: list[float], values: list[str], *, bold: bool = False) -> None:
    cursor = x
    for idx, (width, value) in enumerate(zip(columns, values)):
        font = "Helvetica-Bold" if bold or idx == 0 else "Helvetica"
        pdf.setFillColor(colors.HexColor("#FFFFFF"))
        pdf.setStrokeColor(colors.HexColor("#94A3B8"))
        pdf.setLineWidth(0.42)
        pdf.rect(cursor, y - 10, width, 12, stroke=1, fill=1)
        if idx == 0:
            _draw_text(pdf, _fit_text(pdf, value, width - 4, font, 5.8), cursor + 2, y - 6, font=font, size=5.8, color="#0F172A")
        else:
            _right_text(pdf, value, cursor + width - 2, y - 6, font=font, size=5.8, color="#0F172A")
        cursor += width


def _draw_continue_marker(pdf: canvas.Canvas, x: float, bottom: float, width: float, page_index: int) -> None:
    y = bottom + 27
    _draw_box(pdf, x, y, width, 14, "#F8FAFC", "#CBD5E1", radius=3, stroke_width=0.55)
    _center_text(pdf, f"Continued on next page... Page {page_index}", x, y + 4.5, width, font="Helvetica-Bold", size=6.6, color="#475569")


def _draw_page_footer(pdf: canvas.Canvas, width: float, margin: float, page_index: int) -> None:
    logo = _resolve_asset("assets/PRM_SoftSolutions.jpg", logo=True)
    y = margin + 10
    if logo:
        _draw_image(pdf, logo, margin + 4, y - 2, 12, 12)
    _center_text(pdf, f"Copyright (c) {datetime.now():%Y} PRM Software Solutions. All rights reserved.", 0, y, width, size=6.2, color="#475569")
    _right_text(pdf, f"Page {page_index}", width - margin - 6, y, size=5.8, color="#94A3B8")


def _section_company_center_text(pdf: canvas.Canvas, company: dict[str, Any], x: float, top: float, width: float) -> None:
    _center_text(pdf, _company_name(company).upper(), x, top - 18, width, font="Helvetica-Bold", size=11 if width > (150 * mm) else 9.2, color="#0F172A")
    _center_text(pdf, _company_address(company), x, top - 28, width, size=6.7, color="#475569")
    _center_text(pdf, _company_contact_line(company), x, top - 38, width, font="Helvetica-Bold", size=6.4, color="#475569")


def _section_party_block(pdf: canvas.Canvas, label: str, values: list[str], x: float, y: float, width: float, height: float) -> None:
    """Draw a labeled party/payment block with wrapped values inside a box."""
    _draw_text(pdf, label, x + 5, y - 12, font="Helvetica-Bold", size=7.2, color="#1E3A8A")
    text_y = y - 24
    for value in values[:7]:
        _draw_wrapped(pdf, value, x + 5, text_y, width - 10, size=6.4, leading=8.6)
        text_y -= 9 if len(value) < 50 else 17


def _section_document_details(pdf: canvas.Canvas, label: str, doc: dict[str, Any] | None, x: float, y: float, width: float) -> None:
    """Draw a labeled detail block for voucher/document metadata."""
    _draw_text(pdf, label, x + 7, y - 13, font="Helvetica-Bold", size=8, color="#1E3A8A")
    if not doc:
        return
    lines: list[str] = []
    doc_no = doc.get("doc_no") or doc.get("voucher_no") or doc.get("no") or ""
    if doc_no:
        lines.append(f"No: {doc_no}")
    doc_date = doc.get("entry_date") or doc.get("date") or doc.get("voucher_date") or ""
    if doc_date:
        lines.append(f"Date: {_date_text(doc_date)}")
    reference = doc.get("reference") or doc.get("ref_no") or doc.get("bank_reference") or doc.get("transaction_id") or doc.get("upi_ref") or ""
    if reference:
        lines.append(f"Reference: {reference}")
    instrument = doc.get("instrument_no") or doc.get("cheque_no") or doc.get("bank_reference") or doc.get("transaction_id") or doc.get("upi_ref") or ""
    if instrument:
        lines.append(f"Instrument: {instrument}")
    prepared = doc.get("employee") or doc.get("prepared_by") or "Administrator"
    if prepared:
        lines.append(f"Prepared: {prepared}")
    text_y = y - 29
    for value in lines:
        _draw_wrapped(pdf, value, x + 7, text_y, width - 14, size=7.1, leading=8.8)
        text_y -= 11.5


def _section_title_strip(pdf: canvas.Canvas, x: float, y: float, width: float, title: str, *, font: str = "Helvetica-Bold", size: float = 7.2, title_left: float = 8) -> None:
    pdf.setFillColor(colors.HexColor("#DFF4FF"))
    pdf.rect(x, y, width, 12, stroke=0, fill=1)
    _draw_text(pdf, _fit_text(pdf, title, width * 0.48, font, size), x + title_left, y + 4, font=font, size=size, color="#0F172A")



def _draw_box(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    fill: str,
    stroke: str,
    *,
    radius: float = 0,
    stroke_width: float = 0.45,
) -> None:
    pdf.setFillColor(colors.HexColor(fill))
    pdf.setStrokeColor(colors.HexColor(stroke))
    pdf.setLineWidth(stroke_width)
    if radius:
        pdf.roundRect(x, y, width, height, radius, stroke=1, fill=1)
    else:
        pdf.rect(x, y, width, height, stroke=1, fill=1)


def _draw_image(pdf: canvas.Canvas, path: Path | None, x: float, y: float, width: float, height: float) -> None:
    if not path or not path.exists():
        return
    try:
        pdf.drawImage(ImageReader(str(path)), x, y, width=width, height=height, preserveAspectRatio=True, mask="auto")
    except Exception:
        return


def _draw_text(pdf: canvas.Canvas, value: Any, x: float, y: float, *, font: str = "Helvetica", size: float = 7, color: str = "#0F172A") -> None:
    pdf.setFont(font, size)
    pdf.setFillColor(colors.HexColor(color))
    pdf.drawString(x, y, str(value or ""))


def _right_text(pdf: canvas.Canvas, value: Any, x: float, y: float, *, font: str = "Helvetica", size: float = 7, color: str = "#0F172A") -> None:
    text = str(value or "")
    pdf.setFont(font, size)
    pdf.setFillColor(colors.HexColor(color))
    pdf.drawRightString(x, y, text)


def _center_text(pdf: canvas.Canvas, value: Any, x: float, y: float, width: float, *, font: str = "Helvetica", size: float = 7, color: str = "#0F172A") -> None:
    text = str(value or "")
    pdf.setFont(font, size)
    pdf.setFillColor(colors.HexColor(color))
    pdf.drawCentredString(x + (width / 2), y, text)


def _draw_wrapped(
    pdf: canvas.Canvas,
    value: Any,
    x: float,
    y: float,
    width: float,
    *,
    font: str = "Helvetica",
    size: float = 7,
    leading: float = 9,
    color: str = "#0F172A",
    max_lines: int = 4,
) -> int:
    text = str(value or "").replace("\r", "\n")
    lines: list[str] = []
    for para in text.splitlines() or [""]:
        words = para.split()
        current = ""
        for word in words:
            trial = f"{current} {word}".strip()
            if pdf.stringWidth(trial, font, size) <= width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current or not words:
            lines.append(current)
    used = 0
    for line in lines[:max_lines]:
        _draw_text(pdf, _fit_text(pdf, line, width, font, size), x, y - (used * leading), font=font, size=size, color=color)
        used += 1
    return used


def _scaled_columns(widths: list[float], target_width: float) -> list[float]:
    total = sum(widths) or 1
    scale = target_width / total
    return [w * scale for w in widths]


def _template_row_by_code(template_code: str | None, document_type: str, db_path: Path | None) -> dict[str, Any]:
    code = str(template_code or "").strip()
    if not code:
        return {}
    db = Path(db_path) if db_path else _default_db_path()
    if not db.exists():
        return {}
    try:
        with sqlite3.connect(db) as conn:
            conn.row_factory = sqlite3.Row
            orientation_col = _print_template_orientation_select(conn)
            row = conn.execute(
                f"""
                SELECT pt.template_code,pt.template_name,pt.document_type,pt.paper_size,{orientation_col},pt.print_mode,
                       tf.family_code,tf.family_name,tf.business_type,tf.default_paper_size,tf.default_print_mode
                FROM print_templates pt
                LEFT JOIN print_template_families tf ON tf.id=pt.family_id
                WHERE LOWER(pt.template_code)=LOWER(?) AND LOWER(pt.document_type)=LOWER(?) AND COALESCE(pt.is_active,1)=1
                LIMIT 1
                """,
                (code, document_type),
            ).fetchone()
            return dict(row) if row else {}
    except sqlite3.Error:
        return {}


def _template_row(company: dict[str, Any], document_type: str, db_path: Path | None) -> dict[str, Any]:
    if company.get("invoice_template_code"):
        row = _template_row_by_code(company.get("invoice_template_code"), document_type, db_path)
        if row:
            return row
    db = Path(db_path) if db_path else _default_db_path()
    if not db or not db.exists():
        return {}
    business_type = normalize_business_type(company.get("business_type_code") or company.get("business_type") or "")
    family_business_types = [bt.lower() for bt in equivalent_business_type_codes(business_type)]
    placeholders = ",".join("?" for _ in family_business_types)
    try:
        with sqlite3.connect(db) as conn:
            conn.row_factory = sqlite3.Row
            orientation_col = _print_template_orientation_select(conn)
            row = conn.execute(
                f"""
                SELECT pt.template_code,pt.template_name,pt.document_type,pt.paper_size,{orientation_col},pt.print_mode,
                       tf.family_code,tf.family_name,tf.business_type,tf.default_paper_size,tf.default_print_mode
                FROM print_templates pt
                LEFT JOIN print_template_families tf ON tf.id=pt.family_id
                WHERE LOWER(pt.document_type)=LOWER(?) AND COALESCE(pt.is_active,1)=1
                ORDER BY
                    CASE WHEN LOWER(COALESCE(tf.business_type,'')) IN ({placeholders}) THEN 0 ELSE 1 END,
                    CASE WHEN COALESCE(pt.is_default,0)=1 THEN 0 ELSE 1 END,
                    pt.id
                LIMIT 1
                """,
                (document_type, *family_business_types),
            ).fetchone()
            return dict(row) if row else {}
    except sqlite3.Error:
        return {}


def _print_template_orientation_select(conn: sqlite3.Connection) -> str:
    try:
        columns = {str(row[1]).lower() for row in conn.execute("PRAGMA table_info(print_templates)").fetchall()}
    except sqlite3.Error:
        columns = set()
    return "pt.orientation AS orientation" if "orientation" in columns else "'' AS orientation"


def _default_db_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "_internal" / "database" / "prm_billing_inventory.db"
    return Path(__file__).resolve().parents[1] / "database" / "prm_billing_inventory.db"


def _resolve_asset(value: Any, *, logo: bool = False) -> Path | None:
    raw = str(value or "").strip()
    candidates: list[Path] = []
    if raw:
        candidate = Path(raw)
        if candidate.is_absolute():
            candidates.append(candidate)
        else:
            for root in _resource_roots():
                candidates.append(root / raw)
    if logo:
        for root in _resource_roots():
            candidates.append(root / "assets" / "PRM_SoftSolutions.jpg")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _resource_roots() -> Iterable[Path]:
    if getattr(sys, "frozen", False):
        exe_root = Path(sys.executable).resolve().parent
        yield exe_root / "_internal"
        yield exe_root
    else:
        yield Path(__file__).resolve().parents[1]


def _party_lines(header: dict[str, Any], party_label: str) -> list[str]:
    party = str(header.get("party_name") or header.get("customer_name") or header.get("supplier_name") or header.get("party") or "")
    return [
        party,
        f"GSTIN: {header.get('party_gstin') or header.get('gstin') or ''}",
        f"Phone: {header.get('party_phone') or header.get('phone') or ''}",
        f"Contact: {header.get('contact_person') or ''}",
        f"Area: {header.get('area') or header.get('customer_area') or ''}",
        f"Billing Address: {header.get('billing_address') or header.get('address') or ''}",
    ]


def _ship_lines(header: dict[str, Any], ship_to: str | None) -> list[str]:
    return [
        str(ship_to or header.get("shipping") or header.get("ship_to") or ""),
        f"No: {header.get('no') or header.get('bill_no') or header.get('doc_no') or ''}",
        f"Date: {_date_text(header.get('date') or header.get('bill_date') or header.get('doc_date'))}",
        f"Employee: {header.get('employee') or 'Administrator'}",
        f"Transport: {header.get('transport') or header.get('transport_details') or ''}",
    ]


def _payment_lines(header: dict[str, Any]) -> list[str]:
    values = [
        f"Mode: {header.get('payment') or header.get('pay_mode') or ''}",
        f"Warehouse: {header.get('warehouse') or ''}",
        f"Credit: {header.get('credit_terms') or ''}",
        f"PO: {header.get('po_no') or header.get('po_number') or ''}",
    ]
    return values


def _gst_summary(lines: list[dict[str, Any]]) -> dict[float, dict[str, float]]:
    summary: dict[float, dict[str, float]] = {}
    for row in lines:
        rate = round(float(row.get("gst") or 0), 2)
        bucket = summary.setdefault(rate, {"taxable": 0.0, "free": 0.0, "disc": 0.0, "cgst": 0.0, "sgst": 0.0, "igst": 0.0, "gst": 0.0})
        taxable = float(row.get("taxable") or 0)
        gst_total = round(taxable * rate / 100, 2)
        cgst = float(row.get("cgst") or 0)
        sgst = float(row.get("sgst") or 0)
        igst = float(row.get("igst") or 0)
        if not any([cgst, sgst, igst]):
            cgst = round(gst_total / 2, 2)
            sgst = round(gst_total - cgst, 2)
        bucket["taxable"] += taxable
        bucket["free"] += float(row.get("free") or row.get("scheme") or 0)
        bucket["disc"] += float(row.get("disc") or row.get("discount") or 0)
        bucket["cgst"] += cgst
        bucket["sgst"] += sgst
        bucket["igst"] += igst
        bucket["gst"] += cgst + sgst + igst
    return dict(sorted(summary.items(), key=lambda item: item[0]))


def amount_in_words(value: Any) -> str:
    try:
        number = int(round(float(value or 0)))
    except (TypeError, ValueError):
        number = 0
    if number == 0:
        return "Zero Rupees Only"
    words = _number_to_words(number)
    return f"{words} Rupees Only"


def _number_to_words(number: int) -> str:
    ones = [
        "",
        "One",
        "Two",
        "Three",
        "Four",
        "Five",
        "Six",
        "Seven",
        "Eight",
        "Nine",
        "Ten",
        "Eleven",
        "Twelve",
        "Thirteen",
        "Fourteen",
        "Fifteen",
        "Sixteen",
        "Seventeen",
        "Eighteen",
        "Nineteen",
    ]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    def below_thousand(value: int) -> str:
        parts: list[str] = []
        if value >= 100:
            parts.append(ones[value // 100] + " Hundred")
            value %= 100
        if value >= 20:
            parts.append(tens[value // 10])
            value %= 10
        if value:
            parts.append(ones[value])
        return " ".join(parts)

    parts: list[str] = []
    for divisor, label in [(10000000, "Crore"), (100000, "Lakh"), (1000, "Thousand")]:
        if number >= divisor:
            parts.append(f"{below_thousand(number // divisor)} {label}")
            number %= divisor
    if number:
        parts.append(below_thousand(number))
    return " ".join(part for part in parts if part)


def _company_name(company: dict[str, Any]) -> str:
    return str(company.get("business_name") or company.get("name") or "PRM Billing Inventory").strip()


def _company_address(company: dict[str, Any]) -> str:
    address = _single_line(company.get("address") or "")
    if address:
        return address
    parts = [
        _single_line(company.get("city") or ""),
        _single_line(company.get("state") or ""),
        _single_line(company.get("pincode") or company.get("pin") or ""),
    ]
    return ", ".join(part for part in parts if part)


def _company_contact_line(company: dict[str, Any]) -> str:
    parts = []
    if company.get("gstin"):
        parts.append(f"GSTIN: {company.get('gstin')}")
    if company.get("fssai_no"):
        parts.append(f"FSSAI: {company.get('fssai_no')}")
    phone = company.get("phone") or company.get("mobile")
    if phone:
        parts.append(f"Phone: {phone}")
    if company.get("email"):
        parts.append(f"Email: {company.get('email')}")
    return " | ".join(_single_line(part) for part in parts if _single_line(part))


def _single_line(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _date_text(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text[:10], fmt).strftime("%d-%m-%Y")
        except ValueError:
            pass
    return text


def _money(value: Any) -> str:
    return f"Rs {_money_plain(value)}"


def _money_plain(value: Any) -> str:
    try:
        return f"{float(value or 0):,.2f}"
    except (TypeError, ValueError):
        return "0.00"


def _qty(value: Any) -> str:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        return "0"
    if abs(number - int(number)) < 0.0001:
        return str(int(number))
    return f"{number:,.3f}".rstrip("0").rstrip(".")


def _text(value: Any) -> str:
    return "" if value is None else str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _title(value: str) -> str:
    return str(value).replace("_", " ").strip().title()


def _norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")


def _is_distributor_a2(business_type: str, document_type: str) -> bool:
    return _norm(business_type) == "distributor_wholesale" and _norm(document_type) in DISTRIBUTOR_A2_TYPES


def _split_item(value: str) -> tuple[str, str]:
    if " / " in value:
        first, rest = value.split(" / ", 1)
        return first, rest
    if "|" in value:
        first, rest = value.split("|", 1)
        return first.strip(), rest.strip()
    return value, ""


def _fit_text(pdf: canvas.Canvas, value: str, width: float, font: str, size: float) -> str:
    text = str(value or "")
    if pdf.stringWidth(text, font, size) <= width:
        return text
    ellipsis = "..."
    while text and pdf.stringWidth(text + ellipsis, font, size) > width:
        text = text[:-1]
    return text + ellipsis if text else ellipsis
