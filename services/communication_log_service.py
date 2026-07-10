from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from services.email_service import EmailDeliveryService
from services.mysql_source import MySqlSource


RETRYABLE_EMAIL_CODES = {"smtp_failed", "open_failed"}


def mask_recipient(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if "@" in text:
        local, _, domain = text.partition("@")
        if not domain:
            return "***"
        visible = local[:1] if local else ""
        return f"{visible}***@{domain}"
    digits = re.sub(r"\D+", "", text)
    if len(digits) >= 7:
        return f"{'*' * max(3, len(digits) - 4)}{digits[-4:]}"
    if len(text) <= 2:
        return "***"
    return f"{text[:1]}***{text[-1:]}"


def safe_log_text(value: object) -> str:
    text = str(value or "")
    if not text:
        return ""
    text = re.sub(r"([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+\.[A-Za-z]{2,})", r"\1***@\2", text)
    text = re.sub(r"\b\d{7,15}\b", lambda match: f"{'*' * max(3, len(match.group(0)) - 4)}{match.group(0)[-4:]}", text)
    return text[:500]


class CommunicationLogService:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else MySqlSource().sqlite_path

    def ensure_schema(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS communication_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel TEXT NOT NULL,
                    recipient TEXT,
                    subject TEXT,
                    body TEXT,
                    attachment_path TEXT,
                    status TEXT NOT NULL,
                    result_code TEXT,
                    result_message TEXT,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    next_retry_at TEXT,
                    last_attempt_at TEXT,
                    sent_at TEXT,
                    metadata_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_communication_logs_retry
                ON communication_logs(channel,status,next_retry_at,updated_at)
                """
            )

    def log_result(
        self,
        *,
        channel: str,
        recipient: object,
        subject: str,
        body: str,
        attachment_path: Path | str | None,
        result: dict[str, object],
        metadata: dict[str, object] | None = None,
    ) -> int:
        self.ensure_schema()
        now = datetime.now().isoformat(timespec="seconds")
        status = self._status_for_result(result)
        code = str(result.get("code") or "")
        attempts = 1 if channel == "email" and code.startswith("smtp") else 0
        sent_at = now if status == "Sent" else None
        next_retry_at = None
        safe_attachment = self._safe_attachment_name(attachment_path)
        safe_metadata = self._safe_metadata(metadata, recipient, attachment_path)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                """
                INSERT INTO communication_logs(
                    channel,recipient,subject,body,attachment_path,status,result_code,
                    result_message,attempts,next_retry_at,last_attempt_at,sent_at,
                    metadata_json,created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    channel,
                    mask_recipient(recipient),
                    safe_log_text(subject),
                    "",
                    safe_attachment,
                    status,
                    code,
                    safe_log_text(result.get("message") or ""),
                    attempts,
                    next_retry_at,
                    now if attempts else None,
                    sent_at,
                    json.dumps(safe_metadata, ensure_ascii=True, sort_keys=True),
                    now,
                    now,
                ),
            )
            return int(cur.lastrowid or 0)

    def recent_logs(self, limit: int = 200) -> list[dict[str, Any]]:
        self.ensure_schema()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT id,channel,recipient,subject,status,result_code,result_message,
                       attempts,next_retry_at,sent_at,created_at,updated_at
                FROM communication_logs
                ORDER BY id DESC
                LIMIT ?
                """,
                (max(1, int(limit)),),
            ).fetchall()
            result_rows = []
            for row in rows:
                item = dict(row)
                item["recipient"] = mask_recipient(item.get("recipient"))
                item["result_message"] = safe_log_text(item.get("result_message"))
                result_rows.append(item)
            return result_rows

    def pending_retries(self, limit: int = 50) -> list[dict[str, Any]]:
        self.ensure_schema()
        now = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT *
                FROM communication_logs
                WHERE channel='email'
                  AND status IN ('Failed','Queued')
                  AND COALESCE(recipient,'') <> ''
                  AND recipient NOT LIKE '%***%'
                  AND COALESCE(attachment_path,'') <> ''
                  AND LOWER(attachment_path) LIKE '%.pdf'
                  AND (instr(attachment_path, ':') > 0 OR substr(attachment_path,1,1)='/' OR substr(attachment_path,1,2)='\\')
                  AND (next_retry_at IS NULL OR next_retry_at <= ?)
                ORDER BY COALESCE(next_retry_at, updated_at), id
                LIMIT ?
                """,
                (now, max(1, int(limit))),
            ).fetchall()
            return [dict(row) for row in rows]

    def retry_pending_emails(
        self,
        *,
        delivery_service: EmailDeliveryService | None = None,
        limit: int = 10,
    ) -> list[dict[str, object]]:
        service = delivery_service or EmailDeliveryService.from_environment(self.db_path)
        results: list[dict[str, object]] = []
        for row in self.pending_retries(limit):
            log_id = int(row["id"])
            pdf_path = Path(str(row.get("attachment_path") or ""))
            result = service.send_pdf(row.get("recipient"), str(row.get("subject") or ""), str(row.get("body") or ""), pdf_path)
            self.update_result(log_id, result)
            results.append({"id": log_id, **result})
        return results

    def update_result(self, log_id: int, result: dict[str, object]) -> None:
        self.ensure_schema()
        now = datetime.now().isoformat(timespec="seconds")
        status = self._status_for_result(result)
        code = str(result.get("code") or "")
        with sqlite3.connect(self.db_path) as conn:
            current = conn.execute("SELECT attempts FROM communication_logs WHERE id=?", (log_id,)).fetchone()
            attempts = int(current[0] or 0) + 1 if current else 1
            conn.execute(
                """
                UPDATE communication_logs
                SET status=?,
                    result_code=?,
                    result_message=?,
                    attempts=?,
                    next_retry_at=?,
                    last_attempt_at=?,
                    sent_at=CASE WHEN ?='Sent' THEN ? ELSE sent_at END,
                    updated_at=?
                WHERE id=?
                """,
                (
                    status,
                    code,
                    safe_log_text(result.get("message") or ""),
                    attempts,
                    self._next_retry_at(status, code, attempts),
                    now,
                    status,
                    now,
                    now,
                    log_id,
                ),
            )

    def _status_for_result(self, result: dict[str, object]) -> str:
        if bool(result.get("ok")) and result.get("code") == "smtp_sent":
            return "Sent"
        if bool(result.get("ok")):
            return "Handed Off"
        if str(result.get("code") or "") in RETRYABLE_EMAIL_CODES:
            return "Failed"
        return "Failed"

    def _next_retry_at(self, status: str, code: str, attempts: int) -> str | None:
        if status != "Failed" or code not in RETRYABLE_EMAIL_CODES:
            return None
        delay_minutes = min(240, max(15, attempts * 15))
        return (datetime.now() + timedelta(minutes=delay_minutes)).isoformat(timespec="seconds")

    def _safe_attachment_name(self, attachment_path: Path | str | None) -> str:
        if not attachment_path:
            return ""
        try:
            return Path(str(attachment_path)).name
        except (TypeError, ValueError):
            return ""

    def _safe_metadata(
        self,
        metadata: dict[str, object] | None,
        recipient: object,
        attachment_path: Path | str | None,
    ) -> dict[str, object]:
        safe: dict[str, object] = {
            "recipient": mask_recipient(recipient),
            "attachment_name": self._safe_attachment_name(attachment_path),
            "privacy": "recipient_masked_body_omitted_path_filename_only",
        }
        for key, value in (metadata or {}).items():
            if isinstance(value, (int, float, bool)) or value is None:
                safe[str(key)] = value
            else:
                safe[str(key)] = safe_log_text(value)
        return safe
