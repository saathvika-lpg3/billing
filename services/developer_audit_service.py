from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from services.mysql_source import MySqlSource


class DeveloperAuditService:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else MySqlSource().sqlite_path

    def ensure_schema(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS developer_login_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    attempted_at TEXT,
                    username TEXT,
                    machine_hash TEXT,
                    success INTEGER,
                    reason TEXT,
                    app_version TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS company_profile_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    changed_at TEXT,
                    changed_by TEXT,
                    source TEXT,
                    field_name TEXT,
                    old_value TEXT,
                    new_value TEXT,
                    machine_id TEXT,
                    reason TEXT
                )
                """
            )

    def log_attempt(self, username: str, success: bool, reason: str = "", app_version: str | None = None) -> None:
        self.ensure_schema()
        now = datetime.now().isoformat(timespec="seconds")
        try:
            import platform
            from services.license_service import LicenseService

            machine = LicenseService.machine_hash()
        except Exception:
            machine = ""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO developer_login_attempts(attempted_at,username,machine_hash,success,reason,app_version) VALUES (?,?,?,?,?,?)",
                (now, username or "",  machine or "", 1 if success else 0, reason or "", app_version or ""),
            )

    def log_company_audit(self, changed_by: str, source: str, field_name: str, old_value: str, new_value: str, reason: str | None = None) -> None:
        self.ensure_schema()
        now = datetime.now().isoformat(timespec="seconds")
        try:
            from services.license_service import LicenseService

            machine = LicenseService.machine_hash()
        except Exception:
            machine = ""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO company_profile_audit(changed_at,changed_by,source,field_name,old_value,new_value,machine_id,reason) VALUES (?,?,?,?,?,?,?,?)",
                    (now, changed_by or "", source or "", field_name or "", old_value or "", new_value or "", machine or "", reason or ""),
                )
        except Exception:
            # Audit must not block main flow
            return

    def log_company_audit_conn(self, conn: sqlite3.Connection, changed_by: str, source: str, field_name: str, old_value: str, new_value: str, reason: str | None = None) -> None:
        """Write audit using an existing sqlite3.Connection to avoid cross-connection locking."""
        now = datetime.now().isoformat(timespec="seconds")
        try:
            from services.license_service import LicenseService

            try:
                machine = LicenseService.machine_hash()
            except Exception:
                machine = ""
            conn.execute(
                "INSERT INTO company_profile_audit(changed_at,changed_by,source,field_name,old_value,new_value,machine_id,reason) VALUES (?,?,?,?,?,?,?,?)",
                (now, changed_by or "", source or "", field_name or "", old_value or "", new_value or "", machine or "", reason or ""),
            )
        except Exception:
            # Audit must not block main flow
            return
