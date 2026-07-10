from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


class GstPayloadService:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def prepare_pending(self, kind: str, output_dir: Path, limit: int = 50) -> dict[str, Any]:
        if kind not in {"einvoice", "eway_bill"}:
            raise ValueError("GST payload kind must be einvoice or eway_bill.")
        output_dir.mkdir(parents=True, exist_ok=True)
        company = self._company()
        sales = self._pending_sales(kind, limit)
        files: list[str] = []
        for sale in sales:
            lines = self._sale_lines(int(sale["id"]))
            payload = self._einvoice_payload(company, sale, lines) if kind == "einvoice" else self._eway_payload(company, sale, lines)
            file_path = output_dir / f"{kind}_{sale['id']}_{_safe_name(sale.get('bill_no'))}.json"
            file_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            files.append(str(file_path))
            self._record_prepared(kind, sale, payload)
        return {"kind": kind, "prepared": len(files), "files": files, "pending_checked": len(sales)}

    def _company(self) -> dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM company ORDER BY id LIMIT 1").fetchone()
            return dict(row) if row else {}

    def _pending_sales(self, kind: str, limit: int) -> list[dict[str, Any]]:
        table = "einvoices" if kind == "einvoice" else "eway_bills"
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"""
                SELECT s.*, c.gstin customer_gstin, c.address customer_address, c.state customer_state,
                       c.place_of_supply, c.phone customer_phone
                FROM sales s
                LEFT JOIN customers c ON c.id=s.customer_id
                LEFT JOIN {table} g ON g.sale_id=s.id OR g.invoice_no=s.bill_no
                WHERE g.id IS NULL AND COALESCE(s.status,'Active') NOT IN ('Cancelled','Deleted')
                ORDER BY s.bill_date DESC, s.id DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
            return [dict(row) for row in rows]

    def _sale_lines(self, sale_id: int) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT item_name, hsn, unit, qty, free_qty, mrp, rate, gst, taxable, gst_amt,
                       cgst, sgst, igst, total, discount, pack_display_snapshot
                FROM sales_items
                WHERE sale_id=?
                ORDER BY id
                """,
                (sale_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def _einvoice_payload(self, company: dict[str, Any], sale: dict[str, Any], lines: list[dict[str, Any]]) -> dict[str, Any]:
        messages = self._validation_messages(company, sale, require_vehicle=False)
        return {
            "Version": "1.1",
            "PreparedBy": "PRM BILLING INVENTORY Desktop",
            "PreparedAt": datetime.now().isoformat(timespec="seconds"),
            "ValidationMessages": messages,
            "TranDtls": {"TaxSch": "GST", "SupTyp": "B2B" if sale.get("customer_gstin") else "B2C", "RegRev": "N"},
            "DocDtls": {"Typ": "INV", "No": sale.get("bill_no") or "", "Dt": sale.get("bill_date") or ""},
            "SellerDtls": self._seller(company),
            "BuyerDtls": self._buyer(sale),
            "ItemList": [self._einvoice_item(index, row) for index, row in enumerate(lines, start=1)],
            "ValDtls": {
                "AssVal": _round(sale.get("taxable")),
                "CgstVal": _round(sale.get("cgst_total")),
                "SgstVal": _round(sale.get("sgst_total")),
                "IgstVal": _round(sale.get("igst_total")),
                "TotInvVal": _round(sale.get("grand_total")),
                "RndOffAmt": _round(sale.get("round_off")),
            },
        }

    def _eway_payload(self, company: dict[str, Any], sale: dict[str, Any], lines: list[dict[str, Any]]) -> dict[str, Any]:
        messages = self._validation_messages(company, sale, require_vehicle=True)
        return {
            "supplyType": "O",
            "subSupplyType": "1",
            "docType": "INV",
            "docNo": sale.get("bill_no") or "",
            "docDate": sale.get("bill_date") or "",
            "fromGstin": company.get("gstin") or "",
            "fromTrdName": company.get("business_name") or company.get("name") or "",
            "fromAddr1": company.get("address") or "",
            "fromPlace": company.get("city") or "",
            "fromState": company.get("state") or "",
            "toGstin": sale.get("customer_gstin") or "",
            "toTrdName": sale.get("customer_name") or "",
            "toAddr1": sale.get("shipping_address") or sale.get("customer_address") or "",
            "toPlace": sale.get("place_of_supply") or sale.get("customer_state") or "",
            "toState": sale.get("customer_state") or "",
            "transactionType": 1,
            "totalValue": _round(sale.get("taxable")),
            "cgstValue": _round(sale.get("cgst_total")),
            "sgstValue": _round(sale.get("sgst_total")),
            "igstValue": _round(sale.get("igst_total")),
            "totInvValue": _round(sale.get("grand_total")),
            "transMode": "1",
            "transDistance": 0,
            "transporterName": sale.get("transport_details") or "",
            "vehicleNo": "",
            "vehicleType": "R",
            "ValidationMessages": messages,
            "itemList": [self._eway_item(row) for row in lines],
            "PreparedBy": "PRM BILLING INVENTORY Desktop",
            "PreparedAt": datetime.now().isoformat(timespec="seconds"),
        }

    def _seller(self, company: dict[str, Any]) -> dict[str, Any]:
        return {
            "Gstin": company.get("gstin") or "",
            "LglNm": company.get("business_name") or company.get("name") or "",
            "Addr1": company.get("address") or "",
            "Loc": company.get("city") or "",
            "Pin": _int(company.get("pincode")),
            "Stcd": company.get("state") or "",
            "Ph": company.get("phone") or company.get("mobile") or "",
            "Em": company.get("email") or "",
        }

    def _buyer(self, sale: dict[str, Any]) -> dict[str, Any]:
        return {
            "Gstin": sale.get("customer_gstin") or "",
            "LglNm": sale.get("customer_name") or "",
            "Pos": sale.get("place_of_supply") or sale.get("customer_state") or "",
            "Addr1": sale.get("shipping_address") or sale.get("customer_address") or "",
            "Loc": sale.get("customer_area") or "",
            "Pin": 0,
            "Stcd": sale.get("customer_state") or "",
            "Ph": sale.get("customer_phone") or "",
        }

    def _einvoice_item(self, index: int, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "SlNo": str(index),
            "PrdDesc": row.get("item_name") or "",
            "IsServc": "N",
            "HsnCd": row.get("hsn") or "",
            "Qty": _round(row.get("qty")),
            "FreeQty": _round(row.get("free_qty")),
            "Unit": row.get("unit") or "NOS",
            "UnitPrice": _round(row.get("rate")),
            "TotAmt": _round(row.get("taxable")),
            "Discount": _round(row.get("discount")),
            "AssAmt": _round(row.get("taxable")),
            "GstRt": _round(row.get("gst")),
            "CgstAmt": _round(row.get("cgst")),
            "SgstAmt": _round(row.get("sgst")),
            "IgstAmt": _round(row.get("igst")),
            "TotItemVal": _round(row.get("total")),
        }

    def _eway_item(self, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "productName": row.get("item_name") or "",
            "productDesc": row.get("pack_display_snapshot") or row.get("item_name") or "",
            "hsnCode": row.get("hsn") or "",
            "quantity": _round(row.get("qty")),
            "qtyUnit": row.get("unit") or "NOS",
            "taxableAmount": _round(row.get("taxable")),
            "cgstRate": _round(row.get("gst")) / 2 if _round(row.get("igst")) == 0 else 0,
            "sgstRate": _round(row.get("gst")) / 2 if _round(row.get("igst")) == 0 else 0,
            "igstRate": _round(row.get("gst")) if _round(row.get("igst")) else 0,
        }

    def _validation_messages(self, company: dict[str, Any], sale: dict[str, Any], require_vehicle: bool) -> list[str]:
        messages: list[str] = []
        if not company.get("gstin"):
            messages.append("Company GSTIN missing.")
        if not sale.get("customer_gstin"):
            messages.append("Customer GSTIN missing; payload prepared as draft.")
        if require_vehicle:
            messages.append("Vehicle number and distance must be filled before live E-Way submission.")
        return messages

    def _record_prepared(self, kind: str, sale: dict[str, Any], payload: dict[str, Any]) -> None:
        now = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(self.db_path) as conn:
            if kind == "einvoice":
                conn.execute(
                    """
                    INSERT INTO einvoices(sale_id,invoice_no,irn,ack_no,ack_date,signed_qr,signed_json,status,created_at)
                    VALUES(?,?,?,?,?,?,?,?,?)
                    """,
                    (sale.get("id"), sale.get("bill_no"), "", "", "", "", json.dumps(payload, ensure_ascii=False), "Prepared", now),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO eway_bills(
                        sale_id,invoice_no,eway_no,eway_date,valid_until,transporter_name,
                        transporter_id,vehicle_no,distance_km,status,created_at
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (sale.get("id"), sale.get("bill_no"), "", "", "", sale.get("transport_details") or "", "", "", 0, "Prepared", now),
                )
            conn.commit()


def _safe_name(value: Any) -> str:
    text = re.sub(r"[^A-Za-z0-9_-]+", "_", str(value or "invoice")).strip("_")
    return text[:60] or "invoice"


def _round(value: Any) -> float:
    try:
        return round(float(value or 0), 2)
    except (TypeError, ValueError):
        return 0.0


def _int(value: Any) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0
