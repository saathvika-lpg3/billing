from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from pypdf import PdfReader, PdfWriter

from config.app_config import AppConfig


class DocumentArchiveService:
    def __init__(self, config: AppConfig, db_path: Path) -> None:
        self.config = config
        self.db_path = Path(db_path)

    def archive_path(self, meta: dict[str, Any], extension: str = "pdf") -> Path:
        folder = self.archive_folder(meta)
        doc_no = str(meta.get("doc_no") or meta.get("document_no") or meta.get("report_name") or meta.get("document_type") or "Document")
        base = f"{datetime.now():%Y-%m-%d_%H%M%S}_{self.sanitize(doc_no, 'Document')}"
        extension = extension.strip(".").lower() or "pdf"
        path = folder / f"{base}.{extension}"
        index = 1
        while path.exists():
            path = folder / f"{base}_{index}.{extension}"
            index += 1
        return path

    def archive_folder(self, meta: dict[str, Any]) -> Path:
        root = self.archive_root()
        category = self.category(meta)
        doc_date = str(meta.get("doc_date") or "")[:10]
        month = self.month_folder(doc_date)
        report_name = str(meta.get("report_name") or "").strip()
        party_name = str(meta.get("party_name") or "").strip()
        document_type = str(meta.get("document_type") or "Others")
        if report_name:
            leaf = report_name
        elif party_name:
            leaf = party_name
        else:
            leaf = document_type
        folder = root / self.sanitize(category, "Others") / month / self.sanitize(leaf, "Document")
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def archive_root(self) -> Path:
        home = Path.home()
        preferred = home / "Documents" / "PRM Billing and Inventory" / "Archive"
        try:
            preferred.mkdir(parents=True, exist_ok=True)
            if preferred.exists():
                return preferred
        except OSError:
            pass
        fallback = self.config.project_root / "documents" / "archive"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback

    def log_archive(self, meta: dict[str, Any], files: list[Path], status: str, message: str, action: str) -> None:
        self.ensure_schema()
        root = self.archive_root()
        folder = files[0].parent if files else Path("")
        total_size = sum(path.stat().st_size for path in files if path.exists())
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO document_archive_logs(
                    user_id,user_name,company_id,company_name,module,document_type,document_no,
                    party_name,action,status,file_count,total_size,root_path,folder_path,
                    files_json,message,created_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    None,
                    "Desktop User",
                    int(meta.get("company_id") or 0),
                    str(meta.get("company_name") or ""),
                    str(meta.get("module") or "document_center"),
                    str(meta.get("document_type") or ""),
                    str(meta.get("doc_no") or meta.get("document_no") or ""),
                    str(meta.get("party_name") or ""),
                    action,
                    status,
                    len(files),
                    total_size,
                    str(root),
                    str(folder),
                    json.dumps([str(path) for path in files], ensure_ascii=True),
                    message,
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            conn.commit()

    def create_print_batch(self, document_type: str, scope: str, filters: dict[str, Any], count: int, reason: str = "") -> int:
        self.ensure_schema()
        batch_no = f"PB-{datetime.now():%y%m%d-%H%M%S}"
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO print_batches(
                    batch_no,document_type,print_scope,filter_json,document_count,
                    reprint_reason,status,printed_by_user_id,printed_by_user_name,created_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    batch_no,
                    document_type,
                    scope,
                    json.dumps(filters, ensure_ascii=True),
                    count,
                    reason,
                    "Success",
                    None,
                    "Desktop User",
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def record_print(
        self,
        table: str,
        document_id: int,
        document_type: str,
        document_no: str,
        party_name: str,
        *,
        batch_id: int | None = None,
        module: str = "document_center",
        action: str = "Print Preview",
    ) -> None:
        if document_id <= 0:
            return
        self.ensure_schema()
        now = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO print_logs(
                    user_id,user_name,batch_id,module,document_table,document_id,
                    document_type,document_no,party_name,action,ip_address,created_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (None, "Desktop User", batch_id, module, table, document_id, document_type, document_no, party_name, action, "local", now),
            )
            if table in {"sales", "purchases"}:
                conn.execute(
                    f"UPDATE {table} SET print_count=COALESCE(print_count,0)+1,last_printed_at=?,last_printed_by=? WHERE id=?",
                    (now, "Desktop User", document_id),
                )
            conn.commit()

    def merge_pdfs(self, sources: list[Path], target: Path) -> Path:
        target.parent.mkdir(parents=True, exist_ok=True)
        writer = PdfWriter()
        for source in sources:
            reader = PdfReader(str(source))
            for page in reader.pages:
                writer.add_page(page)
        with target.open("wb") as handle:
            writer.write(handle)
        return target

    def ensure_schema(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS document_archive_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,user_name TEXT,company_id INTEGER,company_name TEXT,
                    module TEXT,document_type TEXT,document_no TEXT,party_name TEXT,
                    action TEXT,status TEXT,file_count INTEGER,total_size INTEGER,
                    root_path TEXT,folder_path TEXT,files_json TEXT,message TEXT,created_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS print_batches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_no TEXT,document_type TEXT,print_scope TEXT,filter_json TEXT,
                    document_count INTEGER,reprint_reason TEXT,status TEXT,
                    printed_by_user_id INTEGER,printed_by_user_name TEXT,created_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS print_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,user_name TEXT,batch_id INTEGER,module TEXT,
                    document_table TEXT,document_id INTEGER,document_type TEXT,
                    document_no TEXT,party_name TEXT,action TEXT,ip_address TEXT,created_at TEXT
                )
                """
            )
            conn.commit()

    @classmethod
    def category(cls, meta: dict[str, Any]) -> str:
        explicit = str(meta.get("category") or "").strip()
        if explicit:
            return explicit
        value = f"{meta.get('document_type') or ''} {meta.get('module') or ''} {meta.get('report_name') or ''}".lower()
        if "sales_return" in value or "credit note" in value:
            return "Sales Return"
        if "purchase_return" in value or "debit note" in value:
            return "Purchase Return"
        if "quotation" in value:
            return "Quotations"
        if "delivery" in value or "challan" in value:
            return "Delivery Challan"
        if "purchase" in value:
            return "Purchase"
        if "sale" in value or "sales" in value:
            return "Sales"
        if "batch" in value or "bulk" in value:
            return "Print Batches"
        return "Others"

    @staticmethod
    def month_folder(value: str) -> str:
        for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(value[:10], fmt).strftime("%Y-%m_%B")
            except ValueError:
                pass
        return datetime.now().strftime("%Y-%m_%B")

    @staticmethod
    def sanitize(value: str, fallback: str = "Others") -> str:
        cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1F]+', " ", str(value or ""))
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" .\t\r\n")
        if not cleaned:
            cleaned = fallback
        reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
        if cleaned.upper() in reserved:
            cleaned += "_file"
        return cleaned[:120] or fallback
