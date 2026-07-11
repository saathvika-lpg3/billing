from __future__ import annotations

import mimetypes
import os
import base64
import ctypes
import smtplib
import sqlite3
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Mapping


SMTP_SETTING_KEYS = {
    "email.delivery_mode": "PRM_EMAIL_DELIVERY_MODE",
    "smtp.host": "PRM_SMTP_HOST",
    "smtp.port": "PRM_SMTP_PORT",
    "smtp.username": "PRM_SMTP_USERNAME",
    "smtp.password": "PRM_SMTP_PASSWORD",
    "smtp.from_email": "PRM_SMTP_FROM",
    "smtp.use_tls": "PRM_SMTP_USE_TLS",
    "smtp.use_ssl": "PRM_SMTP_USE_SSL",
    "smtp.timeout": "PRM_SMTP_TIMEOUT",
}

SECRET_DPAPI_PREFIX = "dpapi:"


def _env_bool(value: object, default: bool) -> bool:
    text = str(value if value is not None else "").strip().lower()
    if not text:
        return default
    return text not in {"0", "false", "no", "off"}


def protect_secret(value: object) -> str:
    text = str(value or "")
    if not text or text.startswith(SECRET_DPAPI_PREFIX):
        return text
    if os.name != "nt":
        return text
    try:
        protected = _dpapi_protect(text.encode("utf-8"))
    except Exception:
        return text
    return SECRET_DPAPI_PREFIX + base64.b64encode(protected).decode("ascii")


def unprotect_secret(value: object) -> str:
    text = str(value or "")
    if not text.startswith(SECRET_DPAPI_PREFIX):
        return text
    if os.name != "nt":
        return ""
    try:
        raw = base64.b64decode(text[len(SECRET_DPAPI_PREFIX) :])
        return _dpapi_unprotect(raw).decode("utf-8")
    except Exception:
        return ""


@dataclass(frozen=True)
class SmtpEmailConfig:
    delivery_mode: str = "handoff"
    host: str = ""
    port: int = 587
    username: str = ""
    password: str = ""
    from_email: str = ""
    use_tls: bool = True
    use_ssl: bool = False
    timeout: float = 20.0

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "SmtpEmailConfig":
        source = os.environ if env is None else env
        username = str(source.get("PRM_SMTP_USERNAME") or "").strip()
        from_email = str(source.get("PRM_SMTP_FROM") or username).strip()
        try:
            port = int(source.get("PRM_SMTP_PORT") or 587)
        except ValueError:
            port = 587
        try:
            timeout = float(source.get("PRM_SMTP_TIMEOUT") or 20)
        except ValueError:
            timeout = 20.0
        return cls(
            delivery_mode=str(source.get("PRM_EMAIL_DELIVERY_MODE") or "handoff").strip().lower(),
            host=str(source.get("PRM_SMTP_HOST") or "").strip(),
            port=port,
            username=username,
            password=str(source.get("PRM_SMTP_PASSWORD") or ""),
            from_email=from_email,
            use_tls=_env_bool(source.get("PRM_SMTP_USE_TLS"), True),
            use_ssl=_env_bool(source.get("PRM_SMTP_USE_SSL"), False),
            timeout=timeout,
        )

    @classmethod
    def from_sources(
        cls,
        *,
        env: Mapping[str, str] | None = None,
        db_path: str | Path | None = None,
    ) -> "SmtpEmailConfig":
        source = os.environ if env is None else env
        merged = _settings_env(db_path)
        for key in set(SMTP_SETTING_KEYS.values()):
            value = source.get(key)
            if value is not None and str(value).strip() != "":
                merged[key] = str(value)
        return cls.from_env(merged)

    @property
    def smtp_enabled(self) -> bool:
        return self.delivery_mode == "smtp"

    @property
    def smtp_ready(self) -> bool:
        return bool(self.smtp_enabled and self.host and self.from_email)


