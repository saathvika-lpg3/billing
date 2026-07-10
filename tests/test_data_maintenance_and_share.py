from __future__ import annotations

import json
import os
import shutil
import sqlite3
from datetime import date
from pathlib import Path

from config.app_config import AppConfig
from services.data_maintenance_service import DataMaintenanceService
from services.dashboard_service import DashboardService
from services.company_profile_service import CompanyProfileService
from services.communication_log_service import CommunicationLogService
from services.communication_template_service import CommunicationTemplateService
from services.email_service import EmailDeliveryService, SmtpEmailConfig, protect_secret, unprotect_secret
from services.share_service import (
    communication_message,
    document_message_context,
    normalize_phone,
    pdf_share_note,
    prepare_email_document,
    prepare_whatsapp_document,
    whatsapp_readiness,
    whatsapp_native_url,
    whatsapp_url,
)


SOURCE_DB = Path(r"D:\PRM_GST_DESKTOP\database\prm_billing_inventory.db")


def _copy_db(tmp_path: Path) -> Path:
    target = tmp_path / "prm_billing_inventory.db"
    shutil.copy2(SOURCE_DB, target)
    return target


def test_free_space_exports_backs_up_and_deletes_selected_year_transactions(tmp_path: Path) -> None:
    db_path = _copy_db(tmp_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO sales(
                bill_no,bill_date,customer_id,customer_name,pay_mode,taxable,gst_total,
                cgst_total,sgst_total,igst_total,round_off,grand_total,status,created_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            ("OLD-2018-001", "2018-04-15", 0, "Archive Customer", "Cash", 100, 18, 9, 9, 0, 0, 118, "Active", "2018-04-15T10:00:00"),
        )
        sale_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            """
            INSERT INTO sales_items(
                sale_id,item_name,hsn,unit,mrp,qty,rate,gst,taxable,gst_amt,cgst,sgst,igst,total
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (sale_id, "Archive Item", "1905", "PCS", 118, 1, 100, 18, 100, 18, 9, 9, 0, 118),
        )
        conn.commit()

    service = DataMaintenanceService(AppConfig(project_root=tmp_path, source_root=tmp_path), db_path)
    result = service.free_space_by_year_range(2018, 2018, user_name="QA Developer")

    assert result.backup_path.exists()
    assert result.export_path.exists()
    assert result.records_exported >= 2
    assert result.records_deleted >= 2
    assert result.table_counts["sales"] >= 1
    assert result.table_counts["sales_items"] >= 1

    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM sales WHERE bill_no='OLD-2018-001'").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM sales_items WHERE sale_id=?", (sale_id,)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM company").fetchone()[0] >= 1
        log = conn.execute(
            """
            SELECT operation,status,records_exported,records_deleted,details_json
            FROM data_maintenance_logs
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    assert log[0] == "free_space_year_range"
    assert log[1] == "Success"
    assert log[2] >= 2
    assert log[3] >= 2
    details = json.loads(log[4])
    assert details["from_year"] == 2018
    assert details["to_year"] == 2018


def test_whatsapp_links_support_native_and_web_fallbacks(tmp_path: Path) -> None:
    pdf = tmp_path / "invoice.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")

    assert normalize_phone("90000 00000") == "919000000000"
    assert whatsapp_url("9000000000", "Invoice ready").startswith("https://web.whatsapp.com/send?phone=919000000000")
    assert whatsapp_native_url("9000000000", "Invoice ready").startswith("whatsapp://send?phone=919000000000")
    readiness = whatsapp_readiness("90000 00000", "Invoice ready")
    assert readiness["ok"] is True
    assert readiness["code"] == "link_ready"
    assert readiness["phone"] == "919000000000"
    assert whatsapp_readiness("", "Invoice ready")["code"] == "missing_phone"
    assert str(pdf) in pdf_share_note(pdf)


def test_whatsapp_attachment_helper_validates_inputs(tmp_path: Path) -> None:
    pdf = tmp_path / "missing.pdf"

    result = prepare_whatsapp_document("9000000000", "Invoice ready", pdf)

    assert result["ok"] is False
    assert "not ready" in str(result["message"])


