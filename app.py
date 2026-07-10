from __future__ import annotations

import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox

from config.app_config import AppConfig
from config.qt_fonts import ensure_application_font
from services.license_service import LicenseError, LicenseService
from views.login_dialog import LoginDialog
from views.main_window import MainWindow


def _startup_log_file() -> Path:
    log_dir = Path(__file__).resolve().parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "prm_startup.log"


def _log_startup(step: str, status: str, message: str = "") -> None:
    log_file = _startup_log_file()
    timestamp = datetime.now().isoformat(timespec="seconds")
    text = f"{timestamp} | {step} | {status} | {message}\n"
    try:
        log_file.write_text(text, encoding="utf-8", append=False)
    except TypeError:
        # Python <3.11 fallback
        with open(log_file, "a", encoding="utf-8") as handle:
            handle.write(text)
    except Exception:
        pass


def _append_startup_log(step: str, status: str, message: str = "") -> None:
    log_file = _startup_log_file()
    timestamp = datetime.now().isoformat(timespec="seconds")
    text = f"{timestamp} | {step} | {status} | {message}\n"
    try:
        with open(log_file, "a", encoding="utf-8") as handle:
            handle.write(text)
    except Exception:
        pass


def _log_exception_details(step: str, exc: Exception) -> None:
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    frame = traceback.extract_tb(exc.__traceback__)[-1] if exc.__traceback__ else None
    _append_startup_log(step, "FAILED", f"exception_type={type(exc).__name__} message={exc}")
    if frame is not None:
        _append_startup_log(
            step,
            "TRACEBACK",
            f"filename={frame.filename} class=<unknown> method={frame.name} line={frame.lineno}",
        )
    _append_startup_log(step, "TRACEBACK", tb.rstrip())


def _handle_exception(exc_type, exc_value, exc_traceback) -> None:
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    _append_startup_log("uncaught_exception", "FAIL", tb)
    print(tb, file=sys.stderr)
    try:
        QMessageBox.critical(None, "Application Error", f"An unexpected error occurred:\n{exc_value}\nSee logs for details.")
    except Exception:
        pass


def _handle_thread_exception(args: threading.ExceptHookArgs) -> None:
    tb = "".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback))
    _append_startup_log("thread_exception", "FAIL", tb)
    print(tb, file=sys.stderr)


def _install_global_handlers() -> None:
    sys.excepthook = _handle_exception
    try:
        threading.excepthook = _handle_thread_exception
    except AttributeError:
        pass


def main() -> int:
    _log_startup("app_start", "START", "Application starting")
    _install_global_handlers()
    if getattr(sys, "frozen", False):
        root = Path(sys.executable).resolve().parent
    else:
        root = Path(__file__).resolve().parent
    config = AppConfig(project_root=root, source_root=root)
    start_page = "dashboard"
    if "--page" in sys.argv:
        page_index = sys.argv.index("--page")
        if page_index + 1 < len(sys.argv):
            start_page = sys.argv[page_index + 1]
    _append_startup_log("app_config", "OK", f"project_root={config.project_root}")
    _append_startup_log("app_qapplication", "START", "Creating QApplication")
    try:
        app = QApplication(sys.argv)
        ensure_application_font()
        _append_startup_log("app_qapplication", "SUCCESS", f"instance={type(app).__name__}")
    except Exception as exc:
        _log_exception_details("app_qapplication", exc)
        raise
    app.setApplicationName("PRM Billing Inventory")
    app.setOrganizationName("PRM Software Solutions")
    _append_startup_log("app_icon", "START", "Preparing application icon")
    try:
        icon_path = config.assets_dir / "PRM_SoftSolutions.jpg"
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
            _append_startup_log("app_icon", "SUCCESS", f"icon_path={icon_path}")
        else:
            _append_startup_log("app_icon", "FAILED", f"icon_path_missing={icon_path}")
    except Exception as exc:
        _log_exception_details("app_icon", exc)
        raise
    license_service = LicenseService(config)
    _append_startup_log("license_service", "START", f"db_path={license_service.db_path}")
    _append_startup_log("database_initialization", "START", f"Initializing license database at {license_service.db_path}")
    try:
        license_context = license_service.require_license()
        _append_startup_log("license_validation", "START", "Validating license")
        _append_startup_log(
            "license_validation",
            "SUCCESS",
            f"license_key={license_context.license_key} status={license_context.status} expiry={license_context.expiry_date} business_type_code={license_context.business_type_code}",
        )
        license_service.apply_to_database(license_context)
        _append_startup_log("database_initialization", "SUCCESS", f"applied to {license_service.db_path}")
        _append_startup_log("license_database", "SUCCESS", f"applied to {license_service.db_path}")
    except LicenseError as exc:
        _log_exception_details("license_validation", exc)
        _append_startup_log("database_initialization", "FAILED", str(exc))
        QMessageBox.critical(
            None,
            "PRM License Required",
            f"{exc}\n\nPlease reinstall using the client .prmlic file exported from PRM Client Management.",
        )
        return 2
    except Exception as exc:
        _log_exception_details("database_initialization", exc)
        _append_startup_log("license_database", "FAILED", str(exc))
        QMessageBox.critical(None, "PRM License Error", f"Unexpected license initialization failure:\n{exc}")
        return 2

    try:
        _append_startup_log("login_dialog", "START", "Creating LoginDialog")
        login = LoginDialog(config, license_context, license_service)
        _append_startup_log("login_dialog", "OK", "LoginDialog created")
    except Exception as exc:
        _append_startup_log("login_dialog", "FAIL", str(exc))
        raise

    try:
        _append_startup_log("login_exec", "START", "Showing login dialog")
        result = login.exec()
        _append_startup_log("login_exec", "OK", f"result={result}")
    except Exception as exc:
        _append_startup_log("login_exec", "FAIL", str(exc))
        raise

    if result != LoginDialog.DialogCode.Accepted:
        _append_startup_log("login", "CANCELLED", f"result={result}")
        return 0

    try:
        _append_startup_log("main_window", "START", "Creating MainWindow")
        window = MainWindow(
            config,
            start_page=start_page,
            license_context=license_context,
            license_service=license_service,
            session=login.session,
        )
        _append_startup_log("main_window", "SUCCESS", "MainWindow created")
        if icon_path.exists():
            window.setWindowIcon(QIcon(str(icon_path)))
        _append_startup_log("show_window", "START", "Showing MainWindow")
        try:
            window.showMaximized()
            _append_startup_log("show_window", "SUCCESS", f"window_visible={window.isVisible()}")
        except Exception as exc:
            _log_exception_details("show_window", exc)
            raise
        _append_startup_log("main_window", "SUCCESS", "Window shown")
    except Exception as exc:
        _log_exception_details("main_window", exc)
        raise

    _append_startup_log("event_loop", "START", "Starting Qt event loop")
    result = app.exec()
    _append_startup_log("event_loop", "END", f"exit_code={result}")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
