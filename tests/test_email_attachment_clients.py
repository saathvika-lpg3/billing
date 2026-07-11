from __future__ import annotations

from pathlib import Path

from services.email_service import (
    EmailDeliveryService,
    SmtpEmailConfig,
    open_mapi_email_with_attachment,
    open_outlook_email_with_attachment,
)
from services.share_service import prepare_email_document


class _Attachments:
    def __init__(self) -> None:
        self.paths: list[str] = []

    def Add(self, path: str) -> None:  # noqa: N802 - Outlook COM API
        self.paths.append(path)


class _Draft:
    def __init__(self) -> None:
        self.To = ""
        self.Subject = ""
        self.Body = ""
        self.Attachments = _Attachments()
        self.displayed = False

    def Display(self, _modal: bool) -> None:  # noqa: N802 - Outlook COM API
        self.displayed = True


def test_outlook_handoff_attaches_actual_pdf(tmp_path: Path) -> None:
    pdf = tmp_path / "invoice.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    draft = _Draft()

    class Outlook:
        def CreateItem(self, item_type: int):  # noqa: N802 - Outlook COM API
            assert item_type == 0
            return draft

    result = open_outlook_email_with_attachment(
        "buyer@example.test",
        "Invoice",
        "Attached invoice",
        pdf,
        dispatch_factory=lambda name: Outlook() if name == "Outlook.Application" else None,
    )

    assert result["code"] == "outlook_draft"
    assert result["attached"] is True
    assert draft.To == "buyer@example.test"
    assert draft.Subject == "Invoice"
    assert draft.Attachments.paths == [str(pdf.resolve())]
    assert draft.displayed is True


def test_simple_mapi_handoff_passes_actual_pdf(tmp_path: Path) -> None:
    pdf = tmp_path / "statement.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    received = []

    def fake_send(recipient: str, subject: str, body: str, path: Path) -> int:
        received.append((recipient, subject, body, path))
        return 0

    result = open_mapi_email_with_attachment(
        "accounts@example.test",
        "Statement",
        "Please review",
        pdf,
        send_mail=fake_send,
    )
    assert result["code"] == "mapi_completed"
    assert result["attached"] is True
    assert received == [("accounts@example.test", "Statement", "Please review", pdf.resolve())]


def test_handoff_mode_prefers_attachment_capable_client(tmp_path: Path, monkeypatch) -> None:
    pdf = tmp_path / "report.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    service = EmailDeliveryService(SmtpEmailConfig(delivery_mode="handoff"))
    monkeypatch.setattr(
        "services.share_service.open_outlook_email_with_attachment",
        lambda *args, **kwargs: {
            "ok": True,
            "code": "outlook_draft",
            "message": "attached",
            "file": str(pdf),
            "attached": True,
        },
    )
    monkeypatch.setattr(
        "services.share_service.open_email_share",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("mailto should not be used")),
    )
    result = prepare_email_document(
        "buyer@example.test",
        "Report",
        "Ready",
        pdf,
        delivery_service=service,
    )
    assert result["code"] == "outlook_draft"
    assert result["attached"] is True


def test_outlook_mode_falls_back_to_windows_mapi_attachment(tmp_path: Path, monkeypatch) -> None:
    pdf = tmp_path / "outlook-fallback.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    service = EmailDeliveryService(SmtpEmailConfig(delivery_mode="outlook"))
    monkeypatch.setattr(
        "services.share_service.open_outlook_email_with_attachment",
        lambda *args, **kwargs: {"ok": False, "code": "outlook_unavailable", "message": "not installed"},
    )
    monkeypatch.setattr(
        "services.share_service.open_mapi_email_with_attachment",
        lambda *args, **kwargs: {
            "ok": True,
            "code": "mapi_completed",
            "message": "attached",
            "file": str(pdf),
            "attached": True,
        },
    )
    result = prepare_email_document("buyer@example.test", "Invoice", "Ready", pdf, delivery_service=service)
    assert result["code"] == "mapi_completed"
    assert result["attached"] is True


def test_mailto_mode_is_explicit_about_protocol_attachment_limit(tmp_path: Path, monkeypatch) -> None:
    pdf = tmp_path / "voucher.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    service = EmailDeliveryService(SmtpEmailConfig(delivery_mode="mailto"))
    monkeypatch.setattr("services.share_service.open_email_share", lambda *args: "mailto:buyer@example.test")
    result = prepare_email_document(
        "buyer@example.test",
        "Voucher",
        "Ready",
        pdf,
        delivery_service=service,
    )
    assert result["code"] == "opened"
    assert result["attached"] is False
    assert result["manual_attachment_required"] is True


def test_runtime_share_engine_has_no_powershell_or_ps1_helper() -> None:
    source = (Path(__file__).resolve().parents[1] / "services" / "share_service.py").read_text(encoding="utf-8")
    assert "powershell" not in source.casefold()
    assert ".ps1" not in source.casefold()