def test_smtp_email_service_sends_pdf_attachment(tmp_path: Path) -> None:
    pdf = tmp_path / "invoice.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    instances = []

    class FakeSMTP:
        def __init__(self, host: str, port: int, timeout: float | None = None) -> None:
            self.host = host
            self.port = port
            self.timeout = timeout
            self.started_tls = False
            self.login_args = None
            self.sent_message = None
            instances.append(self)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def starttls(self) -> None:
            self.started_tls = True

        def login(self, username: str, password: str) -> None:
            self.login_args = (username, password)

        def send_message(self, message) -> None:
            self.sent_message = message

    config = SmtpEmailConfig(
        delivery_mode="smtp",
        host="smtp.example.test",
        port=2525,
        username="operator@example.test",
        password="secret",
        from_email="operator@example.test",
    )
    service = EmailDeliveryService(config, smtp_factory=FakeSMTP)

    result = service.send_pdf("customer@example.test", "Invoice", "Please find attached.", pdf)

    assert result["ok"] is True
    assert result["code"] == "smtp_sent"
    smtp = instances[0]
    assert (smtp.host, smtp.port, smtp.timeout) == ("smtp.example.test", 2525, 20.0)
    assert smtp.started_tls is True
    assert smtp.login_args == ("operator@example.test", "secret")
    assert smtp.sent_message["To"] == "customer@example.test"
    assert smtp.sent_message["Subject"] == "Invoice"
    assert [attachment.get_filename() for attachment in smtp.sent_message.iter_attachments()] == ["invoice.pdf"]
    diagnostic = service.test_connection()
    assert diagnostic["ok"] is True
    assert diagnostic["code"] == "smtp_ready"
    assert instances[-1].login_args == ("operator@example.test", "secret")


def test_smtp_email_diagnostic_reports_disabled_or_missing_config() -> None:
    disabled = EmailDeliveryService(SmtpEmailConfig(delivery_mode="handoff"))
    missing = EmailDeliveryService(SmtpEmailConfig(delivery_mode="smtp"))

    assert disabled.test_connection()["code"] == "smtp_not_enabled"
    assert missing.test_connection()["code"] == "smtp_not_configured"


def test_prepare_email_document_uses_smtp_or_falls_back_to_mail_client(tmp_path: Path, monkeypatch) -> None:
    pdf = tmp_path / "invoice.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")

    class EnabledService:
        def send_pdf(self, recipient, subject, body, pdf_path):
            return {"ok": True, "code": "smtp_sent", "message": "Email sent.", "file": str(pdf_path)}

    monkeypatch.setattr(
        "services.share_service.open_email_share",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("handoff should not open when SMTP sends")),
    )
    sent = prepare_email_document("customer@example.test", "Invoice", "Ready", pdf, delivery_service=EnabledService())
    assert sent["code"] == "smtp_sent"

    class DisabledService:
        def send_pdf(self, recipient, subject, body, pdf_path):
            return {"ok": False, "code": "smtp_not_enabled", "message": "SMTP disabled."}

    monkeypatch.setattr("services.share_service.open_email_share", lambda recipient, subject, body: "mailto:customer@example.test")
    handed_off = prepare_email_document("customer@example.test", "Invoice", "Ready", pdf, delivery_service=DisabledService())
    assert handed_off["ok"] is True
    assert handed_off["code"] == "opened"


def test_smtp_config_reads_app_settings(tmp_path: Path) -> None:
    db_path = tmp_path / "settings.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE app_settings(setting_key TEXT PRIMARY KEY, setting_value TEXT, updated_at TEXT)")
        conn.executemany(
            "INSERT INTO app_settings(setting_key,setting_value,updated_at) VALUES(?,?,datetime('now'))",
            [
                ("email.delivery_mode", "smtp"),
                ("smtp.host", "smtp.local.test"),
                ("smtp.port", "2525"),
                ("smtp.username", "operator@local.test"),
                ("smtp.password", "secret"),
                ("smtp.from_email", "billing@local.test"),
                ("smtp.use_tls", "0"),
                ("smtp.use_ssl", "1"),
                ("smtp.timeout", "12"),
            ],
        )

    config = SmtpEmailConfig.from_sources(db_path=db_path, env={})

    assert config.smtp_enabled is True
    assert config.host == "smtp.local.test"
    assert config.port == 2525
    assert config.username == "operator@local.test"
    assert config.password == "secret"
    assert config.from_email == "billing@local.test"
    assert config.use_tls is False
    assert config.use_ssl is True
    assert config.timeout == 12
    with sqlite3.connect(db_path) as conn:
        stored_password = conn.execute(
            "SELECT setting_value FROM app_settings WHERE setting_key='smtp.password'"
        ).fetchone()[0]
    assert unprotect_secret(stored_password) == "secret"
    if os.name == "nt":
        assert stored_password != "secret"
        assert stored_password.startswith("dpapi:")


