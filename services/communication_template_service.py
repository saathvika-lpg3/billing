from __future__ import annotations

import re
import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from services.mysql_source import MySqlSource


DEFAULT_TEMPLATES = [
    {
        "template_code": "sales_invoice_email",
        "channel": "email",
        "document_type": "sales_invoice",
        "template_name": "Sales Invoice Email",
        "subject_template": "Invoice {document_no}",
        "body_template": "Dear {party_name},\n\nPlease find the invoice PDF attached.\n\nAmount: {amount}\n\nRegards,\n{company_name}",
    },
    {
        "template_code": "receipt_email",
        "channel": "email",
        "document_type": "receipt",
        "template_name": "Receipt Email",
        "subject_template": "Receipt {document_no}",
        "body_template": "Dear {party_name},\n\nPayment receipt {document_no} is ready.\n\nAmount: {amount}\n\nRegards,\n{company_name}",
    },
    {
        "template_code": "purchase_invoice_email",
        "channel": "email",
        "document_type": "purchase_invoice",
        "template_name": "Purchase Invoice Email",
        "subject_template": "Purchase Invoice {document_no}",
        "body_template": "Dear {party_name},\n\nPlease find the purchase invoice PDF attached.\n\nAmount: {amount}\n\nRegards,\n{company_name}",
    },
    {
        "template_code": "quotation_email",
        "channel": "email",
        "document_type": "quotation",
        "template_name": "Quotation Email",
        "subject_template": "Quotation {document_no}",
        "body_template": "Dear {party_name},\n\nPlease find the quotation PDF attached.\n\nAmount: {amount}\n\nRegards,\n{company_name}",
    },
    {
        "template_code": "sales_order_email",
        "channel": "email",
        "document_type": "sales_order",
        "template_name": "Sales Order Email",
        "subject_template": "Sales Order {document_no}",
        "body_template": "Dear {party_name},\n\nPlease find the sales order PDF attached.\n\nAmount: {amount}\n\nRegards,\n{company_name}",
    },
    {
        "template_code": "purchase_order_email",
        "channel": "email",
        "document_type": "purchase_order",
        "template_name": "Purchase Order Email",
        "subject_template": "Purchase Order {document_no}",
        "body_template": "Dear {party_name},\n\nPlease find the purchase order PDF attached.\n\nRegards,\n{company_name}",
    },
    {
        "template_code": "sales_invoice_whatsapp",
        "channel": "whatsapp",
        "document_type": "sales_invoice",
        "template_name": "Sales Invoice WhatsApp",
        "subject_template": "Invoice {document_no}",
        "body_template": "{company_name}\nInvoice {document_no}\nParty: {party_name}\nAmount: {amount}\nPDF: {pdf_path}",
    },
    {
        "template_code": "receipt_whatsapp",
        "channel": "whatsapp",
        "document_type": "receipt",
        "template_name": "Receipt WhatsApp",
        "subject_template": "Receipt {document_no}",
        "body_template": "{company_name}\nReceipt {document_no}\nParty: {party_name}\nAmount: {amount}\nPDF: {pdf_path}",
    },
    {
        "template_code": "payment_reminder_whatsapp",
        "channel": "whatsapp",
        "document_type": "payment_reminder",
        "template_name": "Payment Reminder WhatsApp",
        "subject_template": "Payment Reminder",
        "body_template": "Dear {party_name}, payment of {amount} is pending for {document_no}. Please review at your convenience.",
    },
]


CONTACT_FIELD_CANDIDATES = {
    "email": ("email", "customer_email", "supplier_email", "party_email", "billing_email", "contact_email"),
    "whatsapp": ("whatsapp", "whatsapp_no", "mobile", "phone", "customer_phone", "supplier_phone", "party_phone"),
    "sms": ("mobile", "phone", "customer_phone", "supplier_phone", "party_phone"),
}


