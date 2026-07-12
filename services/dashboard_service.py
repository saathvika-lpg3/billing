from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from config.product_version import DISPLAY_VERSION, PRODUCT_VERSION, runtime_version_record
from services.communication_log_service import mask_recipient
from services.email_service import SmtpEmailConfig
from services.mysql_source import MySqlSource


class DashboardService:
    def __init__(self, source: Any | None = None) -> None:
        self.source = source or MySqlSource()

    def snapshot(self) -> dict[str, Any]:
        today_date = date.today()
        today = today_date.isoformat()
        month_start = today_date.replace(day=1).isoformat()
        expiry_until = (today_date + timedelta(days=30)).isoformat()
        low_stock_rows = self._low_stock_alerts()
        expiry_rows = self._expiry_alerts(expiry_until)
        pending_dispatch_rows = self._pending_dispatch()
        pending_purchase_orders = self._pending_orders("purchase_order")
        pending_sales_orders = self._pending_orders("sales_order")
        backup_status = self._backup_status()
        database_health = self._database_health()
        communication_status = self._communication_status(today)
        failed_communications = communication_status.get("failures", [])
        sales_kpis = self._sales_kpis(today, month_start, len(pending_sales_orders))
        purchase_kpis = self._purchase_kpis(today, month_start, len(pending_purchase_orders))
        return {
            "company": self.source.company(),
            "business_summary": self._business_summary(today),
            "sales_kpis": sales_kpis,
            "purchase_kpis": purchase_kpis,
            "cash_bank": self._cash_bank_summary(today),
            "receivables": self._receivables(),
            "payables": self._payables(),
            "stock_value": self._stock_value(),
            "low_stock_alerts": low_stock_rows,
            "expiry_alerts": expiry_rows,
            "pending_dispatch": pending_dispatch_rows,
            "pending_purchase_orders": pending_purchase_orders,
            "pending_sales_orders": pending_sales_orders,
            "critical_alerts": self._critical_alerts(
                low_stock_rows,
                expiry_rows,
                pending_dispatch_rows,
                backup_status,
                database_health,
                failed_communications,
            ),
            "top_customers": self._top_customers(month_start),
            "top_selling_products": self._top_selling_products(month_start),
            "recent_sales": self._recent_sales(),
            "recent_purchase": self._recent_purchase(),
            "recent_receipts": self._recent_receipts(),
            "recent_payments": self._recent_payments(),
            "daily_tasks": self._daily_tasks(
                low_stock_rows,
                expiry_rows,
                pending_dispatch_rows,
                pending_purchase_orders,
                pending_sales_orders,
                failed_communications,
            ),
            "communication_status": communication_status,
            "failed_communications": failed_communications,
            "backup_status": backup_status,
            "database_health": database_health,
            "application_version": self._application_version(),
            "sales_trend": sales_kpis["trend"],
            "business_mix": self._business_mix(month_start),
        }

    def _business_summary(self, today: str) -> list[dict[str, str]]:
        sales = self._one(
            """
            SELECT COUNT(*) count, COALESCE(SUM(grand_total),0) total
            FROM sales
            WHERE bill_date=%s AND COALESCE(status,'Active')='Active'
            """,
            (today,),
        )
        purchase = self._one(
            """
            SELECT COUNT(*) count, COALESCE(SUM(grand_total),0) total
            FROM purchases
            WHERE bill_date=%s AND COALESCE(status,'Active')='Active'
            """,
            (today,),
        )
        receipts = self._one(
            """
            SELECT COUNT(*) count, COALESCE(SUM(amount),0) total
            FROM receipts
            WHERE receipt_date=%s AND COALESCE(status,'Active')='Active'
            """,
            (today,),
        )
        payments = self._one(
            """
            SELECT COUNT(*) count, COALESCE(SUM(amount),0) total
            FROM payments
            WHERE payment_date=%s AND COALESCE(status,'Active')='Active'
            """,
            (today,),
        )
        return [
            self._metric("Sales", self._money(sales.get("total")), f"{self._int(sales.get('count'))} bills"),
            self._metric("Purchase", self._money(purchase.get("total")), f"{self._int(purchase.get('count'))} bills"),
            self._metric("Receipts", self._money(receipts.get("total")), f"{self._int(receipts.get('count'))} vouchers"),
            self._metric("Payments", self._money(payments.get("total")), f"{self._int(payments.get('count'))} vouchers"),
        ]

    def _sales_kpis(self, today: str, month_start: str, pending_orders: int) -> dict[str, Any]:
        today_sales = self._one(
            "SELECT COUNT(*) count, COALESCE(SUM(grand_total),0) total FROM sales WHERE bill_date=%s AND COALESCE(status,'Active')='Active'",
            (today,),
        )
        month_sales = self._one(
            "SELECT COUNT(*) count, COALESCE(SUM(grand_total),0) total FROM sales WHERE bill_date>=%s AND COALESCE(status,'Active')='Active'",
            (month_start,),
        )
        average = self._float(month_sales.get("total")) / max(1, self._int(month_sales.get("count")))
        return {
            "items": [
                self._metric("Today", self._money(today_sales.get("total")), f"{self._int(today_sales.get('count'))} invoices"),
                self._metric("This Month", self._money(month_sales.get("total")), f"{self._int(month_sales.get('count'))} invoices"),
                self._metric("Avg Bill", self._money(average), "Monthly average"),
                self._metric("Pending Orders", str(pending_orders), "Sales orders"),
            ],
            "trend": self._trend("sales", "bill_date", "grand_total", today),
        }

    def _purchase_kpis(self, today: str, month_start: str, pending_orders: int) -> dict[str, Any]:
        today_purchase = self._one(
            "SELECT COUNT(*) count, COALESCE(SUM(grand_total),0) total FROM purchases WHERE bill_date=%s AND COALESCE(status,'Active')='Active'",
            (today,),
        )
        month_purchase = self._one(
            "SELECT COUNT(*) count, COALESCE(SUM(grand_total),0) total FROM purchases WHERE bill_date>=%s AND COALESCE(status,'Active')='Active'",
            (month_start,),
        )
        average = self._float(month_purchase.get("total")) / max(1, self._int(month_purchase.get("count")))
        return {
            "items": [
                self._metric("Today", self._money(today_purchase.get("total")), f"{self._int(today_purchase.get('count'))} bills"),
                self._metric("This Month", self._money(month_purchase.get("total")), f"{self._int(month_purchase.get('count'))} bills"),
                self._metric("Avg Bill", self._money(average), "Monthly average"),
                self._metric("Pending POs", str(pending_orders), "Purchase orders"),
            ],
            "trend": self._trend("purchases", "bill_date", "grand_total", today),
        }

    def _cash_bank_summary(self, today: str) -> dict[str, Any]:
        cash = self._one(
            """
            SELECT COALESCE(SUM(COALESCE(debit,0)-COALESCE(credit,0)),0) balance
            FROM ledger_postings
            WHERE LOWER(ledger_name) LIKE '%cash%'
            """
        )
        bank = self._one(
            """
            SELECT COALESCE(SUM(COALESCE(debit,0)-COALESCE(credit,0)),0) balance
            FROM ledger_postings
            WHERE LOWER(ledger_name) LIKE '%bank%'
            """
        )
        receipts = self._one(
            "SELECT COALESCE(SUM(amount),0) total FROM receipts WHERE receipt_date=%s AND COALESCE(status,'Active')='Active'",
            (today,),
        )
        payments = self._one(
            "SELECT COALESCE(SUM(amount),0) total FROM payments WHERE payment_date=%s AND COALESCE(status,'Active')='Active'",
            (today,),
        )
        rows = self._rows(
            """
            SELECT voucher_date, ledger_name, source_ref, debit, credit, status
            FROM ledger_postings
            WHERE LOWER(ledger_name) LIKE '%cash%' OR LOWER(ledger_name) LIKE '%bank%'
            ORDER BY voucher_date DESC,id DESC
            LIMIT 6
            """
        )
        cash_balance = self._float(cash.get("balance"))
        bank_balance = self._float(bank.get("balance"))
        return {
            "items": [
                self._metric("Cash", self._money(cash_balance), "Ledger balance"),
                self._metric("Bank", self._money(bank_balance), "Ledger balance"),
                self._metric("Today In", self._money(receipts.get("total")), "Receipts"),
                self._metric("Today Out", self._money(payments.get("total")), "Payments"),
            ],
            "segments": [
                {"label": "Cash", "value": abs(cash_balance), "color": "#059669"},
                {"label": "Bank", "value": abs(bank_balance), "color": "#2563EB"},
            ],
            "rows": rows,
        }

    def _receivables(self) -> dict[str, Any]:
        summary = self._one(
            "SELECT COUNT(*) count, COALESCE(SUM(balance),0) total FROM customers WHERE COALESCE(balance,0)>0"
        )
        rows = self._rows(
            """
            SELECT name, phone, area, balance
            FROM customers
            WHERE COALESCE(balance,0)>0
            ORDER BY balance DESC,name
            LIMIT 8
            """
        )
        return {
            "items": [self._metric("Outstanding", self._money(summary.get("total")), f"{self._int(summary.get('count'))} customers")],
            "rows": rows,
        }

    def _payables(self) -> dict[str, Any]:
        summary = self._one(
            "SELECT COUNT(*) count, COALESCE(SUM(balance),0) total FROM suppliers WHERE COALESCE(balance,0)>0"
        )
        rows = self._rows(
            """
            SELECT name, phone, area, balance
            FROM suppliers
            WHERE COALESCE(balance,0)>0
            ORDER BY balance DESC,name
            LIMIT 8
            """
        )
        return {
            "items": [self._metric("Outstanding", self._money(summary.get("total")), f"{self._int(summary.get('count'))} suppliers")],
            "rows": rows,
        }

    def _stock_value(self) -> dict[str, Any]:
        stock = self._one(
            """
            SELECT COUNT(*) item_count,
                   COALESCE(SUM(stock),0) qty,
                   COALESCE(SUM(COALESCE(stock,0) * COALESCE(NULLIF(standard_cost,0), buy_rate, 0)),0) value
            FROM items
            WHERE COALESCE(status,'Active')='Active'
            """
        )
        bars = self._rows(
            """
            SELECT name label,
                   ROUND(COALESCE(stock,0) * COALESCE(NULLIF(standard_cost,0), buy_rate, 0),2) value
            FROM items
            WHERE COALESCE(status,'Active')='Active'
            ORDER BY value DESC,name
            LIMIT 5
            """
        )
        return {
            "items": [
                self._metric("Stock Value", self._money(stock.get("value")), f"{self._int(stock.get('item_count'))} items"),
                self._metric("Quantity", self._qty(stock.get("qty")), "Available quantity"),
            ],
            "bars": bars,
        }

    def _low_stock_alerts(self) -> list[dict[str, Any]]:
        return self._rows(
            """
            SELECT id, name, unit, stock, min_stock, reorder_qty
            FROM items
            WHERE COALESCE(min_stock,0)>0 AND COALESCE(stock,0)<=COALESCE(min_stock,0)
            ORDER BY stock ASC,name
            LIMIT 8
            """
        )

    def _expiry_alerts(self, expiry_until: str) -> list[dict[str, Any]]:
        return self._rows(
            """
            SELECT b.id, COALESCE(i.name,'Item') item_name, b.batch_no, b.expiry_date, b.stock
            FROM item_batches b
            LEFT JOIN items i ON i.id=b.item_id
            WHERE COALESCE(b.stock,0)>0
              AND COALESCE(b.expiry_date,'')<>''
              AND b.expiry_date<=%s
            ORDER BY b.expiry_date,b.id
            LIMIT 8
            """,
            (expiry_until,),
        )

    def _pending_dispatch(self) -> list[dict[str, Any]]:
        return self._rows(
            """
            SELECT id, challan_no, challan_date, area, vehicle_no, total_qty, dispatch_status
            FROM stock_outs
            WHERE COALESCE(dispatch_status,'Pending Dispatch')<>'Completed'
              AND COALESCE(status,'Active')='Active'
            ORDER BY challan_date DESC,id DESC
            LIMIT 8
            """
        )

    def _pending_orders(self, doc_type: str) -> list[dict[str, Any]]:
        return self._rows(
            """
            SELECT id, doc_no, doc_date, party_name, grand_total, status
            FROM order_documents
            WHERE doc_type=%s
              AND LOWER(COALESCE(status,'open')) NOT IN ('converted','closed','cancelled','completed','deleted')
            ORDER BY doc_date DESC,id DESC
            LIMIT 8
            """,
            (doc_type,),
        )

    def _critical_alerts(
        self,
        low_stock_rows: list[dict[str, Any]],
        expiry_rows: list[dict[str, Any]],
        pending_dispatch_rows: list[dict[str, Any]],
        backup_status: list[dict[str, Any]],
        database_health: list[dict[str, Any]],
        failed_communications: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        if low_stock_rows:
            alerts.append({"level": "High", "title": "Low Stock", "detail": f"{len(low_stock_rows)} items need reorder"})
        if expiry_rows:
            alerts.append({"level": "High", "title": "Expiry Alert", "detail": f"{len(expiry_rows)} batches within 30 days"})
        if pending_dispatch_rows:
            alerts.append({"level": "Medium", "title": "Pending Dispatch", "detail": f"{len(pending_dispatch_rows)} loads pending"})
        if backup_status and str(backup_status[0].get("status") or "").lower() not in {"success", "completed", "ok"}:
            alerts.append({"level": "Medium", "title": "Backup Status", "detail": str(backup_status[0].get("status") or "Review backup")})
        if database_health and str(database_health[0].get("status") or "").lower() != "ok":
            alerts.append({"level": "High", "title": "Database Health", "detail": str(database_health[0].get("status") or "Review database")})
        if failed_communications:
            alerts.append({"level": "Medium", "title": "Communication Retry", "detail": f"{len(failed_communications)} email rows need retry"})
        if not alerts:
            alerts.append({"level": "Info", "title": "All Clear", "detail": "No critical dashboard alerts right now."})
        return alerts[:6]

    def _top_customers(self, month_start: str) -> dict[str, Any]:
        rows = self._rows(
            """
            SELECT customer_name, COUNT(*) bills, ROUND(COALESCE(SUM(grand_total),0),2) total
            FROM sales
            WHERE bill_date>=%s AND COALESCE(status,'Active')='Active'
            GROUP BY customer_name
            ORDER BY total DESC,customer_name
            LIMIT 6
            """,
            (month_start,),
        )
        return {
            "rows": rows,
            "bars": [{"label": str(row.get("customer_name") or "")[:8], "value": row.get("total") or 0} for row in rows],
        }

    def _business_mix(self, month_start: str) -> list[dict[str, Any]]:
        month_sales = self._one(
            "SELECT COALESCE(SUM(grand_total),0) total FROM sales WHERE bill_date >= %s AND COALESCE(status,'Active')='Active'",
            (month_start,),
        )
        month_purchase = self._one(
            "SELECT COALESCE(SUM(grand_total),0) total FROM purchases WHERE bill_date >= %s AND COALESCE(status,'Active')='Active'",
            (month_start,),
        )
        receivable = self._one("SELECT COALESCE(SUM(balance),0) total FROM customers WHERE COALESCE(balance,0)>0")
        payable = self._one("SELECT COALESCE(SUM(balance),0) total FROM suppliers WHERE COALESCE(balance,0)>0")
        return [
            {"label": "Sales", "value": self._float(month_sales.get("total")), "color": "#2563EB"},
            {"label": "Purchase", "value": self._float(month_purchase.get("total")), "color": "#059669"},
            {"label": "Receivable", "value": self._float(receivable.get("total")), "color": "#D97706"},
            {"label": "Payable", "value": self._float(payable.get("total")), "color": "#DC2626"},
        ]

    def _top_selling_products(self, month_start: str) -> dict[str, Any]:
        rows = self._rows(
            """
            SELECT si.item_name, ROUND(SUM(COALESCE(si.qty,0)),2) qty, ROUND(SUM(COALESCE(si.total,0)),2) total
            FROM sales_items si
            JOIN sales s ON s.id=si.sale_id
            WHERE s.bill_date>=%s AND COALESCE(s.status,'Active')='Active'
            GROUP BY si.item_name
            ORDER BY total DESC,si.item_name
            LIMIT 6
            """,
            (month_start,),
        )
        return {
            "rows": rows,
            "bars": [{"label": str(row.get("item_name") or "")[:8], "value": row.get("total") or 0, "color": "#059669"} for row in rows],
        }

    def _recent_sales(self) -> list[dict[str, Any]]:
        return self._rows(
            """
            SELECT id, bill_no, bill_date, customer_name, grand_total
            FROM sales
            ORDER BY bill_date DESC,id DESC
            LIMIT 8
            """
        )

    def _recent_purchase(self) -> list[dict[str, Any]]:
        return self._rows(
            """
            SELECT id, bill_no, bill_date, supplier_name, grand_total
            FROM purchases
            ORDER BY bill_date DESC,id DESC
            LIMIT 8
            """
        )

    def _recent_receipts(self) -> list[dict[str, Any]]:
        return self._rows(
            """
            SELECT id, receipt_no, receipt_date, customer_name, amount, mode
            FROM receipts
            ORDER BY receipt_date DESC,id DESC
            LIMIT 8
            """
        )

    def _recent_payments(self) -> list[dict[str, Any]]:
        return self._rows(
            """
            SELECT id, payment_no, payment_date, supplier_name, amount, mode
            FROM payments
            ORDER BY payment_date DESC,id DESC
            LIMIT 8
            """
        )

    def _daily_tasks(
        self,
        low_stock_rows: list[dict[str, Any]],
        expiry_rows: list[dict[str, Any]],
        pending_dispatch_rows: list[dict[str, Any]],
        pending_purchase_orders: list[dict[str, Any]],
        pending_sales_orders: list[dict[str, Any]],
        failed_communications: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        tasks: list[dict[str, Any]] = []
        if pending_dispatch_rows:
            tasks.append({"task": "Dispatch follow-up", "detail": f"{len(pending_dispatch_rows)} loads pending", "priority": "High"})
        if low_stock_rows:
            tasks.append({"task": "Reorder low stock", "detail": f"{len(low_stock_rows)} items below minimum", "priority": "High"})
        if expiry_rows:
            tasks.append({"task": "Review expiring batches", "detail": f"{len(expiry_rows)} batches need action", "priority": "High"})
        if pending_purchase_orders:
            tasks.append({"task": "Purchase order review", "detail": f"{len(pending_purchase_orders)} POs open", "priority": "Medium"})
        if pending_sales_orders:
            tasks.append({"task": "Sales order review", "detail": f"{len(pending_sales_orders)} orders open", "priority": "Medium"})
        if failed_communications:
            tasks.append({"task": "Retry failed email", "detail": f"{len(failed_communications)} communication rows ready", "priority": "Medium"})
        if not tasks:
            tasks.append({"task": "No urgent tasks", "detail": "No dashboard action is due right now.", "priority": "Info"})
        return tasks[:8]

    def _communication_status(self, today: str) -> dict[str, Any]:
        db_path = Path(getattr(self.source, "sqlite_path", ""))
        config = SmtpEmailConfig.from_sources(db_path=db_path if db_path else None)
        mode = "SMTP" if config.smtp_enabled else "Handoff"
        mode_note = "SMTP ready" if config.smtp_ready else "Mail client handoff" if not config.smtp_enabled else "Configure SMTP"
        if not self._table_exists("communication_logs"):
            return {
                "items": [
                    self._metric("Mode", mode, mode_note),
                    self._metric("Sent Today", "0", "SMTP deliveries"),
                    self._metric("Failed", "0", "Retry queue"),
                    self._metric("Pending Retry", "0", "Ready now"),
                ],
                "rows": [],
                "failures": [],
            }
        now = datetime.now().isoformat(timespec="seconds")
        summary = self._one(
            """
            SELECT
                COALESCE(SUM(CASE WHEN status='Sent' AND substr(created_at,1,10)=%s THEN 1 ELSE 0 END),0) sent_today,
                COALESCE(SUM(CASE WHEN status='Handed Off' AND substr(created_at,1,10)=%s THEN 1 ELSE 0 END),0) handed_today,
                COALESCE(SUM(CASE WHEN status='Failed' THEN 1 ELSE 0 END),0) failed,
                COALESCE(SUM(
                    CASE WHEN status IN ('Failed','Queued')
                           AND COALESCE(recipient,'')<>''
                           AND recipient NOT LIKE '%***%'
                           AND COALESCE(attachment_path,'')<>''
                           AND LOWER(attachment_path) LIKE '%.pdf'
                           AND (instr(attachment_path, ':') > 0 OR substr(attachment_path,1,1)='/' OR substr(attachment_path,1,2)='\\')
                           AND (next_retry_at IS NULL OR next_retry_at<=%s)
                         THEN 1 ELSE 0 END
                ),0) pending_retry,
                COUNT(*) total
            FROM communication_logs
            """,
            (today, today, now),
        )
        rows = self._rows(
            """
            SELECT channel, recipient, subject, status, result_code, updated_at
            FROM communication_logs
            ORDER BY id DESC
            LIMIT 8
            """
        )
        failures = self._rows(
            """
            SELECT recipient, subject, result_code, attempts, next_retry_at
            FROM communication_logs
            WHERE status IN ('Failed','Queued')
            ORDER BY COALESCE(next_retry_at, updated_at), id
            LIMIT 8
            """
        )
        for row in rows:
            row["recipient"] = mask_recipient(row.get("recipient"))
        for row in failures:
            row["recipient"] = mask_recipient(row.get("recipient"))
        return {
            "items": [
                self._metric("Mode", mode, mode_note),
                self._metric("Sent Today", str(self._int(summary.get("sent_today"))), f"{self._int(summary.get('handed_today'))} handoffs"),
                self._metric("Failed", str(self._int(summary.get("failed"))), f"{self._int(summary.get('total'))} total rows"),
                self._metric("Pending Retry", str(self._int(summary.get("pending_retry"))), "Ready now"),
            ],
            "rows": rows,
            "failures": failures,
        }

    def _backup_status(self) -> list[dict[str, Any]]:
        return self._rows(
            """
            SELECT action, status, message, created_at
            FROM backup_logs
            ORDER BY id DESC
            LIMIT 1
            """
        )

    def _database_health(self) -> list[dict[str, Any]]:
        path = Path(getattr(self.source, "sqlite_path", ""))
        try:
            with sqlite3.connect(path) as conn:
                status = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
            size_mb = path.stat().st_size / (1024 * 1024) if path.exists() else 0
            return [{"status": status, "database": path.name, "size_mb": round(size_mb, 2)}]
        except Exception as exc:
            return [{"status": f"Error: {exc}", "database": path.name if path else "", "size_mb": 0}]

    def _application_version(self) -> list[dict[str, Any]]:
        runtime = runtime_version_record()
        rows = self._rows(
            """
            SELECT version_key component, version_value version, notes, updated_at
            FROM app_release_versions
            ORDER BY updated_at DESC
            LIMIT 5
            """
        )
        if not rows:
            rows = self._rows(
                """
                SELECT setting_key component, setting_value version, '' notes, updated_at
                FROM app_settings
                WHERE LOWER(setting_key) LIKE '%version%'
                ORDER BY updated_at DESC
                LIMIT 5
                """
            )

        history: list[dict[str, Any]] = []
        for row in rows:
            component = str(row.get("component") or "Recorded component").strip()
            recorded_version = str(row.get("version") or "").strip()
            if component.casefold() == "desktop runtime" and recorded_version in {
                DISPLAY_VERSION,
                PRODUCT_VERSION,
            }:
                continue
            notes = str(row.get("notes") or "").strip()
            history.append(
                {
                    "component": f"History: {component}",
                    "version": recorded_version,
                    "notes": "Recorded compatibility/history entry" + (f" - {notes}" if notes else ""),
                    "updated_at": row.get("updated_at") or "",
                }
            )
        return [runtime, *history[:4]]

    def _trend(self, table: str, date_field: str, amount_field: str, today: str) -> list[dict[str, Any]]:
        end = date.fromisoformat(today)
        start = end - timedelta(days=6)
        rows = self._rows(
            f"""
            SELECT {date_field} day, COALESCE(SUM({amount_field}),0) total
            FROM {table}
            WHERE {date_field} BETWEEN %s AND %s
              AND COALESCE(status,'Active')='Active'
            GROUP BY {date_field}
            ORDER BY {date_field}
            """,
            (start.isoformat(), end.isoformat()),
        )
        totals = {str(row.get("day")): self._float(row.get("total")) for row in rows}
        return [
            {"label": (start + timedelta(days=offset)).strftime("%d %b"), "value": totals.get((start + timedelta(days=offset)).isoformat(), 0.0)}
            for offset in range(7)
        ]

    def _rows(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        try:
            return self.source.rows(sql, params)
        except Exception:
            return []

    def _one(self, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any]:
        try:
            return self.source.one(sql, params) or {}
        except Exception:
            return {}

    def _table_exists(self, table_name: str) -> bool:
        db_path = Path(getattr(self.source, "sqlite_path", ""))
        if not db_path.exists():
            return False
        try:
            with sqlite3.connect(db_path) as conn:
                row = conn.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
                    (table_name,),
                ).fetchone()
            return row is not None
        except sqlite3.Error:
            return False

    def _metric(self, title: str, value: str, note: str) -> dict[str, str]:
        return {"title": title, "value": value, "note": note}

    def _money(self, value: Any) -> str:
        try:
            return f"Rs {float(value or 0):,.2f}"
        except (TypeError, ValueError):
            return "Rs 0.00"

    def _qty(self, value: Any) -> str:
        try:
            return f"{float(value or 0):,.2f}"
        except (TypeError, ValueError):
            return "0.00"

    def _int(self, value: Any) -> int:
        try:
            return int(float(value or 0))
        except (TypeError, ValueError):
            return 0

    def _float(self, value: Any) -> float:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0
