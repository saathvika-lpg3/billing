from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


INACTIVE_SQL = "'cancelled','void','deleted','superseded'"


@dataclass(frozen=True)
class AuditCheck:
    category: str
    check: str
    status: str
    count: int
    amount: float
    classification: str
    details: str


class BusinessFlowAuditService:
    """Read-only integrity diagnostics for the live ERP transaction lifecycle."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)

    def run(self) -> dict[str, Any]:
        uri = f"file:{self.db_path.resolve().as_posix()}?mode=ro"
        with sqlite3.connect(uri, uri=True) as conn:
            conn.row_factory = sqlite3.Row
            checks = [
                self._ledger_balance(conn),
                self._unbalanced_vouchers(conn),
                self._duplicate_active_vouchers(conn),
                self._orphan_ledger_rows(conn),
                self._cancelled_documents_with_active_postings(conn),
                self._documents_missing_vouchers(conn),
                self._gst_document_mismatches(conn),
                self._negative_global_stock(conn),
                self._negative_warehouse_stock(conn),
                self._unbalanced_transfer_logs(conn),
                self._duplicate_document_numbers(conn),
                self._locked_period_postings(conn),
            ]
            status_counts = {
                status: sum(1 for check in checks if check.status == status)
                for status in ("PASSED", "FAILED", "WARNING")
            }
            overall = "FAILED" if status_counts["FAILED"] else ("WARNING" if status_counts["WARNING"] else "PASSED")
            return {
                "database": str(self.db_path.resolve()),
                "overall_status": overall,
                "summary": status_counts,
                "checks": [asdict(check) for check in checks],
            }

    @staticmethod
    def _row(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row:
        row = conn.execute(sql, params).fetchone()
        if row is None:
            raise RuntimeError("Audit query returned no result.")
        return row

    @staticmethod
    def _result(
        category: str,
        check: str,
        count: int,
        *,
        amount: float = 0.0,
        details: str,
        warning: bool = False,
    ) -> AuditCheck:
        status = "WARNING" if warning and count else ("FAILED" if count else "PASSED")
        return AuditCheck(
            category=category,
            check=check,
            status=status,
            count=int(count),
            amount=round(float(amount or 0), 2),
            classification="legacy_or_live_data" if count else "none",
            details=details,
        )

    def _ledger_balance(self, conn: sqlite3.Connection) -> AuditCheck:
        row = self._row(
            conn,
            f"""
            SELECT ROUND(COALESCE(SUM(debit),0),2) debit,
                   ROUND(COALESCE(SUM(credit),0),2) credit,
                   ROUND(COALESCE(SUM(debit-credit),0),2) difference
            FROM ledger_postings
            WHERE LOWER(COALESCE(status,'active')) NOT IN ({INACTIVE_SQL})
            """,
        )
        difference = float(row["difference"] or 0)
        return self._result(
            "Accounts",
            "Active ledger debit equals credit",
            int(abs(difference) > 0.01),
            amount=difference,
            details=f"Debit {float(row['debit'] or 0):.2f}; credit {float(row['credit'] or 0):.2f}; difference {difference:.2f}.",
        )

    def _unbalanced_vouchers(self, conn: sqlite3.Connection) -> AuditCheck:
        row = self._row(
            conn,
            f"""
            SELECT COUNT(*) count,ROUND(COALESCE(SUM(ABS(difference)),0),2) amount
            FROM (
                SELECT voucher_id,ROUND(SUM(COALESCE(debit,0)-COALESCE(credit,0)),2) difference
                FROM ledger_postings
                WHERE LOWER(COALESCE(status,'active')) NOT IN ({INACTIVE_SQL})
                GROUP BY voucher_id
                HAVING ABS(difference)>0.01
            )
            """,
        )
        return self._result(
            "Accounts",
            "Every active voucher is internally balanced",
            row["count"],
            amount=row["amount"],
            details="Counts active voucher groups whose ledger rows do not balance within one paisa.",
        )

    def _duplicate_active_vouchers(self, conn: sqlite3.Connection) -> AuditCheck:
        row = self._row(
            conn,
            f"""
            SELECT COUNT(*) count FROM (
                SELECT source_table,source_id
                FROM voucher_headers
                WHERE LOWER(COALESCE(status,'active')) NOT IN ({INACTIVE_SQL})
                  AND COALESCE(source_table,'')<>'' AND COALESCE(source_id,0)>0
                GROUP BY source_table,source_id
                HAVING COUNT(*)>1
            )
            """,
        )
        return self._result(
            "Lifecycle",
            "No duplicate active voucher per source document",
            row["count"],
            details="Superseded and cancelled voucher versions are excluded.",
        )

    def _orphan_ledger_rows(self, conn: sqlite3.Connection) -> AuditCheck:
        row = self._row(
            conn,
            """
            SELECT COUNT(*) count
            FROM ledger_postings lp
            LEFT JOIN voucher_headers vh ON vh.id=lp.voucher_id
            WHERE vh.id IS NULL
            """,
        )
        return self._result(
            "Accounts",
            "No orphan ledger postings",
            row["count"],
            details="Every ledger posting must reference an existing voucher header.",
        )

    def _cancelled_documents_with_active_postings(self, conn: sqlite3.Connection) -> AuditCheck:
        tables = (
            "sales", "purchases", "sales_returns", "purchase_returns",
            "receipts", "payments", "expenses", "journal_entries",
        )
        count = 0
        for table in tables:
            count += int(
                self._row(
                    conn,
                    f"""
                    SELECT COUNT(*) count
                    FROM {table} d
                    JOIN ledger_postings lp ON lp.source_table=? AND lp.source_id=d.id
                    WHERE LOWER(COALESCE(d.status,'active')) IN ('cancelled','void','deleted')
                      AND LOWER(COALESCE(lp.status,'active')) NOT IN ({INACTIVE_SQL})
                    """,
                    (table,),
                )["count"]
            )
        return self._result(
            "Lifecycle",
            "Cancelled documents have no active ledger posting",
            count,
            details="Checks every posted sales, purchase, return, receipt, payment, expense and journal source.",
        )

    def _documents_missing_vouchers(self, conn: sqlite3.Connection) -> AuditCheck:
        tables = ("sales", "purchases", "sales_returns", "purchase_returns", "receipts", "payments", "expenses", "journal_entries")
        count = 0
        for table in tables:
            count += int(
                self._row(
                    conn,
                    f"""
                    SELECT COUNT(*) count
                    FROM {table} d
                    WHERE LOWER(COALESCE(d.status,'active')) NOT IN ('draft','hold','cancelled','void','deleted')
                      AND NOT EXISTS (
                          SELECT 1 FROM voucher_headers vh
                          WHERE vh.source_table=? AND vh.source_id=d.id
                            AND LOWER(COALESCE(vh.status,'active')) NOT IN ({INACTIVE_SQL})
                      )
                    """,
                    (table,),
                )["count"]
            )
        return self._result(
            "Lifecycle",
            "Posted documents have an active voucher",
            count,
            details="Draft and hold documents are intentionally non-posting.",
        )

    def _gst_document_mismatches(self, conn: sqlite3.Connection) -> AuditCheck:
        metadata = (
            ("sales", 1.0),
            ("purchases", 1.0),
            ("sales_returns", -1.0),
            ("purchase_returns", -1.0),
        )
        count = 0
        amount = 0.0
        for table, sign in metadata:
            rows = conn.execute(
                f"""
                SELECT d.id,d.taxable,d.gst_total,
                       COALESCE(SUM(CASE WHEN LOWER(COALESCE(g.status,'active')) NOT IN ({INACTIVE_SQL}) THEN g.taxable ELSE 0 END),0) posted_taxable,
                       COALESCE(SUM(CASE WHEN LOWER(COALESCE(g.status,'active')) NOT IN ({INACTIVE_SQL}) THEN g.cgst+g.sgst+g.igst ELSE 0 END),0) posted_gst
                FROM {table} d
                LEFT JOIN gst_postings g ON g.source_table=? AND g.source_id=d.id
                WHERE LOWER(COALESCE(d.status,'active')) NOT IN ('cancelled','void','deleted')
                GROUP BY d.id
                """,
                (table,),
            ).fetchall()
            for row in rows:
                taxable_difference = float(row["posted_taxable"] or 0) - sign * float(row["taxable"] or 0)
                gst_difference = float(row["posted_gst"] or 0) - sign * float(row["gst_total"] or 0)
                if abs(taxable_difference) > 0.01 or abs(gst_difference) > 0.01:
                    count += 1
                    amount += abs(gst_difference)
        return self._result(
            "GST",
            "Document GST totals match active GST postings",
            count,
            amount=amount,
            details="Returns are reconciled as negative GST postings.",
        )

    def _negative_global_stock(self, conn: sqlite3.Connection) -> AuditCheck:
        row = self._row(conn, "SELECT COUNT(*) count,ROUND(COALESCE(SUM(ABS(stock)),0),3) amount FROM items WHERE COALESCE(stock,0)<-0.0001")
        return self._result(
            "Inventory",
            "No negative global item stock",
            row["count"],
            amount=row["amount"],
            details="Negative legacy stock is reported, never hidden or auto-corrected.",
        )

    def _negative_warehouse_stock(self, conn: sqlite3.Connection) -> AuditCheck:
        row = self._row(
            conn,
            """
            SELECT COUNT(*) count,ROUND(COALESCE(SUM(ABS(stock)),0),3) amount
            FROM (
                SELECT stock FROM warehouse_stock WHERE COALESCE(stock,0)<-0.0001
                UNION ALL
                SELECT stock FROM product_pack_warehouse_stock WHERE COALESCE(stock,0)<-0.0001
            )
            """,
        )
        return self._result(
            "Inventory",
            "No negative warehouse or warehouse-pack stock",
            row["count"],
            amount=row["amount"],
            details="Checks both item-level and pack-level warehouse balances.",
        )

    def _unbalanced_transfer_logs(self, conn: sqlite3.Connection) -> AuditCheck:
        row = self._row(
            conn,
            """
            SELECT COUNT(*) count FROM (
                SELECT ref_no,ROUND(SUM(COALESCE(qty_in,0)-COALESCE(qty_out,0)),3) difference
                FROM stock_log
                WHERE kind LIKE 'stock_transfer%'
                GROUP BY ref_no
                HAVING ABS(difference)>0.001
            )
            """,
        )
        return self._result(
            "Inventory",
            "Stock transfers have equal in and out movement",
            row["count"],
            details="Includes cancellation reversal movements under the original reference.",
        )

    def _duplicate_document_numbers(self, conn: sqlite3.Connection) -> AuditCheck:
        metadata = (
            ("sales", "bill_no"), ("purchases", "bill_no"),
            ("sales_returns", "return_no"), ("purchase_returns", "return_no"),
            ("receipts", "receipt_no"), ("payments", "payment_no"),
            ("expenses", "expense_no"), ("journal_entries", "entry_no"),
            ("stock_transfers", "transfer_no"),
        )
        count = 0
        for table, column in metadata:
            count += int(
                self._row(
                    conn,
                    f"SELECT COUNT(*) count FROM (SELECT {column} FROM {table} WHERE TRIM(COALESCE({column},''))<>'' GROUP BY {column} HAVING COUNT(*)>1)",
                )["count"]
            )
        return self._result(
            "Validation",
            "Document numbers are unique within each transaction type",
            count,
            details="Cancelled numbers remain reserved and are included in the duplicate check.",
        )

    def _locked_period_postings(self, conn: sqlite3.Connection) -> AuditCheck:
        row = self._row(
            conn,
            f"""
            SELECT COUNT(*) count
            FROM voucher_headers vh
            JOIN financial_years fy ON vh.voucher_date BETWEEN fy.start_date AND fy.end_date
            WHERE COALESCE(fy.is_locked,0)=1
              AND LOWER(COALESCE(vh.status,'active')) NOT IN ({INACTIVE_SQL})
            """,
        )
        return self._result(
            "Validation",
            "No active posting exists in a locked financial year",
            row["count"],
            details="Existing locked-period postings are surfaced as a live-data issue.",
        )