def test_prepare_email_document_records_delivery_log(tmp_path: Path, monkeypatch) -> None:
    pdf = tmp_path / "invoice.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    log_service = CommunicationLogService(tmp_path / "communication.db")

    class DisabledService:
        def send_pdf(self, recipient, subject, body, pdf_path):
            return {"ok": False, "code": "smtp_not_enabled", "message": "SMTP disabled."}

    monkeypatch.setattr("services.share_service.open_email_share", lambda recipient, subject, body: "mailto:customer@example.test")
    result = prepare_email_document(
        "customer@example.test",
        "Invoice",
        "Ready",
        pdf,
        delivery_service=DisabledService(),
        log_service=log_service,
    )

    assert result["code"] == "opened"
    rows = log_service.recent_logs()
    assert rows[0]["status"] == "Handed Off"
    assert rows[0]["result_code"] == "opened"
    assert rows[0]["recipient"] == "c***@example.test"
    with sqlite3.connect(log_service.db_path) as conn:
        raw = conn.execute(
            "SELECT recipient,body,attachment_path,metadata_json FROM communication_logs ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert raw[0] == "c***@example.test"
    assert raw[1] == ""
    assert raw[2] == "invoice.pdf"
    assert "customer@example.test" not in raw[3]

    class FailingService:
        def send_pdf(self, recipient, subject, body, pdf_path):
            return {"ok": False, "code": "smtp_failed", "message": "Network unavailable.", "file": str(pdf_path)}

    failed = prepare_email_document(
        "customer@example.test",
        "Invoice",
        "Ready",
        pdf,
        delivery_service=FailingService(),
        log_service=log_service,
    )

    assert failed["code"] == "smtp_failed"
    assert log_service.recent_logs()[0]["status"] == "Failed"
    assert log_service.pending_retries() == []


def test_communication_retry_sends_pending_email(tmp_path: Path) -> None:
    pdf = tmp_path / "invoice.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    service = CommunicationLogService(tmp_path / "communication.db")
    service.ensure_schema()
    with sqlite3.connect(service.db_path) as conn:
        conn.execute(
            """
            INSERT INTO communication_logs(
                channel,recipient,subject,body,attachment_path,status,result_code,
                result_message,attempts,next_retry_at,last_attempt_at,sent_at,
                metadata_json,created_at,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                "email",
                "customer@example.test",
                "Invoice",
                "Ready",
                str(pdf),
                "Failed",
                "smtp_failed",
                "Network unavailable.",
                1,
                "2000-01-01T00:00:00",
                "2000-01-01T00:00:00",
                None,
                "{}",
                "2000-01-01T00:00:00",
                "2000-01-01T00:00:00",
            ),
        )

    class RetryService:
        def __init__(self) -> None:
            self.sent = []

        def send_pdf(self, recipient, subject, body, pdf_path):
            self.sent.append((recipient, subject, body, Path(pdf_path).name))
            return {"ok": True, "code": "smtp_sent", "message": "Email sent.", "file": str(pdf_path)}

    retry_service = RetryService()
    results = service.retry_pending_emails(delivery_service=retry_service, limit=10)

    assert results[0]["code"] == "smtp_sent"
    assert retry_service.sent == [("customer@example.test", "Invoice", "Ready", "invoice.pdf")]
    row = service.recent_logs()[0]
    assert row["status"] == "Sent"
    assert row["attempts"] == 2
    assert row["recipient"] == "c***@example.test"


def test_dashboard_snapshot_includes_communication_status(tmp_path: Path) -> None:
    db_path = tmp_path / "dashboard_communication.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE app_settings(setting_key TEXT PRIMARY KEY, setting_value TEXT, updated_at TEXT)")
        conn.execute(
            "INSERT INTO app_settings(setting_key,setting_value,updated_at) VALUES('email.delivery_mode','smtp',datetime('now'))"
        )
        conn.execute(
            """
            CREATE TABLE communication_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel TEXT,
                recipient TEXT,
                subject TEXT,
                body TEXT,
                attachment_path TEXT,
                status TEXT,
                result_code TEXT,
                result_message TEXT,
                attempts INTEGER,
                next_retry_at TEXT,
                last_attempt_at TEXT,
                sent_at TEXT,
                metadata_json TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO communication_logs(
                channel,recipient,subject,body,attachment_path,status,result_code,
                result_message,attempts,next_retry_at,created_at,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            [
                ("email", "sent@example.test", "Sent", "Body", "sent.pdf", "Sent", "smtp_sent", "Sent", 1, None, date.today().isoformat() + "T09:00:00", date.today().isoformat() + "T09:00:00"),
                ("email", "failed@example.test", "Failed", "Body", "failed.pdf", "Failed", "smtp_failed", "Failed", 1, "2000-01-01T00:00:00", date.today().isoformat() + "T10:00:00", date.today().isoformat() + "T10:00:00"),
            ],
        )

    class LocalSource:
        sqlite_path = db_path

        def rows(self, sql, params=()):
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                return [dict(row) for row in conn.execute(sql.replace("%s", "?"), params).fetchall()]

        def one(self, sql, params=()):
            rows = self.rows(sql, params)
            return rows[0] if rows else None

        def company(self):
            return {}

    snapshot = DashboardService(LocalSource()).snapshot()

    assert snapshot["communication_status"]["items"][0]["value"] == "SMTP"
    assert snapshot["communication_status"]["items"][1]["value"] == "1"
    assert snapshot["communication_status"]["items"][2]["value"] == "1"
    assert snapshot["failed_communications"][0]["recipient"] == "f***@example.test"
    assert any(row["title"] == "Communication Retry" for row in snapshot["critical_alerts"])


def test_communication_templates_seed_render_and_resolve_contacts(tmp_path: Path) -> None:
    service = CommunicationTemplateService(tmp_path / "templates.db")
    service.seed_defaults()

    templates = service.templates()
    assert any(row["template_code"] == "sales_invoice_email" for row in templates)

    template_id = service.save_template(
        {
            "template_code": "custom invoice email",
            "channel": "email",
            "document_type": "sales_invoice",
            "template_name": "Custom Invoice",
            "subject_template": "Invoice {document_no}",
            "body_template": "Dear {party_name}, amount {amount}. Missing {unknown}.",
        }
    )
    assert template_id > 0
    custom = next(row for row in service.templates() if row["template_code"] == "custom_invoice_email")
    rendered = service.render_template(custom, {"document_no": "INV-001", "party_name": "ACME", "amount": "Rs 100"})

    assert rendered["subject"] == "Invoice INV-001"
    assert rendered["body"] == "Dear ACME, amount Rs 100. Missing ."
    assert service.active_template("email", "sales_invoice")["template_code"] == "custom_invoice_email"
    service.save_contact_preference("email", "sales_invoice", "billing_email")
    assert service.contact_preference("email", "sales_invoice") == "billing_email"
    preferred = service.resolve_contact(
        "email",
        {"customer_email": "customer@example.test", "billing_email": "billing@example.test"},
        document_type="sales_invoice",
    )
    assert preferred == {"channel": "email", "field": "billing_email", "value": "billing@example.test"}
    service.save_contact_preference("email", "sales_invoice", "")
    assert service.contact_preference("email", "sales_invoice") == ""
    assert service.resolve_contact("email", {"customer_email": "customer@example.test"})["value"] == "customer@example.test"
    assert service.resolve_contact("whatsapp", {"mobile": "9000000000"})["field"] == "mobile"


def test_share_service_renders_active_communication_template(tmp_path: Path) -> None:
    db_path = tmp_path / "templates.db"
    context = document_message_context(
        title="Tax Invoice",
        document_no="INV-001",
        party_name="ACME",
        amount=1250,
        company={"name": "Demo Company"},
        pdf_path=tmp_path / "invoice.pdf",
    )

    rendered = communication_message(
        channel="email",
        document_type="sales_invoice",
        context=context,
        fallback_subject="Fallback",
        fallback_body="Fallback body",
        db_path=db_path,
    )
    fallback = communication_message(
        channel="email",
        document_type="unknown_document",
        context=context,
        fallback_subject="Fallback",
        fallback_body="Fallback body",
        db_path=db_path,
    )

    assert rendered["template_code"] == "sales_invoice_email"
    assert rendered["subject"] == "Invoice INV-001"
    assert "Dear ACME" in rendered["body"]
    assert fallback == {"subject": "Fallback", "body": "Fallback body", "template_code": ""}


def test_dashboard_snapshot_includes_graph_data() -> None:
    snapshot = DashboardService().snapshot()

    assert len(snapshot["sales_trend"]) == 7
    assert {point["label"] for point in snapshot["sales_trend"]}
    assert [segment["label"] for segment in snapshot["business_mix"]] == [
        "Sales",
        "Purchase",
        "Receivable",
        "Payable",
    ]


def test_company_profile_preserves_client_logo_path(tmp_path: Path) -> None:
    db_path = _copy_db(tmp_path)
    service = CompanyProfileService(db_path)
    profile = service.current_profile()
    service.save_profile(
        {
            "company_id": profile.get("company_id"),
            "license_id": profile.get("license_id"),
            "dev_company_id": profile.get("dev_company_id"),
            "company_name": profile.get("company_name") or "Logo Test Company",
            "business_type_code": profile.get("business_type_code") or "distributor_wholesale",
            "logo_path": "uploads/client_logo_test.png",
        }
    )

    assert service.current_profile()["logo_path"] == "uploads/client_logo_test.png"
