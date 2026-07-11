from __future__ import annotations

import ctypes
import re
import os
import struct
import subprocess
import time
import webbrowser
from pathlib import Path
from urllib.parse import quote

from services.communication_log_service import CommunicationLogService
from services.communication_template_service import CommunicationTemplateService
from services.email_service import (
    EmailDeliveryService,
    open_mapi_email_with_attachment,
    open_outlook_email_with_attachment,
)


def normalize_phone(value: object) -> str:
    digits = re.sub(r"\D+", "", str(value or ""))
    if len(digits) == 10:
        return "91" + digits
    return digits


def whatsapp_url(phone: object, message: str) -> str:
    digits = normalize_phone(phone)
    text = quote(message or "")
    if digits:
        return f"https://web.whatsapp.com/send?phone={digits}&text={text}"
    return f"https://web.whatsapp.com/send?text={text}"


def whatsapp_native_url(phone: object, message: str) -> str:
    digits = normalize_phone(phone)
    text = quote(message or "")
    if digits:
        return f"whatsapp://send?phone={digits}&text={text}"
    return f"whatsapp://send?text={text}"


def whatsapp_readiness(phone: object, message: str = "PRM test message") -> dict[str, object]:
    digits = normalize_phone(phone)
    if not digits:
        return {"ok": False, "code": "missing_phone", "message": "WhatsApp number is missing."}
    if len(digits) < 10 or len(digits) > 15:
        return {"ok": False, "code": "invalid_phone", "message": "WhatsApp number should contain 10 to 15 digits."}
    return {
        "ok": True,
        "code": "link_ready",
        "message": "WhatsApp link is ready. Browser login/attachment acceptance must be checked on this workstation.",
        "phone": digits,
        "web_url": whatsapp_url(digits, message),
        "native_url": whatsapp_native_url(digits, message),
    }


