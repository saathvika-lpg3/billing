from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from services.mysql_source import MySqlSource
from services.sales_calculator import SalesLine


class TransactionRepository:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = Path(db_path or MySqlSource().sqlite_path)

    def save_sales(self, header: dict[str, Any], lines: list[Any], totals: dict[str, float]) -> int:
        now = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            with conn:
                sale_id = self._insert_sales(conn, header, totals, now)
                for line in lines:
                    self._insert_sales_item(conn, sale_id, header, line)
                    self._post_stock(conn, line, header, "sale", qty_in=0.0, qty_out=line.source.qty + line.source.free_qty)
                    self._post_gst(conn, sale_id, header, line, "sales", "output")
                voucher_id = self._insert_voucher(conn, "SALES", sale_id, header, totals, now)
                self._post_sales_ledger(conn, voucher_id, sale_id, header, totals, now)
                return sale_id

    def save_purchase(self, header: dict[str, Any], lines: list[Any], totals: dict[str, float]) -> int:
        now = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            with conn:
                purchase_id = self._insert_purchase(conn, header, totals, now)
                for line in lines:
                    self._insert_purchase_item(conn, purchase_id, header, line)
                    self._post_stock(conn, line, header, "purchase", qty_in=line.source.qty + line.source.free_qty, qty_out=0.0)
                    self._post_gst(conn, purchase_id, header, line, "purchases", "input")
                voucher_id = self._insert_voucher(conn, "PURCHASE", purchase_id, header, totals, now)
                self._post_purchase_ledger(conn, voucher_id, purchase_id, header, totals, now)
                return purchase_id

    def save_order_document(self, header: dict[str, Any], lines: list[Any], totals: dict[str, float]) -> int:
        now = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            with conn:
                document_id = self._insert_order_document(conn, header, totals, now)
                for line in lines:
                    self._insert_order_document_item(conn, document_id, header, line)
                return document_id

    def save_sales_return(self, header: dict[str, Any], lines: list[Any], totals: dict[str, float]) -> int:
        now = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            with conn:
                self._validate_sales_return_limits(conn, header, lines)
                return_id = self._insert_sales_return(conn, header, totals, now)
                for line in lines:
                    stock_qty = self._sales_return_stock_qty(header, line)
                    self._insert_sales_return_item(conn, return_id, header, line)
                    self._post_stock(conn, line, header, "sales_return", qty_in=stock_qty, qty_out=0.0)
                    self._post_gst_reverse(conn, return_id, header, line, "sales_returns", "output", "Sales Return")
                voucher_id = self._insert_voucher(conn, "SALES_RETURN", return_id, header, totals, now)
                self._post_sales_return_ledger(conn, voucher_id, return_id, header, totals, now)
                return return_id

    def save_purchase_return(self, header: dict[str, Any], lines: list[Any], totals: dict[str, float]) -> int:
        now = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            with conn:
                self._validate_purchase_return_limits(conn, header, lines)
                self._validate_purchase_return_stock_available(conn, lines)
                return_id = self._insert_purchase_return(conn, header, totals, now)
                for line in lines:
                    self._insert_purchase_return_item(conn, return_id, header, line)
                    self._post_stock(conn, line, header, "purchase_return", qty_in=0.0, qty_out=line.source.qty)
                    self._post_gst_reverse(conn, return_id, header, line, "purchase_returns", "input", "Purchase Return")
                voucher_id = self._insert_voucher(conn, "PURCHASE_RETURN", return_id, header, totals, now)
                self._post_purchase_return_ledger(conn, voucher_id, return_id, header, totals, now)
                return return_id

    def save_dispatch_return(self, header: dict[str, Any], rows: list[dict[str, Any]]) -> int:
        now = datetime.now().isoformat(timespec="seconds")
        source_table = str(header.get("source_table") or "").strip()
        source_id = int(header.get("source_id") or 0)
        if source_table not in {"sales", "stock_outs"} or source_id <= 0:
            raise ValueError("Choose a sales bill or load challan for dispatch return.")
        if not str(header.get("reason") or "").strip():
            raise ValueError("Return reason is required.")
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            with conn:
                source = self._dispatch_source_record(conn, source_table, source_id)
                source_lines = self._dispatch_source_lines(conn, source_table, source_id)
                selected = self._prepare_dispatch_return_rows(source_table, source_id, source_lines, rows)
                if not selected:
                    raise ValueError("Enter at least one return quantity.")

                sale_return_id = None
                total_dispatched = round(sum(float(row["qty"] or 0) for row in source_lines), 3)
                already_returned = round(sum(float(row["returned_qty"] or 0) for row in source_lines), 3)
                total_returned = round(sum(row["return_qty"] for row in selected), 3)
                total_accepted = round(sum(row["accepted_qty"] for row in selected), 3)
                total_damaged = round(sum(row["damaged_qty"] for row in selected), 3)
                total_value = round(sum(row["line_value"] for row in selected), 2)
                after_returned = already_returned + total_returned
                status_after = "Returned" if total_dispatched and after_returned >= total_dispatched - 0.0001 else "Partially Returned"
                condition = "Reusable" if total_damaged <= 0 else ("Damaged" if total_accepted <= 0 else "Mixed")
                stock_impact = "Return recorded; stock not changed"
                accounting_impact = "No accounting posting from dispatch return"

                if source_table == "sales":
                    sale_return_id = self._insert_dispatch_sales_return(conn, source, header, selected, now)
                    stock_impact = (
                        "Accepted quantity added to saleable stock; damaged quantity recorded separately"
                        if total_damaged > 0
                        else "Accepted quantity added through Sales Return / Credit Note"
                    )
                    accounting_impact = "Sales Return / Credit Note posted"
                elif source_table == "stock_outs":
                    if int(source["stock_effect"] or 0) == 1 and total_accepted > 0:
                        for row in selected:
                            if row["accepted_qty"] > 0:
                                self._post_dispatch_stock(conn, header, row, now)
                        stock_impact = (
                            "Accepted load return added to stock; damaged quantity recorded separately"
                            if total_damaged > 0
                            else "Reusable load return added back to stock"
                        )
                    else:
                        stock_impact = "Load challan was slip-only; stock not changed"
                    accounting_impact = "Load challan has no sales accounting"

                return_no = str(header.get("return_no") or "").strip() or self._next_local_no(conn, "dispatch_returns", "DRTN")
                cursor = conn.execute(
                    """
                    INSERT INTO dispatch_returns(
                        return_no,return_date,source_table,source_id,source_ref,customer_name,route,area,vehicle,
                        dispatch_status_before,dispatch_status_after,total_dispatched_qty,total_returned_qty,
                        total_accepted_qty,damaged_qty,total_value,reason,condition_type,notes,sale_return_id,
                        stock_impact,accounting_impact,status,created_at
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        return_no,
                        header.get("return_date"),
                        source_table,
                        source_id,
                        source["source_ref"],
                        source["customer_name"],
                        source["route"],
                        source["area"],
                        source["vehicle"],
                        source["dispatch_status"],
                        status_after,
                        total_dispatched,
                        total_returned,
                        total_accepted,
                        total_damaged,
                        total_value,
                        header.get("reason"),
                        condition,
                        header.get("notes"),
                        sale_return_id,
                        stock_impact,
                        accounting_impact,
                        "Active",
                        now,
                    ),
                )
                dispatch_return_id = int(cursor.lastrowid)
                for row in selected:
                    self._insert_dispatch_return_item(conn, dispatch_return_id, source_table, source_id, row, header)
                self._update_dispatch_status(conn, source_table, source_id, status_after, header, now)
                return dispatch_return_id

    def save_account_entry(self, mode: str, entry: dict[str, Any]) -> int:
        now = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            with conn:
                if mode == "receipt":
                    source_id = self._insert_receipt(conn, entry, now)
                    voucher_id = self._insert_account_voucher(conn, "RECEIPT", source_id, "receipts", entry, now)
                    self._post_account_ledger(
                        conn,
                        voucher_id,
                        source_id,
                        "receipts",
                        entry,
                        [
                            (self._cash_bank_ledger(entry.get("mode")), entry["amount"], 0.0, ""),
                            (entry.get("party_name") or "Customer", 0.0, entry["amount"], "customer"),
                        ],
                        now,
                    )
                    return source_id
                if mode == "payment":
                    source_id = self._insert_payment(conn, entry, now)
                    voucher_id = self._insert_account_voucher(conn, "PAYMENT", source_id, "payments", entry, now)
                    self._post_account_ledger(
                        conn,
                        voucher_id,
                        source_id,
                        "payments",
                        entry,
                        [
                            (entry.get("party_name") or "Supplier", entry["amount"], 0.0, "supplier"),
                            (self._cash_bank_ledger(entry.get("mode")), 0.0, entry["amount"], ""),
                        ],
                        now,
                    )
                    return source_id
                if mode == "expense":
                    source_id = self._insert_expense(conn, entry, now)
                    voucher_id = self._insert_account_voucher(conn, "EXPENSE", source_id, "expenses", entry, now)
                    self._post_account_ledger(
                        conn,
                        voucher_id,
                        source_id,
                        "expenses",
                        entry,
                        [
                            (entry.get("party_name") or "Expense", entry["amount"], 0.0, ""),
                            (self._cash_bank_ledger(entry.get("mode")), 0.0, entry["amount"], ""),
                        ],
                        now,
                    )
                    return source_id
                if mode == "journal":
                    source_id = self._insert_journal(conn, entry, now)
                    voucher_id = self._insert_account_voucher(conn, "JOURNAL", source_id, "journal_entries", entry, now)
                    self._post_account_ledger(
                        conn,
                        voucher_id,
                        source_id,
                        "journal_entries",
                        entry,
                        [
                            (entry.get("party_name") or "Debit Ledger", entry["amount"], 0.0, ""),
                            (entry.get("credit_ledger") or "Credit Ledger", 0.0, entry["amount"], ""),
                        ],
                        now,
                    )
                    return source_id
                raise ValueError(f"Unsupported account entry mode: {mode}")

    def save_inventory_entry(self, mode: str, header: dict[str, Any], rows: list[dict[str, Any]]) -> int:
        now = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            with conn:
                if mode == "stock_entry":
                    for row in rows:
                        self._apply_stock_delta(conn, row, float(row.get("qty") or 0))
                        conn.execute(
                            "INSERT INTO stock_log(item_id,kind,ref_no,qty_in,qty_out,entry_date,created_at,pack_id) VALUES(?,?,?,?,?,?,?,?)",
                            (
                                row.get("item_id") or None,
                                "stock_entry",
                                header.get("doc_no"),
                                float(row.get("qty") or 0),
                                0,
                                header.get("doc_date"),
                                now,
                                row.get("pack_id") or None,
                            ),
                        )
                    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0] or 0)
                if mode == "transfer":
                    transfer_id = self._insert_stock_transfer(conn, header, rows, now)
                    for row in rows:
                        self._insert_stock_transfer_item(conn, transfer_id, row)
                        conn.execute(
                            "INSERT INTO stock_log(item_id,kind,ref_no,qty_in,qty_out,entry_date,created_at,pack_id) VALUES(?,?,?,?,?,?,?,?)",
                            (
                                row.get("item_id") or None,
                                "stock_transfer",
                                header.get("doc_no"),
                                0,
                                float(row.get("qty") or 0),
                                header.get("doc_date"),
                                now,
                                row.get("pack_id") or None,
                            ),
                        )
                    return transfer_id
                if mode == "adjustment":
                    last_id = 0
                    for row in rows:
                        last_id = self._insert_stock_adjustment(conn, header, row, now)
                        difference = float(row.get("difference") or 0)
                        self._apply_stock_delta(conn, row, difference)
                        conn.execute(
                            "INSERT INTO stock_log(item_id,kind,ref_no,qty_in,qty_out,entry_date,created_at,pack_id) VALUES(?,?,?,?,?,?,?,?)",
                            (
                                row.get("item_id") or None,
                                "stock_adjustment",
                                header.get("doc_no"),
                                max(difference, 0),
                                abs(min(difference, 0)),
                                header.get("doc_date"),
                                now,
                                row.get("pack_id") or None,
                            ),
                        )
                    return last_id
                raise ValueError(f"Unsupported inventory mode: {mode}")

    def _validate_sales_return_limits(self, conn: sqlite3.Connection, header: dict[str, Any], lines: list[Any]) -> None:
        source_doc_id = int(header.get("source_doc_id") or header.get("sale_id") or 0)
        if not source_doc_id:
            return
        for line in lines:
            source_item_id = int(getattr(line.source, "source_item_id", 0) or 0)
            if not source_item_id:
                continue
            original = conn.execute(
                "SELECT qty,free_qty,item_name FROM sales_items WHERE id=? AND sale_id=?",
                (source_item_id, source_doc_id),
            ).fetchone()
            if not original:
                raise ValueError(f"Original sales item not found for {line.source.item_name}.")
            returned = conn.execute(
                """
                SELECT COALESCE(SUM(sri.qty),0) qty, COALESCE(SUM(sri.free_qty),0) free_qty
                FROM sales_return_items sri
                JOIN sales_returns sr ON sr.id=sri.return_id
                WHERE sri.sale_item_id=? AND COALESCE(sr.status,'Active')<>'Cancelled'
                """,
                (source_item_id,),
            ).fetchone()
            left_qty = float(original["qty"] or 0) - float(returned["qty"] or 0)
            left_free = float(original["free_qty"] or 0) - float(returned["free_qty"] or 0)
            if line.source.qty > left_qty + 0.0001 or line.source.free_qty > left_free + 0.0001:
                raise ValueError(f"Return quantity is more than sold quantity for {original['item_name']}.")

    def _validate_purchase_return_limits(self, conn: sqlite3.Connection, header: dict[str, Any], lines: list[Any]) -> None:
        source_doc_id = int(header.get("source_doc_id") or header.get("purchase_id") or 0)
        if not source_doc_id:
            return
        for line in lines:
            source_item_id = int(getattr(line.source, "source_item_id", 0) or 0)
            if not source_item_id:
                continue
            original = conn.execute(
                "SELECT qty,free_qty,item_name FROM purchase_items WHERE id=? AND purchase_id=?",
                (source_item_id, source_doc_id),
            ).fetchone()
            if not original:
                raise ValueError(f"Original purchase item not found for {line.source.item_name}.")
            returned = conn.execute(
                """
                SELECT COALESCE(SUM(pri.qty),0) qty, COALESCE(SUM(pri.free_qty),0) free_qty
                FROM purchase_return_items pri
                JOIN purchase_returns pr ON pr.id=pri.return_id
                WHERE pri.purchase_item_id=? AND COALESCE(pr.status,'Active')<>'Cancelled'
                """,
                (source_item_id,),
            ).fetchone()
            left_qty = float(original["qty"] or 0) - float(returned["qty"] or 0)
            left_free = float(original["free_qty"] or 0) - float(returned["free_qty"] or 0)
            if line.source.qty > left_qty + 0.0001 or line.source.free_qty > left_free + 0.0001:
                raise ValueError(f"Return quantity is more than purchased quantity for {original['item_name']}.")

    def _validate_purchase_return_stock_available(self, conn: sqlite3.Connection, lines: list[Any]) -> None:
        for line in lines:
            qty = float(getattr(line.source, "qty", 0) or 0)
            if qty <= 0:
                continue
            item_id = int(getattr(line.source, "item_id", 0) or 0)
            pack_id = int(getattr(line.source, "pack_id", 0) or 0)
            if pack_id:
                row = conn.execute("SELECT COALESCE(current_stock_qty,0) stock FROM product_packs WHERE id=?", (pack_id,)).fetchone()
                available = float(row["stock"] if row else 0)
                if qty > available + 0.0001:
                    raise ValueError(f"Purchase return stock is not available for {line.source.item_name}. Available: {available:.3f}.")
            elif item_id:
                row = conn.execute("SELECT COALESCE(stock,0) stock FROM items WHERE id=?", (item_id,)).fetchone()
                available = float(row["stock"] if row else 0)
                if qty > available + 0.0001:
                    raise ValueError(f"Purchase return stock is not available for {line.source.item_name}. Available: {available:.3f}.")

    def _sales_return_stock_qty(self, header: dict[str, Any], line: Any) -> float:
        if header.get("stock_qty_from_line"):
            return max(float(getattr(line.source, "stock_qty", 0) or 0), 0.0)
        return max(float(getattr(line.source, "qty", 0) or 0), 0.0)

    def _next_local_no(self, conn: sqlite3.Connection, table: str, prefix: str) -> str:
        row = conn.execute(f"SELECT COALESCE(MAX(id),0)+1 next_id FROM {table}").fetchone()
        return f"{prefix}-{datetime.now():%y%m%d}-{int(row['next_id'] if row else 1):04d}"

    def _dispatch_source_record(self, conn: sqlite3.Connection, source_table: str, source_id: int) -> sqlite3.Row:
        if source_table == "sales":
            row = conn.execute(
                """
                SELECT id,bill_no source_ref,bill_date source_date,customer_id,customer_name,
                       customer_area route,customer_area area,COALESCE(transport_details,'') vehicle,
                       COALESCE(dispatch_status,'Open') dispatch_status,warehouse_id,pay_mode,
                       branch_name,cost_center_name,0 stock_effect
                FROM sales WHERE id=? AND COALESCE(status,'Active')<>'Cancelled'
                """,
                (source_id,),
            ).fetchone()
        else:
            row = conn.execute(
                """
                SELECT id,challan_no source_ref,challan_date source_date,0 customer_id,
                       COALESCE(salesman_name,area,'') customer_name,area route,area area,
                       COALESCE(vehicle_no,'') vehicle,COALESCE(dispatch_status,'Pending Dispatch') dispatch_status,
                       warehouse_id,'' pay_mode,'' branch_name,'' cost_center_name,COALESCE(stock_effect,0) stock_effect
                FROM stock_outs WHERE id=? AND COALESCE(status,'Active')<>'Cancelled'
                """,
                (source_id,),
            ).fetchone()
        if not row:
            raise ValueError("Dispatch source document was not found.")
        return row

    def _dispatch_source_lines(self, conn: sqlite3.Connection, source_table: str, source_id: int) -> list[sqlite3.Row]:
        returned_sql = """
            SELECT dri.source_item_id,
                   SUM(COALESCE(dri.returned_qty,0)) returned_qty,
                   SUM(COALESCE(dri.free_qty,0)) returned_free_qty
            FROM dispatch_return_items dri
            JOIN dispatch_returns dr ON dr.id=dri.dispatch_return_id
            WHERE dri.source_table=? AND dri.source_id=? AND COALESCE(dr.status,'Active')<>'Cancelled'
            GROUP BY dri.source_item_id
        """
        if source_table == "sales":
            rows = conn.execute(
                f"""
                SELECT si.id source_item_id,si.warehouse_id,si.item_id,si.pack_id,
                       COALESCE(si.pack_display_snapshot,'') pack_display_snapshot,
                       COALESCE(si.pack_size_snapshot,1) pack_size_snapshot,
                       si.item_name,si.unit,'' company,COALESCE(si.qty,0) qty,
                       COALESCE(si.free_qty,0) free_qty,COALESCE(si.rate,0) rate,
                       COALESCE(si.gst,0) gst,COALESCE(si.igst,0) original_igst,
                       COALESCE(si.hsn,'') hsn,COALESCE(si.mrp,0) mrp,
                       COALESCE(si.total,COALESCE(si.qty,0)*COALESCE(si.rate,0)) value,
                       COALESCE(ret.returned_qty,0) returned_qty,
                       COALESCE(ret.returned_free_qty,0) returned_free_qty
                FROM sales_items si
                LEFT JOIN ({returned_sql}) ret ON ret.source_item_id=si.id
                WHERE si.sale_id=?
                ORDER BY si.id
                """,
                (source_table, source_id, source_id),
            ).fetchall()
        else:
            rows = conn.execute(
                f"""
                SELECT soi.id source_item_id,soi.warehouse_id,soi.item_id,soi.pack_id,
                       COALESCE(soi.pack_display_snapshot,'') pack_display_snapshot,
                       COALESCE(soi.pack_size_snapshot,1) pack_size_snapshot,
                       soi.item_name,soi.unit,'' company,COALESCE(soi.qty,0) qty,
                       COALESCE(soi.free_qty,0) free_qty,COALESCE(soi.mrp,0) rate,
                       0 gst,0 original_igst,COALESCE(soi.hsn,'') hsn,COALESCE(soi.mrp,0) mrp,
                       COALESCE(soi.qty,0)*COALESCE(soi.mrp,0) value,
                       COALESCE(ret.returned_qty,0) returned_qty,
                       COALESCE(ret.returned_free_qty,0) returned_free_qty
                FROM stock_out_items soi
                LEFT JOIN ({returned_sql}) ret ON ret.source_item_id=soi.id
                WHERE soi.stock_out_id=?
                ORDER BY soi.id
                """,
                (source_table, source_id, source_id),
            ).fetchall()
        if not rows:
            raise ValueError("No dispatch items are available for return.")
        return list(rows)

    def _prepare_dispatch_return_rows(
        self,
        source_table: str,
        source_id: int,
        source_lines: list[sqlite3.Row],
        rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        by_id = {int(row["source_item_id"]): row for row in source_lines}
        selected: list[dict[str, Any]] = []
        for row in rows:
            source_item_id = int(row.get("source_item_id") or 0)
            if source_item_id not in by_id:
                continue
            line = by_id[source_item_id]
            qty = float(row.get("return_qty") or 0)
            free_qty = float(row.get("return_free_qty") or 0)
            damaged = float(row.get("damaged_qty") or 0)
            if qty < -0.0001 or free_qty < -0.0001 or damaged < -0.0001:
                raise ValueError("Return and damaged quantities cannot be negative.")
            available_qty = max(0.0, float(line["qty"] or 0) - float(line["returned_qty"] or 0))
            available_free = max(0.0, float(line["free_qty"] or 0) - float(line["returned_free_qty"] or 0))
            if qty > available_qty + 0.0001 or free_qty > available_free + 0.0001:
                raise ValueError(f"Returned quantity cannot exceed dispatched quantity for {line['item_name']}.")
            if damaged > qty + 0.0001:
                raise ValueError(f"Damaged quantity cannot exceed returned quantity for {line['item_name']}.")
            if qty <= 0 and free_qty <= 0:
                continue
            accepted = max(0.0, qty - damaged)
            condition = "Reusable" if damaged <= 0 else ("Damaged" if accepted <= 0 else "Mixed")
            line_value = (float(line["value"] or 0) / float(line["qty"] or 1)) * qty if float(line["qty"] or 0) > 0 else 0.0
            selected.append(
                {
                    "source_table": source_table,
                    "source_id": source_id,
                    "source_item_id": source_item_id,
                    "warehouse_id": line["warehouse_id"],
                    "item_id": line["item_id"],
                    "pack_id": line["pack_id"],
                    "pack_display_snapshot": line["pack_display_snapshot"],
                    "pack_size_snapshot": line["pack_size_snapshot"],
                    "item_name": line["item_name"],
                    "unit": line["unit"],
                    "company": line["company"],
                    "dispatched_qty": float(line["qty"] or 0),
                    "free_qty": free_qty,
                    "return_qty": qty,
                    "accepted_qty": accepted,
                    "damaged_qty": damaged,
                    "rate": float(line["rate"] or 0),
                    "value": float(line["value"] or 0),
                    "line_value": round(line_value, 2),
                    "condition_type": condition,
                    "reason": str(row.get("reason") or ""),
                    "remarks": str(row.get("remarks") or ""),
                    "hsn": line["hsn"],
                    "mrp": float(line["mrp"] or 0),
                    "gst": float(line["gst"] or 0),
                    "original_igst": float(line["original_igst"] or 0),
                }
            )
        return selected

    def _insert_dispatch_sales_return(
        self,
        conn: sqlite3.Connection,
        source: sqlite3.Row,
        header: dict[str, Any],
        selected: list[dict[str, Any]],
        now: str,
    ) -> int:
        return_header = {
            "doc_no": str(header.get("credit_note_no") or "").strip() or self._next_local_no(conn, "sales_returns", "RET"),
            "doc_date": header.get("return_date"),
            "source_doc_id": header.get("source_id"),
            "sale_id": header.get("source_id"),
            "party_type": "customer",
            "party_id": source["customer_id"],
            "party_name": source["customer_name"],
            "warehouse_id": source["warehouse_id"],
            "payment": source["pay_mode"],
            "status": "Active",
            "notes": header.get("reason"),
            "branch": source["branch_name"],
            "cost_center": source["cost_center_name"],
            "stock_qty_from_line": True,
        }
        computed_lines = [self._dispatch_sales_return_line(row) for row in selected]
        totals = self._totals_from_computed_lines(computed_lines)
        return_id = self._insert_sales_return(conn, return_header, totals, now)
        for line in computed_lines:
            stock_qty = self._sales_return_stock_qty(return_header, line)
            self._insert_sales_return_item(conn, return_id, return_header, line)
            if stock_qty > 0:
                self._post_stock(conn, line, return_header, "sales_return", qty_in=stock_qty, qty_out=0.0)
            self._post_gst_reverse(conn, return_id, return_header, line, "sales_returns", "output", "Sales Return")
        voucher_id = self._insert_voucher(conn, "SALES_RETURN", return_id, return_header, totals, now)
        self._post_sales_return_ledger(conn, voucher_id, return_id, return_header, totals, now)
        return return_id

    def _dispatch_sales_return_line(self, row: dict[str, Any]) -> Any:
        source = SalesLine(
            item_name=str(row["item_name"] or ""),
            pack_name=str(row["pack_display_snapshot"] or ""),
            hsn=str(row["hsn"] or ""),
            unit=str(row["unit"] or "PCS"),
            qty=float(row["return_qty"] or 0),
            free_qty=float(row["free_qty"] or 0),
            mrp=float(row["mrp"] or 0),
            rate=float(row["rate"] or 0),
            scheme=0,
            discount_amount=0,
            gst_rate=float(row["gst"] or 0),
            item_id=int(row["item_id"] or 0),
            pack_id=int(row["pack_id"] or 0),
            pack_size=float(row["pack_size_snapshot"] or 1),
            stock_qty=float(row["accepted_qty"] or 0),
            source_item_id=int(row["source_item_id"] or 0),
            source_doc_id=int(row["source_id"] or 0),
        )
        taxable = round(max(source.qty - source.free_qty, 0) * source.rate, 2)
        gst_total = round(taxable * source.gst_rate / 100, 2)
        if float(row["original_igst"] or 0) > 0:
            cgst = 0.0
            sgst = 0.0
            igst = gst_total
        else:
            cgst = round(gst_total / 2, 2)
            sgst = round(gst_total - cgst, 2)
            igst = 0.0
        return SimpleNamespace(source=source, gross=taxable, taxable=taxable, cgst=cgst, sgst=sgst, igst=igst, gst_total=gst_total, line_total=round(taxable + gst_total, 2))

    def _totals_from_computed_lines(self, lines: list[Any]) -> dict[str, float]:
        taxable = round(sum(float(row.taxable) for row in lines), 2)
        cgst = round(sum(float(row.cgst) for row in lines), 2)
        sgst = round(sum(float(row.sgst) for row in lines), 2)
        igst = round(sum(float(row.igst) for row in lines), 2)
        total = round(sum(float(row.line_total) for row in lines), 2)
        rounded = round(total)
        return {
            "gross": taxable,
            "discount": 0.0,
            "taxable": taxable,
            "cgst": cgst,
            "sgst": sgst,
            "igst": igst,
            "gst_total": round(cgst + sgst + igst, 2),
            "round_off": round(rounded - total, 2),
            "grand_total": float(rounded),
        }

    def _post_dispatch_stock(self, conn: sqlite3.Connection, header: dict[str, Any], row: dict[str, Any], now: str) -> None:
        item_id = row.get("item_id") or None
        pack_id = row.get("pack_id") or None
        qty = float(row.get("accepted_qty") or 0)
        if item_id:
            conn.execute("UPDATE items SET stock=COALESCE(stock,0)+? WHERE id=?", (qty, item_id))
        if pack_id:
            conn.execute("UPDATE product_packs SET current_stock_qty=COALESCE(current_stock_qty,0)+? WHERE id=?", (qty, pack_id))
        conn.execute(
            "INSERT INTO stock_log(item_id,kind,ref_no,qty_in,qty_out,entry_date,created_at,pack_id) VALUES(?,?,?,?,?,?,?,?)",
            (item_id, "Dispatch Return", header.get("return_no"), qty, 0.0, header.get("return_date"), now, pack_id),
        )

    def _insert_dispatch_return_item(
        self,
        conn: sqlite3.Connection,
        dispatch_return_id: int,
        source_table: str,
        source_id: int,
        row: dict[str, Any],
        header: dict[str, Any],
    ) -> None:
        conn.execute(
            """
            INSERT INTO dispatch_return_items(
                dispatch_return_id,source_table,source_id,source_item_id,item_id,item_name,unit,company,
                dispatched_qty,free_qty,returned_qty,accepted_qty,damaged_qty,rate,value,condition_type,
                reason,remarks,warehouse_id,pack_id,pack_display_snapshot,pack_size_snapshot
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                dispatch_return_id,
                source_table,
                source_id,
                row["source_item_id"],
                row["item_id"],
                row["item_name"],
                row["unit"],
                row["company"],
                row["dispatched_qty"],
                row["free_qty"],
                row["return_qty"],
                row["accepted_qty"],
                row["damaged_qty"],
                row["rate"],
                row["line_value"],
                row["condition_type"],
                row["reason"] or header.get("reason"),
                row["remarks"] or header.get("notes"),
                row["warehouse_id"],
                row["pack_id"],
                row["pack_display_snapshot"],
                row["pack_size_snapshot"],
            ),
        )

    def _update_dispatch_status(
        self,
        conn: sqlite3.Connection,
        source_table: str,
        source_id: int,
        status_after: str,
        header: dict[str, Any],
        now: str,
    ) -> None:
        if source_table == "sales":
            conn.execute(
                "UPDATE sales SET dispatch_status=?,dispatch_status_at=?,dispatch_status_note=? WHERE id=?",
                (status_after, now, header.get("reason"), source_id),
            )
        elif source_table == "stock_outs":
            conn.execute(
                "UPDATE stock_outs SET dispatch_status=?,dispatch_status_at=?,dispatch_status_note=? WHERE id=?",
                (status_after, now, header.get("reason"), source_id),
            )

    def _insert_sales(self, conn: sqlite3.Connection, header: dict[str, Any], totals: dict[str, float], now: str) -> int:
        cursor = conn.execute(
            """
            INSERT INTO sales(
                bill_no,bill_date,customer_id,customer_name,customer_area,warehouse_id,pay_mode,
                taxable,gst_total,cgst_total,sgst_total,igst_total,round_off,grand_total,status,
                created_at,po_no,transport_details,credit_terms,branch_name,cost_center_name,
                employee_name,shipping_address
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                header.get("bill_no"),
                header.get("bill_date"),
                header.get("customer_id") or None,
                header.get("customer_name"),
                header.get("customer_area"),
                header.get("warehouse_id") or None,
                header.get("payment"),
                totals["taxable"],
                totals["gst_total"],
                totals["cgst"],
                totals["sgst"],
                totals["igst"],
                totals["round_off"],
                totals["grand_total"],
                "Active",
                now,
                header.get("po_no"),
                header.get("transport"),
                header.get("credit_terms"),
                header.get("branch"),
                header.get("cost_center"),
                header.get("employee"),
                header.get("shipping"),
            ),
        )
        return int(cursor.lastrowid)

    def _insert_order_document(self, conn: sqlite3.Connection, header: dict[str, Any], totals: dict[str, float], now: str) -> int:
        cursor = conn.execute(
            """
            INSERT INTO order_documents(
                doc_no,doc_date,doc_type,party_type,party_id,party_name,area,warehouse_id,
                pay_mode,valid_until,delivery_date,taxable,gst_total,cgst_total,sgst_total,
                igst_total,round_off,grand_total,status,notes,created_at,employee_name
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                header.get("doc_no"),
                header.get("doc_date"),
                header.get("doc_type"),
                header.get("party_type"),
                header.get("party_id") or None,
                header.get("party_name"),
                header.get("area"),
                header.get("warehouse_id") or None,
                header.get("payment"),
                header.get("valid_until"),
                header.get("delivery_date"),
                totals["taxable"],
                totals["gst_total"],
                totals["cgst"],
                totals["sgst"],
                totals["igst"],
                totals["round_off"],
                totals["grand_total"],
                header.get("status") or "Open",
                header.get("notes"),
                now,
                header.get("employee"),
            ),
        )
        return int(cursor.lastrowid)

    def _insert_order_document_item(self, conn: sqlite3.Connection, document_id: int, header: dict[str, Any], line: Any) -> None:
        conn.execute(
            """
            INSERT INTO order_document_items(
                order_document_id,item_id,item_name,hsn,unit,mrp,qty,free_qty,rate,gst,taxable,
                gst_amt,cgst,sgst,igst,total,discount,warehouse_id,pack_id,pack_display_snapshot,
                pack_size_snapshot,price_level
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                document_id,
                line.source.item_id or None,
                line.source.item_name,
                line.source.hsn,
                line.source.unit,
                line.source.mrp,
                line.source.qty,
                line.source.free_qty,
                line.source.rate,
                line.source.gst_rate,
                line.taxable,
                line.gst_total,
                line.cgst,
                line.sgst,
                line.igst,
                line.line_total,
                line.source.discount_amount,
                header.get("warehouse_id") or None,
                line.source.pack_id or None,
                line.source.pack_name,
                line.source.pack_size,
                header.get("price_level"),
            ),
        )

    def _insert_sales_item(self, conn: sqlite3.Connection, sale_id: int, header: dict[str, Any], line: Any) -> None:
        conn.execute(
            """
            INSERT INTO sales_items(
                sale_id,item_id,item_name,hsn,unit,mrp,qty,free_qty,rate,gst,taxable,gst_amt,
                cgst,sgst,igst,total,discount,warehouse_id,pack_id,pack_display_snapshot,
                pack_size_snapshot,price_level
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                sale_id,
                line.source.item_id or None,
                line.source.item_name,
                line.source.hsn,
                line.source.unit,
                line.source.mrp,
                line.source.qty,
                line.source.free_qty,
                line.source.rate,
                line.source.gst_rate,
                line.taxable,
                line.gst_total,
                line.cgst,
                line.sgst,
                line.igst,
                line.line_total,
                line.source.discount_amount,
                header.get("warehouse_id") or None,
                line.source.pack_id or None,
                line.source.pack_name,
                line.source.pack_size,
                header.get("price_level"),
            ),
        )

    def _insert_purchase(self, conn: sqlite3.Connection, header: dict[str, Any], totals: dict[str, float], now: str) -> int:
        cursor = conn.execute(
            """
            INSERT INTO purchases(
                bill_no,bill_date,supplier_id,warehouse_id,supplier_name,pay_mode,taxable,
                gst_total,cgst_total,sgst_total,igst_total,grand_total,status,created_at,
                branch_name,cost_center_name,employee_name,round_off
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                header.get("bill_no"),
                header.get("bill_date"),
                header.get("supplier_id") or None,
                header.get("warehouse_id") or None,
                header.get("supplier_name"),
                header.get("payment"),
                totals["taxable"],
                totals["gst_total"],
                totals["cgst"],
                totals["sgst"],
                totals["igst"],
                totals["grand_total"],
                "Active",
                now,
                header.get("branch"),
                header.get("cost_center"),
                header.get("employee"),
                totals["round_off"],
            ),
        )
        return int(cursor.lastrowid)

    def _insert_sales_return(self, conn: sqlite3.Connection, header: dict[str, Any], totals: dict[str, float], now: str) -> int:
        cursor = conn.execute(
            """
            INSERT INTO sales_returns(
                return_no,return_date,sale_id,customer_id,customer_name,warehouse_id,taxable,gst_total,
                cgst_total,sgst_total,igst_total,round_off,grand_total,reason,status,created_at,
                branch_name,cost_center_name
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                header.get("doc_no"),
                header.get("doc_date"),
                header.get("source_doc_id") or header.get("sale_id") or None,
                header.get("party_id") or None,
                header.get("party_name"),
                header.get("warehouse_id") or None,
                totals["taxable"],
                totals["gst_total"],
                totals["cgst"],
                totals["sgst"],
                totals["igst"],
                totals["round_off"],
                totals["grand_total"],
                header.get("notes"),
                header.get("status") or "Active",
                now,
                header.get("branch"),
                header.get("cost_center"),
            ),
        )
        return int(cursor.lastrowid)

    def _insert_sales_return_item(self, conn: sqlite3.Connection, return_id: int, header: dict[str, Any], line: Any) -> None:
        conn.execute(
            """
            INSERT INTO sales_return_items(
                return_id,sale_item_id,item_id,item_name,hsn,unit,mrp,qty,free_qty,rate,gst,taxable,
                gst_amt,cgst,sgst,igst,total,stock_qty,warehouse_id,pack_id,
                pack_display_snapshot,pack_size_snapshot
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                return_id,
                line.source.source_item_id or None,
                line.source.item_id or None,
                line.source.item_name,
                line.source.hsn,
                line.source.unit,
                line.source.mrp,
                line.source.qty,
                line.source.free_qty,
                line.source.rate,
                line.source.gst_rate,
                line.taxable,
                line.gst_total,
                line.cgst,
                line.sgst,
                line.igst,
                line.line_total,
                self._sales_return_stock_qty(header, line),
                header.get("warehouse_id") or None,
                line.source.pack_id or None,
                line.source.pack_name,
                line.source.pack_size,
            ),
        )

    def _insert_purchase_return(self, conn: sqlite3.Connection, header: dict[str, Any], totals: dict[str, float], now: str) -> int:
        cursor = conn.execute(
            """
            INSERT INTO purchase_returns(
                return_no,return_date,purchase_id,supplier_id,supplier_name,warehouse_id,taxable,gst_total,
                cgst_total,sgst_total,igst_total,grand_total,reason,status,created_at,
                branch_name,cost_center_name,round_off
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                header.get("doc_no"),
                header.get("doc_date"),
                header.get("source_doc_id") or header.get("purchase_id") or None,
                header.get("party_id") or None,
                header.get("party_name"),
                header.get("warehouse_id") or None,
                totals["taxable"],
                totals["gst_total"],
                totals["cgst"],
                totals["sgst"],
                totals["igst"],
                totals["grand_total"],
                header.get("notes"),
                header.get("status") or "Active",
                now,
                header.get("branch"),
                header.get("cost_center"),
                totals["round_off"],
            ),
        )
        return int(cursor.lastrowid)

    def _insert_purchase_return_item(self, conn: sqlite3.Connection, return_id: int, header: dict[str, Any], line: Any) -> None:
        conn.execute(
            """
            INSERT INTO purchase_return_items(
                return_id,purchase_item_id,item_id,item_name,hsn,unit,mrp,qty,free_qty,rate,gst,taxable,
                gst_amt,cgst,sgst,igst,total,warehouse_id,pack_id,pack_display_snapshot,
                pack_size_snapshot
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                return_id,
                line.source.source_item_id or None,
                line.source.item_id or None,
                line.source.item_name,
                line.source.hsn,
                line.source.unit,
                line.source.mrp,
                line.source.qty,
                line.source.free_qty,
                line.source.rate,
                line.source.gst_rate,
                line.taxable,
                line.gst_total,
                line.cgst,
                line.sgst,
                line.igst,
                line.line_total,
                header.get("warehouse_id") or None,
                line.source.pack_id or None,
                line.source.pack_name,
                line.source.pack_size,
            ),
        )

    def _insert_receipt(self, conn: sqlite3.Connection, entry: dict[str, Any], now: str) -> int:
        cursor = conn.execute(
            """
            INSERT INTO receipts(
                receipt_no,receipt_date,customer_id,customer_name,amount,mode,notes,status,
                created_at,branch_name,cost_center_name
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                entry.get("doc_no"),
                entry.get("entry_date"),
                entry.get("party_id") or None,
                entry.get("party_name"),
                entry["amount"],
                entry.get("mode"),
                entry.get("notes"),
                entry.get("status") or "Active",
                now,
                entry.get("branch"),
                entry.get("cost_center"),
            ),
        )
        return int(cursor.lastrowid)

    def _insert_payment(self, conn: sqlite3.Connection, entry: dict[str, Any], now: str) -> int:
        cursor = conn.execute(
            """
            INSERT INTO payments(
                payment_no,payment_date,supplier_id,supplier_name,amount,mode,notes,status,
                created_at,branch_name,cost_center_name
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                entry.get("doc_no"),
                entry.get("entry_date"),
                entry.get("party_id") or None,
                entry.get("party_name"),
                entry["amount"],
                entry.get("mode"),
                entry.get("notes"),
                entry.get("status") or "Active",
                now,
                entry.get("branch"),
                entry.get("cost_center"),
            ),
        )
        return int(cursor.lastrowid)

    def _insert_expense(self, conn: sqlite3.Connection, entry: dict[str, Any], now: str) -> int:
        cursor = conn.execute(
            """
            INSERT INTO expenses(
                expense_no,expense_date,ledger_id,ledger_name,amount,mode,paid_to,notes,status,
                created_at,branch_name,cost_center_name
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                entry.get("doc_no"),
                entry.get("entry_date"),
                entry.get("party_id") or None,
                entry.get("party_name"),
                entry["amount"],
                entry.get("mode"),
                entry.get("paid_to"),
                entry.get("notes"),
                entry.get("status") or "Active",
                now,
                entry.get("branch"),
                entry.get("cost_center"),
            ),
        )
        return int(cursor.lastrowid)

    def _insert_journal(self, conn: sqlite3.Connection, entry: dict[str, Any], now: str) -> int:
        cursor = conn.execute(
            """
            INSERT INTO journal_entries(
                entry_no,entry_date,voucher_type,debit_ledger,credit_ledger,amount,narration,
                status,created_at,cost_center_name,branch_name
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                entry.get("doc_no"),
                entry.get("entry_date"),
                entry.get("voucher_type"),
                entry.get("party_name"),
                entry.get("credit_ledger"),
                entry["amount"],
                entry.get("notes"),
                entry.get("status") or "Active",
                now,
                entry.get("cost_center"),
                entry.get("branch"),
            ),
        )
        return int(cursor.lastrowid)

    def _insert_stock_transfer(self, conn: sqlite3.Connection, header: dict[str, Any], rows: list[dict[str, Any]], now: str) -> int:
        total_qty = sum(float(row.get("qty") or 0) for row in rows)
        cursor = conn.execute(
            """
            INSERT INTO stock_transfers(
                transfer_no,transfer_date,from_warehouse_id,to_warehouse_id,notes,total_qty,status,created_at
            ) VALUES(?,?,?,?,?,?,?,?)
            """,
            (
                header.get("doc_no"),
                header.get("doc_date"),
                header.get("from_warehouse_id") or None,
                header.get("to_warehouse_id") or None,
                header.get("notes"),
                total_qty,
                header.get("status") or "Active",
                now,
            ),
        )
        return int(cursor.lastrowid)

    def _insert_stock_transfer_item(self, conn: sqlite3.Connection, transfer_id: int, row: dict[str, Any]) -> None:
        conn.execute(
            """
            INSERT INTO stock_transfer_items(
                stock_transfer_id,item_id,item_name,hsn,unit,qty,mrp,pack_id,
                pack_display_snapshot,pack_size_snapshot
            ) VALUES(?,?,?,?,?,?,?,?,?,?)
            """,
            (
                transfer_id,
                row.get("item_id") or None,
                row.get("item_name"),
                row.get("hsn"),
                row.get("unit"),
                row.get("qty"),
                row.get("mrp") or 0,
                row.get("pack_id") or None,
                row.get("pack_name"),
                row.get("pack_size") or 1,
            ),
        )

    def _insert_stock_adjustment(self, conn: sqlite3.Connection, header: dict[str, Any], row: dict[str, Any], now: str) -> int:
        cursor = conn.execute(
            """
            INSERT INTO stock_adjustments(
                adj_no,adj_date,warehouse_id,item_id,item_name,old_stock,counted_stock,
                difference_qty,reason,created_at,pack_id,pack_display_snapshot,pack_size_snapshot
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                header.get("doc_no"),
                header.get("doc_date"),
                header.get("from_warehouse_id") or None,
                row.get("item_id") or None,
                row.get("item_name"),
                row.get("current"),
                row.get("qty"),
                row.get("difference"),
                row.get("reason"),
                now,
                row.get("pack_id") or None,
                row.get("pack_name"),
                row.get("pack_size") or 1,
            ),
        )
        return int(cursor.lastrowid)

    def _apply_stock_delta(self, conn: sqlite3.Connection, row: dict[str, Any], delta: float) -> None:
        item_id = row.get("item_id") or None
        pack_id = row.get("pack_id") or None
        if item_id:
            conn.execute("UPDATE items SET stock=COALESCE(stock,0)+? WHERE id=?", (delta, item_id))
        if pack_id:
            conn.execute("UPDATE product_packs SET current_stock_qty=COALESCE(current_stock_qty,0)+? WHERE id=?", (delta, pack_id))

    def _insert_purchase_item(self, conn: sqlite3.Connection, purchase_id: int, header: dict[str, Any], line: Any) -> None:
        conn.execute(
            """
            INSERT INTO purchase_items(
                purchase_id,item_id,item_name,unit,mrp,qty,free_qty,rate,gst,taxable,gst_amt,
                cgst,sgst,igst,total,hsn,warehouse_id,pack_id,pack_display_snapshot,
                pack_size_snapshot,price_level
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                purchase_id,
                line.source.item_id or None,
                line.source.item_name,
                line.source.unit,
                line.source.mrp,
                line.source.qty,
                line.source.free_qty,
                line.source.rate,
                line.source.gst_rate,
                line.taxable,
                line.gst_total,
                line.cgst,
                line.sgst,
                line.igst,
                line.line_total,
                line.source.hsn,
                header.get("warehouse_id") or None,
                line.source.pack_id or None,
                line.source.pack_name,
                line.source.pack_size,
                header.get("price_level"),
            ),
        )

    def _post_stock(
        self,
        conn: sqlite3.Connection,
        line: Any,
        header: dict[str, Any],
        kind: str,
        *,
        qty_in: float,
        qty_out: float,
    ) -> None:
        item_id = line.source.item_id or None
        pack_id = line.source.pack_id or None
        if item_id:
            delta = float(qty_in) - float(qty_out)
            conn.execute("UPDATE items SET stock=COALESCE(stock,0)+? WHERE id=?", (delta, item_id))
        if pack_id:
            delta = float(qty_in) - float(qty_out)
            conn.execute("UPDATE product_packs SET current_stock_qty=COALESCE(current_stock_qty,0)+? WHERE id=?", (delta, pack_id))
        conn.execute(
            "INSERT INTO stock_log(item_id,kind,ref_no,qty_in,qty_out,entry_date,created_at,pack_id) VALUES(?,?,?,?,?,?,?,?)",
            (
                item_id,
                kind,
                header.get("bill_no") or header.get("doc_no"),
                qty_in,
                qty_out,
                header.get("bill_date") or header.get("doc_date"),
                datetime.now().isoformat(timespec="seconds"),
                pack_id,
            ),
        )

    def _post_gst(
        self,
        conn: sqlite3.Connection,
        source_id: int,
        header: dict[str, Any],
        line: Any,
        source_table: str,
        input_output: str,
    ) -> None:
        conn.execute(
            """
            INSERT INTO gst_postings(
                voucher_date,source_table,source_id,source_ref,party_type,party_id,hsn_sac,
                tax_rate,taxable,cgst,sgst,igst,cess,input_output,transaction_type,status,
                created_at,item_id,item_name,unit,qty,free_qty,branch_name
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                header.get("bill_date"),
                source_table,
                source_id,
                header.get("bill_no"),
                header.get("party_type"),
                header.get("party_id") or None,
                line.source.hsn,
                line.source.gst_rate,
                line.taxable,
                line.cgst,
                line.sgst,
                line.igst,
                0,
                input_output,
                "Sales" if source_table == "sales" else "Purchase",
                "Active",
                datetime.now().isoformat(timespec="seconds"),
                line.source.item_id or None,
                line.source.item_name,
                line.source.unit,
                line.source.qty,
                line.source.free_qty,
                header.get("branch"),
            ),
        )

    def _post_gst_reverse(
        self,
        conn: sqlite3.Connection,
        source_id: int,
        header: dict[str, Any],
        line: Any,
        source_table: str,
        input_output: str,
        transaction_type: str,
    ) -> None:
        conn.execute(
            """
            INSERT INTO gst_postings(
                voucher_date,source_table,source_id,source_ref,party_type,party_id,hsn_sac,
                tax_rate,taxable,cgst,sgst,igst,cess,input_output,transaction_type,status,
                created_at,item_id,item_name,unit,qty,free_qty,branch_name
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                header.get("doc_date"),
                source_table,
                source_id,
                header.get("doc_no"),
                header.get("party_type"),
                header.get("party_id") or None,
                line.source.hsn,
                line.source.gst_rate,
                -abs(line.taxable),
                -abs(line.cgst),
                -abs(line.sgst),
                -abs(line.igst),
                0,
                input_output,
                transaction_type,
                "Active",
                datetime.now().isoformat(timespec="seconds"),
                line.source.item_id or None,
                line.source.item_name,
                line.source.unit,
                line.source.qty,
                line.source.free_qty,
                header.get("branch"),
            ),
        )

    def _insert_voucher(
        self,
        conn: sqlite3.Connection,
        voucher_type: str,
        source_id: int,
        header: dict[str, Any],
        totals: dict[str, float],
        now: str,
    ) -> int:
        cursor = conn.execute(
            """
            INSERT INTO voucher_headers(
                voucher_type_code,voucher_no,voucher_date,source_table,source_id,source_ref,
                party_type,party_id,party_name,status,total_debit,total_credit,narration,
                created_at,approval_status,branch_name
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                voucher_type,
                header.get("bill_no") or header.get("doc_no"),
                header.get("bill_date") or header.get("doc_date"),
                self._voucher_source_table(voucher_type),
                source_id,
                header.get("bill_no") or header.get("doc_no"),
                header.get("party_type"),
                header.get("party_id") or None,
                header.get("party_name"),
                "Active",
                totals["grand_total"],
                totals["grand_total"],
                f"{voucher_type.title()} auto posting",
                now,
                "Approved",
                header.get("branch"),
            ),
        )
        return int(cursor.lastrowid)

    def _post_sales_ledger(
        self,
        conn: sqlite3.Connection,
        voucher_id: int,
        sale_id: int,
        header: dict[str, Any],
        totals: dict[str, float],
        now: str,
    ) -> None:
        debit_ledger = "Cash" if str(header.get("payment")).lower() == "cash" else header.get("party_name") or "Customer"
        rows = [
            (debit_ledger, totals["grand_total"], 0.0, "customer"),
            ("Sales", 0.0, totals["taxable"], ""),
            ("Output GST", 0.0, totals["gst_total"], ""),
        ]
        self._insert_ledger_rows(conn, voucher_id, sale_id, "sales", header, rows, now)

    def _post_purchase_ledger(
        self,
        conn: sqlite3.Connection,
        voucher_id: int,
        purchase_id: int,
        header: dict[str, Any],
        totals: dict[str, float],
        now: str,
    ) -> None:
        credit_ledger = "Cash" if str(header.get("payment")).lower() == "cash" else header.get("party_name") or "Supplier"
        rows = [
            ("Purchases", totals["taxable"], 0.0, ""),
            ("Input GST", totals["gst_total"], 0.0, ""),
            (credit_ledger, 0.0, totals["grand_total"], "supplier"),
        ]
        self._insert_ledger_rows(conn, voucher_id, purchase_id, "purchases", header, rows, now)

    def _post_sales_return_ledger(
        self,
        conn: sqlite3.Connection,
        voucher_id: int,
        return_id: int,
        header: dict[str, Any],
        totals: dict[str, float],
        now: str,
    ) -> None:
        credit_ledger = header.get("party_name") or "Customer"
        rows = [
            ("Sales Returns", totals["taxable"], 0.0, ""),
            ("Output GST", totals["gst_total"], 0.0, ""),
            (credit_ledger, 0.0, totals["grand_total"], "customer"),
        ]
        self._insert_ledger_rows(conn, voucher_id, return_id, "sales_returns", header, rows, now, ref_key="doc_no", date_key="doc_date")

    def _post_purchase_return_ledger(
        self,
        conn: sqlite3.Connection,
        voucher_id: int,
        return_id: int,
        header: dict[str, Any],
        totals: dict[str, float],
        now: str,
    ) -> None:
        debit_ledger = header.get("party_name") or "Supplier"
        rows = [
            (debit_ledger, totals["grand_total"], 0.0, "supplier"),
            ("Purchase Returns", 0.0, totals["taxable"], ""),
            ("Input GST", 0.0, totals["gst_total"], ""),
        ]
        self._insert_ledger_rows(conn, voucher_id, return_id, "purchase_returns", header, rows, now, ref_key="doc_no", date_key="doc_date")

    def _insert_ledger_rows(
        self,
        conn: sqlite3.Connection,
        voucher_id: int,
        source_id: int,
        source_table: str,
        header: dict[str, Any],
        rows: list[tuple[str, float, float, str]],
        now: str,
        *,
        ref_key: str = "bill_no",
        date_key: str = "bill_date",
    ) -> None:
        for ledger_name, debit, credit, party_type in rows:
            if round(float(debit) + float(credit), 2) == 0:
                continue
            conn.execute(
                """
                INSERT INTO ledger_postings(
                    voucher_id,voucher_date,ledger_name,debit,credit,party_type,party_id,
                    source_table,source_id,source_ref,status,created_at,cost_center_name,branch_name
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    voucher_id,
                    header.get(date_key),
                    ledger_name,
                    debit,
                    credit,
                    party_type,
                    header.get("party_id") if party_type else None,
                    source_table,
                    source_id,
                    header.get(ref_key),
                    "Active",
                    now,
                    header.get("cost_center"),
                    header.get("branch"),
                ),
            )

    def _insert_account_voucher(
        self,
        conn: sqlite3.Connection,
        voucher_type: str,
        source_id: int,
        source_table: str,
        entry: dict[str, Any],
        now: str,
    ) -> int:
        cursor = conn.execute(
            """
            INSERT INTO voucher_headers(
                voucher_type_code,voucher_no,voucher_date,source_table,source_id,source_ref,
                party_type,party_id,party_name,status,total_debit,total_credit,narration,
                created_at,approval_status,branch_name
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                voucher_type,
                entry.get("doc_no"),
                entry.get("entry_date"),
                source_table,
                source_id,
                entry.get("doc_no"),
                entry.get("party_type"),
                entry.get("party_id") or None,
                entry.get("party_name"),
                entry.get("status") or "Active",
                entry["amount"],
                entry["amount"],
                entry.get("notes"),
                now,
                "Approved",
                entry.get("branch"),
            ),
        )
        return int(cursor.lastrowid)

    def _post_account_ledger(
        self,
        conn: sqlite3.Connection,
        voucher_id: int,
        source_id: int,
        source_table: str,
        entry: dict[str, Any],
        rows: list[tuple[str, float, float, str]],
        now: str,
    ) -> None:
        for ledger_name, debit, credit, party_type in rows:
            conn.execute(
                """
                INSERT INTO ledger_postings(
                    voucher_id,voucher_date,ledger_name,debit,credit,party_type,party_id,
                    source_table,source_id,source_ref,status,created_at,cost_center_name,branch_name
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    voucher_id,
                    entry.get("entry_date"),
                    ledger_name,
                    debit,
                    credit,
                    party_type,
                    entry.get("party_id") if party_type else None,
                    source_table,
                    source_id,
                    entry.get("doc_no"),
                    entry.get("status") or "Active",
                    now,
                    entry.get("cost_center"),
                    entry.get("branch"),
                ),
            )

    def _voucher_source_table(self, voucher_type: str) -> str:
        return {
            "SALES": "sales",
            "PURCHASE": "purchases",
            "SALES_RETURN": "sales_returns",
            "PURCHASE_RETURN": "purchase_returns",
        }.get(voucher_type, voucher_type.lower())

    def _cash_bank_ledger(self, mode: Any) -> str:
        value = str(mode or "Cash").strip().lower()
        if value in {"bank", "card", "cheque", "upi"}:
            return "Bank"
        return "Cash"
