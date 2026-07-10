from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

from services.mysql_source import MySqlSource
from services.sales_calculator import SalesCalculator, SalesLine
from services.transaction_repository import TransactionRepository


class OrderConversionService:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = Path(db_path or MySqlSource().sqlite_path)
        self.repository = TransactionRepository(self.db_path)

    def candidates(self, limit: int = 500) -> list[dict[str, Any]]:
        return self._rows(
            """
            SELECT
                id,
                doc_no,
                doc_date,
                CASE LOWER(REPLACE(doc_type,' ','_'))
                    WHEN 'quotation' THEN 'Quotation'
                    WHEN 'sales_order' THEN 'Sales Order'
                    WHEN 'purchase_order' THEN 'Purchase Order'
                    ELSE doc_type
                END flow_stage,
                CASE LOWER(REPLACE(doc_type,' ','_'))
                    WHEN 'quotation' THEN 'Make Sales Bill'
                    WHEN 'sales_order' THEN 'Make Sales Bill'
                    WHEN 'purchase_order' THEN 'Make Purchase'
                    ELSE ''
                END next_action,
                CASE LOWER(REPLACE(doc_type,' ','_'))
                    WHEN 'quotation' THEN 'No stock or account posting until converted'
                    WHEN 'sales_order' THEN 'Posts sale, stock and voucher after conversion'
                    WHEN 'purchase_order' THEN 'Posts purchase, stock and voucher after conversion'
                    ELSE ''
                END accounting_effect,
                doc_type,
                party_name,
                area,
                pay_mode,
                grand_total,
                status,
                converted_ref
            FROM order_documents
            WHERE COALESCE(converted_ref,'')=''
              AND LOWER(COALESCE(status,'Open')) NOT IN ('cancelled','converted','closed')
              AND LOWER(REPLACE(doc_type,' ','_')) IN ('quotation','sales_order','purchase_order')
            ORDER BY doc_date DESC,id DESC
            LIMIT ?
            """,
            (int(limit),),
        )

    def convert_to_sales(self, order_id: int, bill_no: str | None = None) -> dict[str, Any]:
        doc = self._document(order_id)
        if self._normalized_doc_type(doc.get("doc_type")) not in {"quotation", "sales_order"}:
            raise ValueError("Only quotation or sales order can convert to sales.")
        self._ensure_not_converted(doc)
        self._ensure_convertible_status(doc)
        lines = self._document_lines(order_id)
        if not lines:
            raise ValueError("No item rows found for conversion.")
        company = self._company()
        bill_no = bill_no or self._next_no("sales", "bill_no", str(company.get("invoice_prefix") or "PRM"))
        computed = self._computed_lines(lines, str(company.get("state") or ""))
        self._validate_sales_stock(computed)
        totals = SalesCalculator(str(company.get("state") or "")).totals(computed)
        header = {
            "bill_no": bill_no,
            "bill_date": date.today().isoformat(),
            "customer_id": doc.get("party_id") or 0,
            "customer_name": doc.get("party_name") or "Customer",
            "customer_area": doc.get("area") or "",
            "payment": doc.get("pay_mode") or "Credit",
            "party_type": "customer",
            "party_id": doc.get("party_id") or 0,
            "party_name": doc.get("party_name") or "Customer",
            "price_level": "Retail",
            "employee": doc.get("employee_name") or "",
            "warehouse_id": doc.get("warehouse_id") or 0,
            "branch": "",
            "cost_center": "",
            "shipping": "",
            "po_no": doc.get("doc_no") or "",
            "transport": doc.get("notes") or "",
            "credit_terms": "",
        }
        sale_id = self.repository.save_sales(header, computed, totals)
        self._mark_converted(order_id, bill_no)
        return {"target": "sales", "id": sale_id, "bill_no": bill_no, "grand_total": totals["grand_total"]}

    def convert_to_purchase(self, order_id: int, bill_no: str | None = None) -> dict[str, Any]:
        doc = self._document(order_id)
        if self._normalized_doc_type(doc.get("doc_type")) != "purchase_order":
            raise ValueError("Only purchase order can convert to purchase.")
        self._ensure_not_converted(doc)
        self._ensure_convertible_status(doc)
        lines = self._document_lines(order_id)
        if not lines:
            raise ValueError("No item rows found for conversion.")
        bill_no = (bill_no or doc.get("doc_no") or "").strip()
        if not bill_no:
            raise ValueError("Supplier invoice number is required.")
        if self._one("SELECT id FROM purchases WHERE bill_no=?", (bill_no,)):
            raise ValueError("Supplier invoice number already exists in purchases.")
        company = self._company()
        computed = self._computed_lines(lines, str(company.get("state") or ""))
        totals = SalesCalculator(str(company.get("state") or "")).totals(computed)
        header = {
            "bill_no": bill_no,
            "bill_date": date.today().isoformat(),
            "supplier_id": doc.get("party_id") or 0,
            "supplier_name": doc.get("party_name") or "Supplier",
            "payment": doc.get("pay_mode") or "Credit",
            "party_type": "supplier",
            "party_id": doc.get("party_id") or 0,
            "party_name": doc.get("party_name") or "Supplier",
            "price_level": "Purchase",
            "employee": doc.get("employee_name") or "",
            "warehouse_id": doc.get("warehouse_id") or 0,
            "branch": "",
            "cost_center": "",
        }
        purchase_id = self.repository.save_purchase(header, computed, totals)
        self._mark_converted(order_id, bill_no)
        return {"target": "purchases", "id": purchase_id, "bill_no": bill_no, "grand_total": totals["grand_total"]}

    def set_status(self, order_id: int, status: str) -> None:
        allowed = {"Open", "Accepted", "Ready", "Closed", "Cancelled"}
        if status not in allowed:
            raise ValueError("Unsupported document status.")
        doc = self._document(order_id)
        self._ensure_not_converted(doc)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE order_documents SET status=?, updated_at=? WHERE id=?",
                (status, date.today().isoformat(), int(order_id)),
            )
            conn.commit()

    def _computed_lines(self, rows: list[dict[str, Any]], company_state: str) -> list[Any]:
        calculator = SalesCalculator(company_state)
        computed = []
        for row in rows:
            qty = float(row.get("qty") or 0)
            if qty <= 0:
                continue
            line = SalesLine(
                item_name=str(row.get("item_name") or ""),
                pack_name=str(row.get("pack_display_snapshot") or ""),
                hsn=str(row.get("hsn") or ""),
                unit=str(row.get("unit") or "PCS"),
                qty=qty,
                free_qty=float(row.get("free_qty") or 0),
                mrp=float(row.get("mrp") or 0),
                rate=float(row.get("rate") or 0),
                scheme=0,
                discount_amount=float(row.get("discount") or 0),
                gst_rate=float(row.get("gst") or 0),
                item_id=int(row.get("item_id") or 0),
                pack_id=int(row.get("pack_id") or 0),
                pack_size=float(row.get("pack_size_snapshot") or 1),
                tax_mode="igst" if float(row.get("igst") or 0) > 0 else "",
            )
            place = "Interstate" if line.tax_mode == "igst" else ""
            computed.append(calculator.compute_line(line, place_of_supply=place))
        if not computed:
            raise ValueError("Enter quantity for at least one item.")
        return computed

    def _validate_sales_stock(self, lines: list[Any]) -> None:
        for line in lines:
            if not line.source.item_id:
                continue
            stock = self._one("SELECT COALESCE(stock,0) stock FROM items WHERE id=?", (line.source.item_id,))
            available = float((stock or {}).get("stock") or 0)
            needed = float(line.source.qty or 0) + float(line.source.free_qty or 0)
            if needed > available + 0.0001:
                raise ValueError(f"Insufficient stock for {line.source.item_name}. Available {available:.3f}, required {needed:.3f}.")

    def _document(self, order_id: int) -> dict[str, Any]:
        doc = self._one("SELECT * FROM order_documents WHERE id=?", (int(order_id),))
        if not doc:
            raise ValueError("Order document not found.")
        return doc

    def _document_lines(self, order_id: int) -> list[dict[str, Any]]:
        return self._rows("SELECT * FROM order_document_items WHERE order_document_id=? ORDER BY id", (int(order_id),))

    def _company(self) -> dict[str, Any]:
        return self._one("SELECT * FROM company ORDER BY id LIMIT 1") or {}

    def _ensure_not_converted(self, doc: dict[str, Any]) -> None:
        if str(doc.get("converted_ref") or "").strip():
            raise ValueError(f"Already converted to {doc.get('converted_ref')}.")

    def _ensure_convertible_status(self, doc: dict[str, Any]) -> None:
        status = str(doc.get("status") or "Open").strip().lower()
        if status in {"converted", "cancelled", "closed"}:
            raise ValueError(f"{doc.get('doc_no') or 'Document'} is {doc.get('status') or status} and cannot be converted.")

    def _normalized_doc_type(self, value: Any) -> str:
        return str(value or "").strip().lower().replace(" ", "_")

    def _mark_converted(self, order_id: int, ref: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE order_documents SET status='Converted', converted_ref=?, updated_at=? WHERE id=?", (ref, date.today().isoformat(), int(order_id)))
            conn.commit()

    def _next_no(self, table: str, column: str, prefix: str) -> str:
        row = self._one(f"SELECT COALESCE(MAX(id),0)+1 next_id FROM {table}")
        return f"{prefix}-{date.today():%y%m%d}-{int((row or {}).get('next_id') or 1):04d}"

    def _rows(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def _one(self, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        rows = self._rows(sql, params)
        return rows[0] if rows else None