class EmailDeliveryService:
    def __init__(
        self,
        config: SmtpEmailConfig | None = None,
        *,
        smtp_factory: Any | None = None,
        smtp_ssl_factory: Any | None = None,
    ) -> None:
        self.config = config or SmtpEmailConfig.from_env()
        self.smtp_factory = smtp_factory or smtplib.SMTP
        self.smtp_ssl_factory = smtp_ssl_factory or smtplib.SMTP_SSL

    @classmethod
    def from_environment(cls, db_path: str | Path | None = None) -> "EmailDeliveryService":
        return cls(SmtpEmailConfig.from_sources(db_path=db_path))

    def send_pdf(self, recipient: object, subject: str, body: str, pdf_path: Path) -> dict[str, object]:
        file_path = Path(pdf_path)
        if not self.config.smtp_enabled:
            return {"ok": False, "code": "smtp_not_enabled", "message": "SMTP email delivery is not enabled."}
        if not self.config.smtp_ready:
            return {
                "ok": False,
                "code": "smtp_not_configured",
                "message": "SMTP email delivery is enabled but host/from address is not configured.",
            }
        to_address = str(recipient or "").strip()
        if not to_address:
            return {"ok": False, "code": "missing_recipient", "message": "Email recipient is missing."}
        if not file_path.exists() or file_path.suffix.lower() != ".pdf":
            return {"ok": False, "code": "missing_pdf", "message": "PDF attachment file is not ready."}
        message = self._build_message(to_address, subject, body, file_path)
        try:
            self._send_message(message)
        except Exception as exc:
            return {"ok": False, "code": "smtp_failed", "message": f"SMTP email could not be sent: {exc}", "file": str(file_path)}
        return {"ok": True, "code": "smtp_sent", "message": "Email sent successfully.", "file": str(file_path)}

    def test_connection(self) -> dict[str, object]:
        if not self.config.smtp_enabled:
            return {"ok": False, "code": "smtp_not_enabled", "message": "SMTP email delivery is not enabled."}
        if not self.config.smtp_ready:
            return {
                "ok": False,
                "code": "smtp_not_configured",
                "message": "SMTP email delivery is enabled but host/from address is not configured.",
            }
        try:
            self._with_smtp(lambda smtp: None)
        except Exception as exc:
            return {"ok": False, "code": "smtp_failed", "message": f"SMTP connection/authentication failed: {exc}"}
        return {"ok": True, "code": "smtp_ready", "message": "SMTP connection and authentication succeeded."}

    def _build_message(self, recipient: str, subject: str, body: str, pdf_path: Path) -> EmailMessage:
        message = EmailMessage()
        message["From"] = self.config.from_email
        message["To"] = recipient
        message["Subject"] = subject or "PRM document"
        message.set_content(body or "")
        content_type, _ = mimetypes.guess_type(str(pdf_path))
        maintype, subtype = (content_type or "application/pdf").split("/", 1)
        message.add_attachment(
            pdf_path.read_bytes(),
            maintype=maintype,
            subtype=subtype,
            filename=pdf_path.name,
        )
        return message

    def _send_message(self, message: EmailMessage) -> None:
        self._with_smtp(lambda smtp: smtp.send_message(message))

    def _with_smtp(self, action: Any) -> None:
        factory = self.smtp_ssl_factory if self.config.use_ssl else self.smtp_factory
        with factory(self.config.host, self.config.port, timeout=self.config.timeout) as smtp:
            if self.config.use_tls and not self.config.use_ssl:
                smtp.starttls()
            if self.config.username:
                smtp.login(self.config.username, self.config.password)
            action(smtp)


def open_outlook_email_with_attachment(
    recipient: object,
    subject: str,
    body: str,
    pdf_path: Path,
    *,
    dispatch_factory: Any | None = None,
) -> dict[str, object]:
    """Open an Outlook compose window with the PDF already attached."""

    file_path = Path(pdf_path).resolve()
    if not file_path.is_file():
        return {"ok": False, "code": "missing_pdf", "message": "PDF attachment file is not ready."}
    try:
        if dispatch_factory is None:
            from win32com.client import Dispatch  # type: ignore[import-not-found]

            dispatch_factory = Dispatch
        outlook = dispatch_factory("Outlook.Application")
        draft = outlook.CreateItem(0)
        draft.To = str(recipient or "").strip()
        draft.Subject = subject or "PRM document"
        draft.Body = body or ""
        draft.Attachments.Add(str(file_path))
        draft.Display(False)
    except Exception as exc:
        return {
            "ok": False,
            "code": "outlook_unavailable",
            "message": f"Outlook attachment handoff is unavailable: {exc}",
            "file": str(file_path),
        }
    return {
        "ok": True,
        "code": "outlook_draft",
        "message": "Outlook draft opened with the PDF attached.",
        "file": str(file_path),
        "attached": True,
    }


def open_mapi_email_with_attachment(
    recipient: object,
    subject: str,
    body: str,
    pdf_path: Path,
    *,
    send_mail: Any | None = None,
) -> dict[str, object]:
    """Use Windows Simple MAPI so the default compatible mail client receives an attachment."""

    file_path = Path(pdf_path).resolve()
    if not file_path.is_file():
        return {"ok": False, "code": "missing_pdf", "message": "PDF attachment file is not ready."}
    try:
        if send_mail is not None:
            result_code = int(send_mail(str(recipient or ""), subject, body, file_path))
        else:
            if os.name != "nt":
                raise RuntimeError("Simple MAPI is available only on Windows.")
            result_code = _mapi_send_mail(str(recipient or ""), subject, body, file_path)
    except Exception as exc:
        return {
            "ok": False,
            "code": "mapi_unavailable",
            "message": f"Default mail-client attachment handoff is unavailable: {exc}",
            "file": str(file_path),
        }
    if result_code == 0:
        return {
            "ok": True,
            "code": "mapi_completed",
            "message": "Default mail client opened with the PDF attached.",
            "file": str(file_path),
            "attached": True,
        }
    if result_code == 1:
        return {
            "ok": False,
            "code": "mapi_cancelled",
            "message": "Email composition was cancelled in the default mail client.",
            "file": str(file_path),
        }
    return {
        "ok": False,
        "code": "mapi_failed",
        "message": f"Default mail client returned MAPI error {result_code}.",
        "file": str(file_path),
    }


