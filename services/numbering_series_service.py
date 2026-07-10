from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from services.mysql_source import MySqlSource


class NumberingSeriesService:
    RESET_NEVER = "never"
    RESET_YEARLY = "yearly"
    RESET_MONTHLY = "monthly"

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else MySqlSource().sqlite_path

    def ensure_schema(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS numbering_series (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_type TEXT NOT NULL,
                    prefix TEXT,
                    suffix TEXT,
                    separator TEXT DEFAULT '-',
                    financial_year_label TEXT,
                    branch_code TEXT,
                    warehouse_code TEXT,
                    business_type_code TEXT,
                    running_number INTEGER DEFAULT 0,
                    padding_length INTEGER DEFAULT 6,
                    start_number INTEGER DEFAULT 1,
                    current_number INTEGER DEFAULT 0,
                    reset_rule TEXT DEFAULT 'never',
                    last_reset_at TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT,
                    updated_at TEXT,
                    UNIQUE(document_type,financial_year_label,branch_code,warehouse_code,business_type_code)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS numbering_series_reservations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numbering_series_id INTEGER NOT NULL,
                    reserved_number TEXT NOT NULL,
                    reserved_at TEXT NOT NULL,
                    reserved_by TEXT,
                    status TEXT NOT NULL DEFAULT 'reserved',
                    cancelled_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT
                )
                """
            )

    def list_series(self) -> list[dict[str, Any]]:
        self.ensure_schema()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM numbering_series ORDER BY document_type,financial_year_label,branch_code,warehouse_code").fetchall()
            return [dict(row) for row in rows]

    def get_series(self, series_id: int) -> dict[str, Any] | None:
        self.ensure_schema()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM numbering_series WHERE id=?", (int(series_id),)).fetchone()
            return dict(row) if row else None

    def create_series(
        self,
        document_type: str,
        prefix: str | None = None,
        suffix: str | None = None,
        separator: str | None = None,
        financial_year_label: str | None = None,
        branch_code: str | None = None,
        warehouse_code: str | None = None,
        business_type_code: str | None = None,
        padding_length: int = 6,
        start_number: int = 1,
        reset_rule: str = RESET_NEVER,
    ) -> int:
        self.ensure_schema()
        document_type = str(document_type or "").strip()
        if not document_type:
            raise ValueError("Document type is required.")
        if reset_rule not in {self.RESET_NEVER, self.RESET_YEARLY, self.RESET_MONTHLY}:
            raise ValueError("Invalid reset rule.")
        now = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(self.db_path) as conn:
            existing = conn.execute(
                "SELECT id FROM numbering_series WHERE document_type=? AND COALESCE(financial_year_label,'')=? AND COALESCE(branch_code,'')=? AND COALESCE(warehouse_code,'')=? AND COALESCE(business_type_code,'')=? LIMIT 1",
                (
                    document_type,
                    financial_year_label or "",
                    branch_code or "",
                    warehouse_code or "",
                    business_type_code or "",
                ),
            ).fetchone()
            if existing:
                raise ValueError("Numbering series already exists for the specified document and scope.")
            cur = conn.execute(
                "INSERT INTO numbering_series(document_type,prefix,suffix,separator,financial_year_label,branch_code,warehouse_code,business_type_code,running_number,padding_length,start_number,current_number,reset_rule,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    document_type,
                    prefix or "",
                    suffix or "",
                    separator or "-",
                    financial_year_label or "",
                    branch_code or "",
                    warehouse_code or "",
                    business_type_code or "",
                    start_number - 1,
                    int(padding_length),
                    int(start_number),
                    start_number - 1,
                    reset_rule,
                    now,
                    now,
                ),
            )
            return int(cur.lastrowid)

    def update_series(self, series_id: int, data: dict[str, Any]) -> dict[str, Any]:
        self.ensure_schema()
        series = self.get_series(int(series_id))
        if not series:
            raise ValueError("Numbering series not found.")
        updated = {**series}
        for key in [
            "prefix",
            "suffix",
            "separator",
            "financial_year_label",
            "branch_code",
            "warehouse_code",
            "business_type_code",
            "padding_length",
            "start_number",
            "reset_rule",
            "is_active",
        ]:
            if key in data:
                updated[key] = data[key]
        if updated["reset_rule"] not in {self.RESET_NEVER, self.RESET_YEARLY, self.RESET_MONTHLY}:
            raise ValueError("Invalid reset rule.")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE numbering_series SET prefix=?,suffix=?,separator=?,financial_year_label=?,branch_code=?,warehouse_code=?,business_type_code=?,padding_length=?,start_number=?,reset_rule=?,is_active=?,updated_at=? WHERE id=?",
                (
                    str(updated["prefix"] or ""),
                    str(updated["suffix"] or ""),
                    str(updated["separator"] or "-"),
                    str(updated["financial_year_label"] or ""),
                    str(updated["branch_code"] or ""),
                    str(updated["warehouse_code"] or ""),
                    str(updated["business_type_code"] or ""),
                    int(updated["padding_length"] or 6),
                    int(updated["start_number"] or 1),
                    updated["reset_rule"],
                    1 if updated["is_active"] else 0,
                    datetime.now().isoformat(timespec="seconds"),
                    int(series_id),
                ),
            )
        return self.get_series(int(series_id))

    def generate_next(self, document_type: str, scope: dict[str, str] | None = None, preview: bool = False, reserved_by: str | None = None) -> str:
        self.ensure_schema()
        document_type = str(document_type or "").strip()
        if not document_type:
            raise ValueError("Document type is required.")
        scope = scope or {}
        now = datetime.now()
        series = self._find_series(document_type, scope)
        if series is None:
            raise ValueError("Numbering series not configured for this document type and scope.")
        if int(series["is_active"] or 0) == 0:
            raise ValueError("Numbering series is not active.")
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            with conn:
                current_text = str(series["current_number"] or 0)
                reset_rule = str(series["reset_rule"] or self.RESET_NEVER)
                if self._should_reset(series, now):
                    next_num = int(series["start_number"] or 1)
                    conn.execute(
                        "UPDATE numbering_series SET running_number=?, current_number=?, last_reset_at=?, updated_at=? WHERE id=?",
                        (next_num, next_num, now.isoformat(), now.isoformat(), int(series["id"])),
                    )
                else:
                    next_num = int(series["current_number"] or 0) + 1
                    if next_num < int(series["start_number"] or 1):
                        next_num = int(series["start_number"] or 1)
                    conn.execute(
                        "UPDATE numbering_series SET running_number=?, current_number=?, updated_at=? WHERE id=?",
                        (next_num, next_num, now.isoformat(), int(series["id"])),
                    )
                if preview:
                    conn.rollback()
                    next_num = int(series["current_number"] or 0) + 1 if not self._should_reset(series, now) else int(series["start_number"] or 1)
                formatted_number = self._format_number(series, next_num)
                if not preview:
                    self._reserve_number(conn, int(series["id"]), formatted_number, reserved_by)
                return formatted_number

    def reserve_number(self, numbering_series_id: int, number: str, reserved_by: str | None = None) -> int:
        self.ensure_schema()
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "INSERT INTO numbering_series_reservations(numbering_series_id,reserved_number,reserved_at,reserved_by,created_at) VALUES (?,?,?,?,?)",
                (int(numbering_series_id), str(number or ""), datetime.now().isoformat(timespec="seconds"), str(reserved_by or ""), datetime.now().isoformat(timespec="seconds")),
            )
            return int(cur.lastrowid)

    def cancel_reserved_number(self, reservation_id: int) -> None:
        self.ensure_schema()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE numbering_series_reservations SET status='cancelled',cancelled_at=?,updated_at=? WHERE id=?",
                (datetime.now().isoformat(timespec="seconds"), datetime.now().isoformat(timespec="seconds"), int(reservation_id)),
            )

    def get_reservation(self, reservation_id: int) -> dict[str, Any] | None:
        self.ensure_schema()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM numbering_series_reservations WHERE id=?", (int(reservation_id),)).fetchone()
            return dict(row) if row else None

    def _find_series(self, document_type: str, scope: dict[str, str] | None) -> dict[str, Any] | None:
        scope = scope or {}
        keys = [
            "financial_year_label",
            "branch_code",
            "warehouse_code",
            "business_type_code",
        ]
        query = "SELECT * FROM numbering_series WHERE document_type=?"
        params: list[Any] = [document_type]
        for key in keys:
            query += f" AND COALESCE({key},'')=?"
            params.append(str(scope.get(key) or ""))
        query += " LIMIT 1"
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(query, tuple(params)).fetchone()
            return dict(row) if row else None

    def _should_reset(self, series: dict[str, Any], now: datetime) -> bool:
        reset_rule = str(series["reset_rule"] or self.RESET_NEVER)
        last_reset_at = series.get("last_reset_at")
        if reset_rule == self.RESET_NEVER:
            return False
        if not last_reset_at:
            return True
        try:
            last_reset = datetime.fromisoformat(str(last_reset_at))
        except ValueError:
            return True
        if reset_rule == self.RESET_YEARLY:
            return last_reset.year != now.year
        if reset_rule == self.RESET_MONTHLY:
            return last_reset.year != now.year or last_reset.month != now.month
        return False

    def _format_number(self, series: dict[str, Any], running_number: int) -> str:
        prefix = str(series.get("prefix") or "").strip()
        suffix = str(series.get("suffix") or "").strip()
        separator = str(series.get("separator") or "-").strip()
        padding = int(series.get("padding_length") or 6)
        running_text = str(running_number).zfill(padding)
        parts = []
        if prefix:
            parts.append(prefix)
        if str(series.get("financial_year_label") or ""):
            parts.append(str(series.get("financial_year_label")))
        parts.append(running_text)
        if suffix:
            parts.append(suffix)
        return separator.join(parts)

    def _reserve_number(self, conn: sqlite3.Connection, series_id: int, number: str, reserved_by: str | None = None) -> None:
        conn.execute(
            "INSERT INTO numbering_series_reservations(numbering_series_id,reserved_number,reserved_at,reserved_by,created_at) VALUES (?,?,?,?,?)",
            (int(series_id), str(number), datetime.now().isoformat(timespec="seconds"), str(reserved_by or ""), datetime.now().isoformat(timespec="seconds")),
        )