class CommunicationTemplateService:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else MySqlSource().sqlite_path

    def ensure_schema(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS communication_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_code TEXT NOT NULL UNIQUE,
                    channel TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    template_name TEXT NOT NULL,
                    subject_template TEXT,
                    body_template TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_communication_templates_lookup
                ON communication_templates(channel,document_type,is_active)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS communication_contact_preferences (
                    channel TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    preferred_field TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY(channel, document_type)
                )
                """
            )

    def seed_defaults(self) -> None:
        self.ensure_schema()
        now = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(self.db_path) as conn:
            for template in DEFAULT_TEMPLATES:
                conn.execute(
                    """
                    INSERT INTO communication_templates(
                        template_code,channel,document_type,template_name,
                        subject_template,body_template,is_active,created_at,updated_at
                    ) VALUES(?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(template_code) DO NOTHING
                    """,
                    (
                        template["template_code"],
                        template["channel"],
                        template["document_type"],
                        template["template_name"],
                        template["subject_template"],
                        template["body_template"],
                        1,
                        now,
                        now,
                    ),
                )

    def templates(self, limit: int = 200) -> list[dict[str, Any]]:
        self.seed_defaults()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT id,template_code,channel,document_type,template_name,
                       subject_template,body_template,is_active,updated_at
                FROM communication_templates
                ORDER BY channel,document_type,template_code
                LIMIT ?
                """,
                (max(1, int(limit)),),
            ).fetchall()
            return [dict(row) for row in rows]

    def active_template(self, channel: str, document_type: str) -> dict[str, Any]:
        self.seed_defaults()
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT id,template_code,channel,document_type,template_name,
                       subject_template,body_template,is_active,updated_at
                FROM communication_templates
                WHERE LOWER(channel)=LOWER(?)
                  AND LOWER(document_type)=LOWER(?)
                  AND COALESCE(is_active,1)=1
                ORDER BY id DESC
                LIMIT 1
                """,
                (self._clean(channel), self._clean(document_type)),
            ).fetchone()
            return dict(row) if row else {}

    def save_template(self, payload: Mapping[str, object]) -> int:
        self.ensure_schema()
        code = self._template_code(payload.get("template_code"))
        channel = self._clean(payload.get("channel")) or "email"
        document_type = self._clean(payload.get("document_type")) or "general"
        name = self._clean(payload.get("template_name")) or code.replace("_", " ").title()
        subject = self._clean(payload.get("subject_template"))
        body = self._clean(payload.get("body_template"))
        if not code:
            raise ValueError("Template code is required.")
        if not body:
            raise ValueError("Template body is required.")
        now = datetime.now().isoformat(timespec="seconds")
        active = 1 if int(payload.get("is_active", 1) or 0) else 0
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                """
                INSERT INTO communication_templates(
                    template_code,channel,document_type,template_name,
                    subject_template,body_template,is_active,created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?)
                ON CONFLICT(template_code) DO UPDATE SET
                    channel=excluded.channel,
                    document_type=excluded.document_type,
                    template_name=excluded.template_name,
                    subject_template=excluded.subject_template,
                    body_template=excluded.body_template,
                    is_active=excluded.is_active,
                    updated_at=excluded.updated_at
                """,
                (code, channel, document_type, name, subject, body, active, now, now),
            )
            row = conn.execute("SELECT id FROM communication_templates WHERE template_code=?", (code,)).fetchone()
            return int(row[0] if row else cur.lastrowid or 0)

    def render_template(self, template: Mapping[str, object], context: Mapping[str, object]) -> dict[str, str]:
        values = defaultdict(str, {str(key): "" if value is None else str(value) for key, value in context.items()})
        return {
            "subject": str(template.get("subject_template") or "").format_map(values),
            "body": str(template.get("body_template") or "").format_map(values),
        }

    def render_for_document(
        self,
        *,
        channel: str,
        document_type: str,
        context: Mapping[str, object],
        fallback_subject: str,
        fallback_body: str,
    ) -> dict[str, str]:
        template = self.active_template(channel, document_type)
        if not template:
            return {"subject": fallback_subject, "body": fallback_body, "template_code": ""}
        rendered = self.render_template(template, context)
        return {
            "subject": rendered.get("subject") or fallback_subject,
            "body": rendered.get("body") or fallback_body,
            "template_code": str(template.get("template_code") or ""),
        }

    def contact_fields(self, channel: str) -> tuple[str, ...]:
        normalized_channel = self._clean(channel).lower()
        return CONTACT_FIELD_CANDIDATES.get(normalized_channel, CONTACT_FIELD_CANDIDATES["email"])

    def contact_preference(self, channel: str, document_type: str) -> str:
        self.ensure_schema()
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT preferred_field
                FROM communication_contact_preferences
                WHERE LOWER(channel)=LOWER(?) AND LOWER(document_type)=LOWER(?)
                """,
                (self._clean(channel), self._clean(document_type)),
            ).fetchone()
        preferred = self._clean(row[0] if row else "")
        return preferred if preferred in self.contact_fields(channel) else ""

    def save_contact_preference(self, channel: str, document_type: str, preferred_field: str) -> None:
        self.ensure_schema()
        normalized_channel = self._clean(channel).lower() or "email"
        normalized_document = self._clean(document_type) or "general"
        field = self._clean(preferred_field)
        if field and field not in self.contact_fields(normalized_channel):
            raise ValueError(f"Unsupported contact field for {normalized_channel}: {field}")
        with sqlite3.connect(self.db_path) as conn:
            if not field:
                conn.execute(
                    """
                    DELETE FROM communication_contact_preferences
                    WHERE LOWER(channel)=LOWER(?) AND LOWER(document_type)=LOWER(?)
                    """,
                    (normalized_channel, normalized_document),
                )
                return
            conn.execute(
                """
                INSERT INTO communication_contact_preferences(channel,document_type,preferred_field,updated_at)
                VALUES(?,?,?,?)
                ON CONFLICT(channel,document_type) DO UPDATE SET
                    preferred_field=excluded.preferred_field,
                    updated_at=excluded.updated_at
                """,
                (normalized_channel, normalized_document, field, datetime.now().isoformat(timespec="seconds")),
            )

    def resolve_contact(
        self,
        channel: str,
        *sources: Mapping[str, object],
        document_type: str = "",
        preferred_field: str = "",
    ) -> dict[str, str]:
        normalized_channel = self._clean(channel).lower()
        preferred = self._clean(preferred_field)
        if not preferred and document_type:
            preferred = self.contact_preference(normalized_channel, document_type)
        candidates = list(self.contact_fields(normalized_channel))
        if preferred and preferred in candidates:
            candidates.remove(preferred)
            candidates.insert(0, preferred)
        for source in sources:
            for field in candidates:
                value = self._clean(source.get(field))
                if value:
                    return {"channel": normalized_channel, "field": field, "value": value}
        return {"channel": normalized_channel, "field": "", "value": ""}

    def _template_code(self, value: object) -> str:
        text = self._clean(value).lower()
        text = re.sub(r"[^a-z0-9_]+", "_", text)
        return re.sub(r"_+", "_", text).strip("_")

    def _clean(self, value: object) -> str:
        return str(value or "").strip()
