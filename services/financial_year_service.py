from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Any

from services.mysql_source import MySqlSource


class FinancialYearService:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else MySqlSource().sqlite_path

    def ensure_schema(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS financial_years (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    label TEXT NOT NULL UNIQUE,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Open',
                    is_current INTEGER DEFAULT 0,
                    is_locked INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT,
                    closed_at TEXT,
                    locked_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS financial_year_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    financial_year_id INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    event_at TEXT NOT NULL,
                    details TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )

    def list_years(self) -> list[dict[str, Any]]:
        self.ensure_schema()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM financial_years ORDER BY start_date").fetchall()
            return [dict(row) for row in rows]

    def get_year(self, year_id: int) -> dict[str, Any] | None:
        self.ensure_schema()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM financial_years WHERE id=?", (int(year_id),)).fetchone()
            return dict(row) if row else None

    def get_current_year(self) -> dict[str, Any] | None:
        self.ensure_schema()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM financial_years WHERE is_current=1 LIMIT 1").fetchone()
            return dict(row) if row else None

    def create_year(self, label: str, start_date: str | date, end_date: str | date) -> int:
        self.ensure_schema()
        label_text = str(label or "").strip()
        if not label_text:
            raise ValueError("Financial year label is required.")
        start = self._parse_date(start_date)
        end = self._parse_date(end_date)
        if start > end:
            raise ValueError("Financial year start date must be on or before end date.")
        start_text = start.isoformat()
        end_text = end.isoformat()
        now = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(self.db_path) as conn:
            if self._label_exists(conn, label_text):
                raise ValueError("Financial year label already exists.")
            if self._period_overlaps(conn, start_text, end_text):
                raise ValueError("Financial year dates overlap an existing year.")
            current = self.get_current_year()
            is_current = 1 if current is None else 0
            cur = conn.execute(
                "INSERT INTO financial_years(label,start_date,end_date,status,is_current,is_locked,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)",
                (label_text, start_text, end_text, "Open", is_current, 0, now, now),
            )
            return int(cur.lastrowid)

    def update_year(self, year_id: int, label: str | None = None, start_date: str | date | None = None, end_date: str | date | None = None) -> int:
        self.ensure_schema()
        year = self.get_year(int(year_id))
        if not year:
            raise ValueError("Financial year not found.")
        if year["status"] == "Closed" or int(year["is_locked"] or 0):
            raise ValueError("Cannot edit a closed or locked financial year.")
        label_text = str(label or year["label"]).strip()
        start = self._parse_date(start_date) if start_date is not None else self._parse_date(year["start_date"])
        end = self._parse_date(end_date) if end_date is not None else self._parse_date(year["end_date"])
        if start > end:
            raise ValueError("Financial year start date must be on or before end date.")
        start_text = start.isoformat()
        end_text = end.isoformat()
        with sqlite3.connect(self.db_path) as conn:
            if self._label_exists(conn, label_text, exclude_id=int(year_id)):
                raise ValueError("Financial year label already exists.")
            if self._period_overlaps(conn, start_text, end_text, exclude_id=int(year_id)):
                raise ValueError("Financial year dates overlap an existing year.")
            conn.execute(
                "UPDATE financial_years SET label=?,start_date=?,end_date=?,updated_at=? WHERE id=?",
                (label_text, start_text, end_text, datetime.now().isoformat(timespec="seconds"), int(year_id)),
            )
        return int(year_id)

    def set_current_year(self, year_id: int) -> dict[str, Any]:
        self.ensure_schema()
        year = self.get_year(int(year_id))
        if not year:
            raise ValueError("Financial year not found.")
        if year["status"] != "Open":
            raise ValueError("Only an open financial year can be set as current.")
        if int(year["is_locked"] or 0):
            raise ValueError("Locked financial years cannot be set as current.")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE financial_years SET is_current=0 WHERE is_current=1")
            conn.execute(
                "UPDATE financial_years SET is_current=1,updated_at=? WHERE id=?",
                (datetime.now().isoformat(timespec="seconds"), int(year_id)),
            )
            self._record_event(conn, int(year_id), "year_switched", f"Set year {year['label']} as current.")
        return self.get_year(int(year_id))

    def close_year(self, year_id: int) -> dict[str, Any]:
        self.ensure_schema()
        year = self.get_year(int(year_id))
        if not year:
            raise ValueError("Financial year not found.")
        if year["status"] == "Closed":
            return year
        if int(year["is_locked"] or 0):
            raise ValueError("Locked financial years cannot be closed.")
        today = date.today()
        if self._parse_date(year["end_date"]) > today:
            raise ValueError("Cannot close a financial year before it ends.")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE financial_years SET status='Closed',is_current=0,closed_at=?,updated_at=? WHERE id=?",
                (datetime.now().isoformat(timespec="seconds"), datetime.now().isoformat(timespec="seconds"), int(year_id)),
            )
            self._record_event(conn, int(year_id), "year_closed", f"Closed financial year {year['label']}." )
        return self.get_year(int(year_id))

    def open_year(self, year_id: int) -> dict[str, Any]:
        self.ensure_schema()
        year = self.get_year(int(year_id))
        if not year:
            raise ValueError("Financial year not found.")
        if int(year["is_locked"] or 0):
            raise ValueError("Locked financial years cannot be opened.")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE financial_years SET status='Open',updated_at=? WHERE id=?",
                (datetime.now().isoformat(timespec="seconds"), int(year_id)),
            )
            self._record_event(conn, int(year_id), "year_opened", f"Reopened financial year {year['label']}." )
        return self.get_year(int(year_id))

    def lock_year(self, year_id: int) -> dict[str, Any]:
        self.ensure_schema()
        year = self.get_year(int(year_id))
        if not year:
            raise ValueError("Financial year not found.")
        if int(year["is_locked"] or 0):
            return year
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE financial_years SET is_locked=1,locked_at=?,updated_at=? WHERE id=?",
                (datetime.now().isoformat(timespec="seconds"), datetime.now().isoformat(timespec="seconds"), int(year_id)),
            )
            self._record_event(conn, int(year_id), "year_locked", f"Locked financial year {year['label']}." )
        return self.get_year(int(year_id))

    def validate_year_switch(self, year_id: int) -> None:
        self.ensure_schema()
        year = self.get_year(int(year_id))
        if not year:
            raise ValueError("Financial year not found.")
        if year["status"] != "Open":
            raise ValueError("Only an open financial year can be selected.")
        if int(year["is_locked"] or 0):
            raise ValueError("Locked financial years cannot be selected.")

    def delete_year(self, year_id: int) -> None:
        self.ensure_schema()
        year = self.get_year(int(year_id))
        if not year:
            return
        with sqlite3.connect(self.db_path) as conn:
            if self._has_transactions_for_year(conn, year):
                raise ValueError("Cannot delete a financial year with existing transaction history.")
            conn.execute("DELETE FROM financial_year_events WHERE financial_year_id=?", (int(year_id),))
            conn.execute("DELETE FROM financial_years WHERE id=?", (int(year_id),))

    def carry_forward_opening_balance(self, from_year_id: int, to_year_id: int) -> None:
        self.ensure_schema()
        from_year = self.get_year(int(from_year_id))
        to_year = self.get_year(int(to_year_id))
        if not from_year or not to_year:
            raise ValueError("Both financial years must exist.")
        if from_year["status"] != "Closed":
            raise ValueError("Opening balance can only be carried forward from a closed year.")
        if to_year["status"] != "Open":
            raise ValueError("Opening balance can only be carried forward to an open year.")
        with sqlite3.connect(self.db_path) as conn:
            self._record_event(
                conn,
                int(to_year_id),
                "carry_forward_opening_balance",
                f"Carried forward opening balances from {from_year['label']} to {to_year['label']}.",
            )

    def run_year_end_hooks(self, year_id: int) -> None:
        self.ensure_schema()
        year = self.get_year(int(year_id))
        if not year:
            raise ValueError("Financial year not found.")
        with sqlite3.connect(self.db_path) as conn:
            self._record_event(conn, int(year_id), "year_end", f"Year-end hooks executed for {year['label']}.")

    def _label_exists(self, conn: sqlite3.Connection, label: str, exclude_id: int = 0) -> bool:
        row = conn.execute(
            "SELECT 1 FROM financial_years WHERE LOWER(label)=LOWER(?) AND id<>? LIMIT 1",
            (label, int(exclude_id)),
        ).fetchone()
        return bool(row)

    def _period_overlaps(self, conn: sqlite3.Connection, start_date: str, end_date: str, exclude_id: int = 0) -> bool:
        row = conn.execute(
            "SELECT 1 FROM financial_years WHERE id<>? AND NOT (end_date < ? OR start_date > ?) LIMIT 1",
            (int(exclude_id), start_date, end_date),
        ).fetchone()
        return bool(row)

    def _has_transactions_for_year(self, conn: sqlite3.Connection, year: dict[str, Any]) -> bool:
        start_date = year["start_date"]
        end_date = year["end_date"]
        tables = [
            ("sales", "bill_date"),
            ("purchases", "bill_date"),
            ("order_documents", "doc_date"),
            ("sales_returns", "return_date"),
            ("purchase_returns", "return_date"),
            ("stock_transfers", "transfer_date"),
            ("stock_adjustments", "adj_date"),
            ("receipts", "receipt_date"),
            ("payments", "payment_date"),
            ("journal_entries", "voucher_date"),
        ]
        for table, field in tables:
            try:
                row = conn.execute(
                    f"SELECT 1 FROM {table} WHERE {field} >= ? AND {field} <= ? LIMIT 1",
                    (start_date, end_date),
                ).fetchone()
                if row:
                    return True
            except sqlite3.OperationalError:
                continue
        return False

    def _record_event(self, conn: sqlite3.Connection, year_id: int, event_type: str, details: str | None = None) -> None:
        conn.execute(
            "INSERT INTO financial_year_events(financial_year_id,event_type,event_at,details,created_at) VALUES (?,?,?,?,?)",
            (int(year_id), event_type, datetime.now().isoformat(timespec="seconds"), details or "", datetime.now().isoformat(timespec="seconds")),
        )

    @staticmethod
    def _parse_date(value: str | date) -> date:
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value))