def _mapi_send_mail(recipient: str, subject: str, body: str, pdf_path: Path) -> int:
    class MapiRecipDescW(ctypes.Structure):
        _fields_ = [
            ("ulReserved", ctypes.c_ulong),
            ("ulRecipClass", ctypes.c_ulong),
            ("lpszName", ctypes.c_wchar_p),
            ("lpszAddress", ctypes.c_wchar_p),
            ("ulEIDSize", ctypes.c_ulong),
            ("lpEntryID", ctypes.c_void_p),
        ]

    class MapiFileDescW(ctypes.Structure):
        _fields_ = [
            ("ulReserved", ctypes.c_ulong),
            ("flFlags", ctypes.c_ulong),
            ("nPosition", ctypes.c_ulong),
            ("lpszPathName", ctypes.c_wchar_p),
            ("lpszFileName", ctypes.c_wchar_p),
            ("lpFileType", ctypes.c_void_p),
        ]

    class MapiMessageW(ctypes.Structure):
        _fields_ = [
            ("ulReserved", ctypes.c_ulong),
            ("lpszSubject", ctypes.c_wchar_p),
            ("lpszNoteText", ctypes.c_wchar_p),
            ("lpszMessageType", ctypes.c_wchar_p),
            ("lpszDateReceived", ctypes.c_wchar_p),
            ("lpszConversationID", ctypes.c_wchar_p),
            ("flFlags", ctypes.c_ulong),
            ("lpOriginator", ctypes.c_void_p),
            ("nRecipCount", ctypes.c_ulong),
            ("lpRecips", ctypes.POINTER(MapiRecipDescW)),
            ("nFileCount", ctypes.c_ulong),
            ("lpFiles", ctypes.POINTER(MapiFileDescW)),
        ]

    address = recipient.strip()
    recip = MapiRecipDescW(0, 1, address or None, f"SMTP:{address}" if address else None, 0, None)
    attachment = MapiFileDescW(0, 0, 0xFFFFFFFF, str(pdf_path), pdf_path.name, None)
    message = MapiMessageW(
        0,
        subject or "PRM document",
        body or "",
        None,
        None,
        None,
        0,
        None,
        1 if address else 0,
        ctypes.pointer(recip) if address else None,
        1,
        ctypes.pointer(attachment),
    )
    send = ctypes.windll.mapi32.MAPISendMailW
    send.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(MapiMessageW), ctypes.c_ulong, ctypes.c_ulong]
    send.restype = ctypes.c_ulong
    return int(send(None, None, ctypes.byref(message), 0x00000009, 0))


def _settings_env(db_path: str | Path | None) -> dict[str, str]:
    if not db_path:
        try:
            from services.mysql_source import MySqlSource

            db_path = MySqlSource().sqlite_path
        except Exception:
            return {}
    path = Path(db_path)
    if not path.exists():
        return {}
    protect_saved_smtp_password(path)
    try:
        placeholders = ",".join("?" for _ in SMTP_SETTING_KEYS)
        query = f"""
            SELECT setting_key, setting_value
            FROM app_settings
            WHERE setting_key IN ({placeholders})
            """
        with sqlite3.connect(path) as conn:
            rows = conn.execute(query, tuple(SMTP_SETTING_KEYS)).fetchall()
    except sqlite3.Error:
        return {}
    env_values: dict[str, str] = {}
    for key, value in rows:
        env_key = SMTP_SETTING_KEYS.get(str(key))
        if env_key and value is not None and str(value).strip() != "":
            env_values[env_key] = unprotect_secret(value) if key == "smtp.password" else str(value)
    return env_values


def protect_saved_smtp_password(db_path: str | Path | None) -> None:
    if not db_path:
        return
    path = Path(db_path)
    if not path.exists():
        return
    try:
        with sqlite3.connect(path) as conn:
            row = conn.execute(
                "SELECT setting_value FROM app_settings WHERE setting_key='smtp.password'"
            ).fetchone()
            if not row:
                return
            current = str(row[0] or "")
            protected = protect_secret(current)
            if protected and protected != current:
                conn.execute(
                    """
                    UPDATE app_settings
                    SET setting_value=?, updated_at=datetime('now')
                    WHERE setting_key='smtp.password'
                    """,
                    (protected,),
                )
    except sqlite3.Error:
        return


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", ctypes.c_ulong), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def _blob_from_bytes(data: bytes) -> tuple[_DataBlob, ctypes.Array[Any]]:
    buffer = ctypes.create_string_buffer(data)
    blob = _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)))
    return blob, buffer


def _dpapi_protect(data: bytes) -> bytes:
    if os.name != "nt":
        raise RuntimeError("DPAPI is only available on Windows.")
    in_blob, _buffer = _blob_from_bytes(data)
    out_blob = _DataBlob()
    if not ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(in_blob),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(out_blob),
    ):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(out_blob.pbData)


def _dpapi_unprotect(data: bytes) -> bytes:
    if os.name != "nt":
        raise RuntimeError("DPAPI is only available on Windows.")
    in_blob, _buffer = _blob_from_bytes(data)
    out_blob = _DataBlob()
    if not ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(in_blob),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(out_blob),
    ):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(out_blob.pbData)