def open_whatsapp_share(phone: object, message: str) -> str:
    web_url = whatsapp_url(phone, message)
    urls = [web_url]
    if os.name == "nt":
        urls.insert(0, whatsapp_native_url(phone, message))

    errors: list[str] = []
    for url in urls:
        if os.name == "nt":
            try:
                os.startfile(url)
                return url
            except OSError as exc:
                errors.append(str(exc))
        try:
            if webbrowser.open(url, new=2, autoraise=True):
                return url
        except Exception as exc:
            errors.append(str(exc))

    if os.name == "nt":
        try:
            subprocess.Popen(
                ["cmd", "/c", "start", "", web_url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return web_url
        except OSError as exc:
            errors.append(str(exc))
    details = "; ".join(error for error in errors if error)
    raise RuntimeError(f"WhatsApp link could not be opened. {details}".strip())


def email_url(recipient: object, subject: str, body: str) -> str:
    address = str(recipient or "").strip()
    query = f"subject={quote(subject or '')}&body={quote(body or '')}"
    return f"mailto:{quote(address)}?{query}"


def open_email_share(recipient: object, subject: str, body: str) -> str:
    url = email_url(recipient, subject, body)
    errors: list[str] = []
    if os.name == "nt":
        try:
            os.startfile(url)
            return url
        except OSError as exc:
            errors.append(str(exc))
    try:
        if webbrowser.open(url, new=1, autoraise=True):
            return url
    except Exception as exc:
        errors.append(str(exc))
    if os.name == "nt":
        try:
            subprocess.Popen(
                ["cmd", "/c", "start", "", url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return url
        except OSError as exc:
            errors.append(str(exc))
    details = "; ".join(error for error in errors if error)
    raise RuntimeError(f"Email client could not be opened. {details}".strip())


def prepare_email_document(
    recipient: object,
    subject: str,
    message: str,
    pdf_path: Path,
    *,
    delivery_service: EmailDeliveryService | None = None,
    db_path: str | Path | None = None,
    log_service: CommunicationLogService | None = None,
) -> dict[str, object]:
    file_path = Path(pdf_path)
    if not file_path.exists() or file_path.suffix.lower() != ".pdf":
        result = {"ok": False, "code": "missing_pdf", "message": "PDF attachment file is not ready."}
        _log_email_result(log_service, db_path, recipient, subject, message, file_path, result)
        return result
    body = str(message or "").strip()
    service = delivery_service or EmailDeliveryService.from_environment(db_path)
    smtp_result = service.send_pdf(recipient, subject, body, file_path)
    if smtp_result.get("code") != "smtp_not_enabled":
        _log_email_result(log_service, db_path, recipient, subject, body, file_path, smtp_result)
        return smtp_result
    delivery_mode = str(getattr(getattr(service, "config", None), "delivery_mode", "") or "").strip().lower()
    if delivery_mode in {"handoff", "auto", "outlook", "mapi"}:
        attachment_attempts = []
        if delivery_mode in {"handoff", "auto", "outlook"}:
            attachment_attempts.append(open_outlook_email_with_attachment(recipient, subject, body, file_path))
        if delivery_mode in {"handoff", "auto", "outlook", "mapi"} and not any(result.get("ok") for result in attachment_attempts):
            attachment_attempts.append(open_mapi_email_with_attachment(recipient, subject, body, file_path))
        attached = next((result for result in attachment_attempts if result.get("ok")), None)
        if attached:
            _log_email_result(log_service, db_path, recipient, subject, body, file_path, attached)
            return attached
    mailto_body = f"{body}\n\nAttachment path (mailto cannot attach files): {file_path}".strip()
    try:
        url = open_email_share(recipient, subject, mailto_body)
    except Exception as exc:
        result = {"ok": False, "code": "open_failed", "message": str(exc), "file": str(file_path)}
        _log_email_result(log_service, db_path, recipient, subject, body, file_path, result)
        return result
    if not str(recipient or "").strip():
        result = {
            "ok": True,
            "code": "missing_recipient",
            "message": "Email draft opened. Add the recipient and attach the PDF from the shown path; mailto cannot attach files.",
            "url": url,
            "file": str(file_path),
        }
        _log_email_result(log_service, db_path, recipient, subject, body, file_path, result)
        return result
    result = {
        "ok": True,
        "code": "opened",
        "message": "Mailto draft opened. Attach the PDF from the shown path; the mailto protocol cannot carry attachments.",
        "url": url,
        "file": str(file_path),
        "attached": False,
        "manual_attachment_required": True,
    }
    _log_email_result(log_service, db_path, recipient, subject, body, file_path, result)
    return result


def communication_message(
    *,
    channel: str,
    document_type: str,
    context: dict[str, object],
    fallback_subject: str,
    fallback_body: str,
    db_path: str | Path | None = None,
) -> dict[str, str]:
    try:
        return CommunicationTemplateService(db_path).render_for_document(
            channel=channel,
            document_type=document_type,
            context=context,
            fallback_subject=fallback_subject,
            fallback_body=fallback_body,
        )
    except Exception:
        return {"subject": fallback_subject, "body": fallback_body, "template_code": ""}


def document_message_context(
    *,
    title: str,
    document_no: object,
    party_name: object,
    amount: object,
    company: dict[str, object],
    pdf_path: Path | None = None,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    context: dict[str, object] = {
        "title": title,
        "document_no": document_no,
        "doc_no": document_no,
        "party_name": party_name,
        "amount": _money_text(amount),
        "raw_amount": amount,
        "company_name": company.get("name") or company.get("business_name") or "PRM Billing Inventory",
        "company_phone": company.get("phone") or "",
        "company_email": company.get("email") or "",
        "pdf_path": str(pdf_path or ""),
    }
    if extra:
        context.update(extra)
    return context


def _money_text(value: object) -> str:
    try:
        return f"Rs {float(value or 0):,.2f}"
    except (TypeError, ValueError):
        return "Rs 0.00"


def _log_email_result(
    log_service: CommunicationLogService | None,
    db_path: str | Path | None,
    recipient: object,
    subject: str,
    body: str,
    attachment_path: Path,
    result: dict[str, object],
) -> None:
    service = log_service or (CommunicationLogService(db_path) if db_path else None)
    if service is None:
        return
    try:
        service.log_result(
            channel="email",
            recipient=recipient,
            subject=subject,
            body=body,
            attachment_path=attachment_path,
            result=result,
        )
    except Exception:
        pass


def prepare_whatsapp_document(phone: object, message: str, pdf_path: Path, *, timeout: int = 90) -> dict[str, object]:
    """Open WhatsApp and paste a PDF using native Windows clipboard APIs."""
    file_path = Path(pdf_path)
    if os.name != "nt":
        return {"ok": False, "code": "unsupported_os", "message": "Automatic PDF attachment is available only on Windows."}
    if not file_path.exists() or file_path.suffix.lower() != ".pdf":
        return {"ok": False, "code": "missing_pdf", "message": "PDF attachment file is not ready."}
    digits = normalize_phone(phone)
    if not digits:
        return {"ok": False, "code": "missing_phone", "message": "Customer WhatsApp number is missing."}
    try:
        open_whatsapp_share(digits, "")
        _set_windows_file_clipboard(file_path.resolve())
    except Exception as exc:
        return {
            "ok": False,
            "code": "helper_start_failed",
            "message": f"WhatsApp attachment could not be prepared: {exc}",
            "file": str(file_path),
        }

    window = _wait_for_whatsapp_window(min(max(int(timeout), 1), 20))
    if not window:
        return {
            "ok": True,
            "code": "clipboard_ready",
            "message": "WhatsApp opened and the PDF is on the clipboard. Select the chat and press Ctrl+V, then Send.",
            "file": str(file_path),
        }
    try:
        ctypes.windll.user32.SetForegroundWindow.argtypes = [ctypes.c_void_p]
        ctypes.windll.user32.SetForegroundWindow(ctypes.c_void_p(window))
        time.sleep(0.5)
        _send_ctrl_v()
        if str(message or "").strip():
            time.sleep(2.5)
            _set_windows_text_clipboard(str(message).strip())
            _send_ctrl_v()
    except Exception as exc:
        return {
            "ok": True,
            "code": "clipboard_ready",
            "message": f"PDF is on the clipboard. Press Ctrl+V in WhatsApp, then Send. ({exc})",
            "file": str(file_path),
        }
    return {
        "ok": True,
        "code": "attached",
        "message": "PDF is ready in WhatsApp. Press Send in WhatsApp, then return to PRM.",
        "file": str(file_path),
    }


def pdf_share_note(path: Path) -> str:
    return (
        "WhatsApp is opened with the message ready. "
        f"The PDF attachment is ready here: {path}"
    )


def _set_windows_file_clipboard(path: Path) -> None:
    # DROPFILES followed by a UTF-16 double-null-terminated path list.
    payload = struct.pack("<IiiII", 20, 0, 0, 0, 1) + (str(path) + "\0\0").encode("utf-16le")
    _set_windows_clipboard_data(15, payload)


def _set_windows_text_clipboard(value: str) -> None:
    _set_windows_clipboard_data(13, (value + "\0").encode("utf-16le"))


def _set_windows_clipboard_data(format_id: int, payload: bytes) -> None:
    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32
    kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
    user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p
    handle = kernel32.GlobalAlloc(0x0002, len(payload))
    if not handle:
        raise ctypes.WinError()
    pointer = kernel32.GlobalLock(handle)
    if not pointer:
        kernel32.GlobalFree(handle)
        raise ctypes.WinError()
    ctypes.memmove(pointer, payload, len(payload))
    kernel32.GlobalUnlock(handle)
    if not user32.OpenClipboard(None):
        kernel32.GlobalFree(handle)
        raise ctypes.WinError()
    transferred = False
    try:
        user32.EmptyClipboard()
        if not user32.SetClipboardData(format_id, handle):
            raise ctypes.WinError()
        transferred = True
    finally:
        user32.CloseClipboard()
        if not transferred:
            kernel32.GlobalFree(handle)


def _wait_for_whatsapp_window(timeout: int) -> int:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        found = _find_whatsapp_window()
        if found:
            return found
        time.sleep(0.5)
    return 0


def _find_whatsapp_window() -> int:
    user32 = ctypes.windll.user32
    matches: list[int] = []
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.IsWindowVisible.argtypes = [ctypes.c_void_p]
    user32.GetWindowTextLengthW.argtypes = [ctypes.c_void_p]
    user32.GetWindowTextW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int]
    user32.EnumWindows.argtypes = [callback_type, ctypes.c_void_p]

    @callback_type
    def visit(hwnd: int, _lparam: int) -> bool:
        handle = ctypes.c_void_p(hwnd)
        if not user32.IsWindowVisible(handle):
            return True
        length = user32.GetWindowTextLengthW(handle)
        if length <= 0:
            return True
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(handle, buffer, length + 1)
        if "whatsapp" in buffer.value.casefold():
            matches.append(int(hwnd))
        return True

    user32.EnumWindows(visit, 0)
    return matches[0] if matches else 0


def _send_ctrl_v() -> None:
    user32 = ctypes.windll.user32
    user32.keybd_event(0x11, 0, 0, 0)
    user32.keybd_event(0x56, 0, 0, 0)
    user32.keybd_event(0x56, 0, 0x0002, 0)
    user32.keybd_event(0x11, 0, 0x0002, 0)
