from __future__ import annotations

import base64
import re
import os
import subprocess
import tempfile
import webbrowser
from pathlib import Path
from urllib.parse import quote

from services.communication_log_service import CommunicationLogService
from services.communication_template_service import CommunicationTemplateService
from services.email_service import EmailDeliveryService


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
    body = f"{message or ''}\n\nPDF: {file_path}".strip()
    service = delivery_service or EmailDeliveryService.from_environment(db_path)
    smtp_result = service.send_pdf(recipient, subject, body, file_path)
    if smtp_result.get("code") != "smtp_not_enabled":
        _log_email_result(log_service, db_path, recipient, subject, body, file_path, smtp_result)
        return smtp_result
    try:
        url = open_email_share(recipient, subject, body)
    except Exception as exc:
        result = {"ok": False, "code": "open_failed", "message": str(exc), "file": str(file_path)}
        _log_email_result(log_service, db_path, recipient, subject, body, file_path, result)
        return result
    if not str(recipient or "").strip():
        result = {
            "ok": True,
            "code": "missing_recipient",
            "message": "Email draft opened. Add the recipient and attach/send the PDF from the shown path.",
            "url": url,
            "file": str(file_path),
        }
        _log_email_result(log_service, db_path, recipient, subject, body, file_path, result)
        return result
    result = {
        "ok": True,
        "code": "opened",
        "message": "Email draft opened. Attach/send the PDF from the shown path if your mail client does not attach files automatically.",
        "url": url,
        "file": str(file_path),
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
    """Open WhatsApp Web and paste the PDF into the active chat when Windows allows it."""
    file_path = Path(pdf_path)
    if os.name != "nt":
        return {"ok": False, "code": "unsupported_os", "message": "Automatic PDF attachment is available only on Windows."}
    if not file_path.exists() or file_path.suffix.lower() != ".pdf":
        return {"ok": False, "code": "missing_pdf", "message": "PDF attachment file is not ready."}
    digits = normalize_phone(phone)
    if not digits:
        return {"ok": False, "code": "missing_phone", "message": "Customer WhatsApp number is missing."}

    powershell = Path(r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe")
    ps_exe = str(powershell) if powershell.exists() else "powershell.exe"
    script = _whatsapp_attach_script()
    replacements = {
        "__PHONE64__": _b64(digits),
        "__FILE64__": _b64(str(file_path.resolve())),
        "__CAPTION64__": _b64(message or ""),
    }
    for marker, value in replacements.items():
        script = script.replace(marker, value)

    tmp_name = ""
    try:
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".ps1", encoding="utf-8-sig") as handle:
            handle.write(script)
            tmp_name = handle.name
        completed = subprocess.run(
            [ps_exe, "-NoProfile", "-STA", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", tmp_name],
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "code": "timeout", "message": "WhatsApp attachment is taking too long. WhatsApp may still be loading; try again after login."}
    except OSError as exc:
        return {"ok": False, "code": "helper_start_failed", "message": f"Local WhatsApp attachment helper could not start: {exc}"}
    finally:
        if tmp_name:
            try:
                Path(tmp_name).unlink(missing_ok=True)
            except OSError:
                pass

    details = " ".join(part.strip() for part in [completed.stdout, completed.stderr] if part and part.strip())
    if completed.returncode == 0:
        return {
            "ok": True,
            "code": "attached",
            "message": details or "PDF is ready in WhatsApp. Press Send in WhatsApp, then return to PRM.",
            "file": str(file_path),
        }
    return {
        "ok": False,
        "code": "attach_failed",
        "message": f"Automatic PDF attachment failed{': ' + details if details else '.'}",
        "file": str(file_path),
    }


def pdf_share_note(path: Path) -> str:
    return (
        "WhatsApp is opened with the message ready. "
        f"The PDF attachment is ready here: {path}"
    )


def _b64(value: str) -> str:
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def _whatsapp_attach_script() -> str:
    return r'''
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class PrmWin32 {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
  [DllImport("user32.dll")] public static extern void mouse_event(uint flags, uint dx, uint dy, uint data, UIntPtr extraInfo);
  public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
}
'@
$utf8 = [System.Text.Encoding]::UTF8
$phone = $utf8.GetString([System.Convert]::FromBase64String('__PHONE64__'))
$file = $utf8.GetString([System.Convert]::FromBase64String('__FILE64__'))
$caption = $utf8.GetString([System.Convert]::FromBase64String('__CAPTION64__'))
if ($phone -notmatch '^\d{10,15}$') { throw 'Invalid WhatsApp phone number.' }
if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw 'PDF file was not found.' }
$pdfPath = (Resolve-Path -LiteralPath $file).Path
$url = 'https://web.whatsapp.com/send?phone=' + [System.Uri]::EscapeDataString($phone)
Start-Process $url | Out-Null
Start-Sleep -Milliseconds 9000
$shell = New-Object -ComObject WScript.Shell
for ($i = 0; $i -lt 12; $i++) {
    if ($shell.AppActivate('WhatsApp')) { break }
    if ($shell.AppActivate('Google Chrome')) { break }
    if ($shell.AppActivate('Microsoft Edge')) { break }
    Start-Sleep -Milliseconds 500
}
Start-Sleep -Milliseconds 1200
$browser = Get-Process msedge,chrome -ErrorAction SilentlyContinue |
    Where-Object { $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -match 'WhatsApp|web\.whatsapp|Microsoft Edge|Google Chrome' } |
    Sort-Object StartTime -Descending |
    Select-Object -First 1
if ($browser) {
    [void][PrmWin32]::SetForegroundWindow($browser.MainWindowHandle)
    Start-Sleep -Milliseconds 700
    $rect = New-Object PrmWin32+RECT
    if ([PrmWin32]::GetWindowRect($browser.MainWindowHandle, [ref]$rect)) {
        $x = [Math]::Max($rect.Left + 120, [Math]::Min($rect.Right - 120, [int]($rect.Left + (($rect.Right - $rect.Left) * 0.72))))
        $y = [Math]::Max($rect.Top + 120, [Math]::Min($rect.Bottom - 35, [int]($rect.Bottom - 48)))
        [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point($x, $y)
        [PrmWin32]::mouse_event(0x0002, 0, 0, 0, [UIntPtr]::Zero)
        Start-Sleep -Milliseconds 80
        [PrmWin32]::mouse_event(0x0004, 0, 0, 0, [UIntPtr]::Zero)
    }
}
Start-Sleep -Milliseconds 900
$files = New-Object System.Collections.Specialized.StringCollection
[void]$files.Add($pdfPath)
[System.Windows.Forms.Clipboard]::SetFileDropList($files)
[System.Windows.Forms.SendKeys]::SendWait('^v')
Start-Sleep -Milliseconds 4200
if ($caption.Trim().Length -gt 0) {
    [System.Windows.Forms.Clipboard]::SetText($caption)
    [System.Windows.Forms.SendKeys]::SendWait('^v')
}
Write-Output 'PDF is ready in WhatsApp. Press Send in WhatsApp.'
'''
