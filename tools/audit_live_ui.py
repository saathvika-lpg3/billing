from __future__ import annotations

import csv
import gc
import inspect
import os
import shutil
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtGui import QAction, QShortcut
from PyQt6.QtWidgets import QApplication, QFrame, QPushButton

from config.app_config import AppConfig
from views.main_window import MainWindow
from widgets.erp_components import (
    ERPPageHeader,
    ERPToolbar,
    TransactionHeader,
    TransactionToolbar,
    TransactionTotalsPanel,
)


TARGET_SIZES = ((1366, 768), (1440, 900), (1920, 1080))
INVENTORY_FIELDS = (
    "menu_route",
    "view_class",
    "view_file",
    "shared_framework",
    "header_implementation",
    "toolbar_implementation",
    "layout_type",
    "action_buttons",
    "signal_slot_wiring",
    "keyboard_shortcuts",
    "save_handler",
    "error_handling",
    "test_coverage",
    "screen_fit",
    "known_issue",
)
SAVE_HANDLERS = (
    "save_draft",
    "save_document",
    "save_record",
    "save_product",
    "save_bill",
    "save_entry",
    "save",
)


def _source_path(page: object) -> str:
    source = inspect.getsourcefile(type(page))
    if not source:
        return ""
    try:
        return str(Path(source).resolve().relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(Path(source).resolve())


def _test_coverage(route: str, class_name: str) -> str:
    needles = {route, class_name}
    matches: list[str] = []
    for path in sorted((PROJECT_ROOT / "tests").glob("test_*.py")):
        text = path.read_text(encoding="utf-8", errors="replace")
        if any(needle and needle in text for needle in needles):
            matches.append(path.name)
    return ", ".join(matches) if matches else "none found"


def _visible_buttons(page: object) -> list[QPushButton]:
    return [
        button
        for button in page.findChildren(QPushButton)
        if button.isVisibleTo(page)
    ]


def _vertical_toolbar_stacks(page: object) -> list[str]:
    """Return action toolbars that still consume a near-vertical column."""

    issues: list[str] = []
    toolbars = [
        frame
        for frame in page.findChildren(QFrame)
        if frame.objectName() == "actionToolbar" or frame.property("role") == "toolbar"
    ]
    for toolbar in toolbars:
        buttons = [button for button in toolbar.findChildren(QPushButton) if button.isVisibleTo(page)]
        if len(buttons) < 4:
            continue
        centers = [button.mapTo(toolbar, button.rect().center()) for button in buttons]
        row_centers: list[int] = []
        tolerance = max(8, max(button.height() for button in buttons) // 2)
        for center in sorted(point.y() for point in centers):
            if not row_centers or abs(center - row_centers[-1]) > tolerance:
                row_centers.append(center)
        # Two compact wrapped rows are acceptable. Three or more rows holding
        # most actions indicates the narrow right-hand stack this audit guards.
        if len(row_centers) >= 3 and len(row_centers) >= (len(buttons) + 1) // 2:
            labels = ", ".join(button.text().strip() for button in buttons if button.text().strip())
            issues.append(labels or type(toolbar).__name__)
    return issues


def _grand_total_visible(window: MainWindow, page: object) -> bool:
    if window.content_scroll is None:
        return True
    viewport = window.content_scroll.viewport()
    for panel in page.findChildren(TransactionTotalsPanel):
        grand = panel.labels.get("grand_total")
        if grand is None or not grand.isVisibleTo(page):
            continue
        top = grand.mapTo(viewport, grand.rect().topLeft()).y()
        bottom = grand.mapTo(viewport, grand.rect().bottomLeft()).y()
        if not (0 <= top < bottom <= viewport.height()):
            return False
    return True


def _shortcuts(page: object) -> list[str]:
    keys = {
        shortcut.key().toString()
        for shortcut in page.findChildren(QShortcut)
        if not shortcut.key().isEmpty()
    }
    keys.update(
        action.shortcut().toString()
        for action in page.findChildren(QAction)
        if not action.shortcut().isEmpty()
    )
    return sorted(key for key in keys if key)


def _frameworks(page: object) -> tuple[str, str, str]:
    headers = page.findChildren(ERPPageHeader)
    toolbars = [
        frame
        for frame in page.findChildren(QFrame)
        if frame.objectName() == "actionToolbar" or frame.property("role") == "toolbar"
    ]
    frameworks: list[str] = []
    if page.property("transactionFramework") is True or page.findChild(TransactionHeader):
        frameworks.append("Shared Transaction Entry Framework")
    if page.findChild(ERPPageHeader) or page.findChild(ERPToolbar):
        frameworks.append("Shared ERP UI Framework")
    if not frameworks:
        frameworks.append("Qt page framework")
    header_names = sorted({type(header).__name__ for header in headers})
    toolbar_names = sorted({type(toolbar).__name__ for toolbar in toolbars})
    return (
        " + ".join(frameworks),
        ", ".join(header_names) if header_names else "none",
        ", ".join(toolbar_names) if toolbar_names else "none",
    )


def _error_handling(page: object) -> str:
    try:
        source = inspect.getsource(type(page))
    except (OSError, TypeError):
        return "not inspectable"
    has_message = "QMessageBox" in source
    has_guard = "except " in source
    if has_message and has_guard:
        return "guarded + user message"
    if has_message:
        return "user message"
    if has_guard:
        return "guarded"
    return "no local handler (shared/service)"


def audit() -> list[dict[str, str]]:
    app = QApplication.instance() or QApplication([])
    source_db = PROJECT_ROOT / "database" / "prm_billing_inventory.db"
    with tempfile.TemporaryDirectory(prefix="prm-live-ui-audit-", ignore_cleanup_errors=True) as temp_dir:
        audit_db = Path(temp_dir) / "audit.db"
        if source_db.exists():
            shutil.copy2(source_db, audit_db)
        os.environ["PRM_SQLITE_DB"] = str(audit_db)
        os.environ["PRM_USE_SQLITE"] = "0"

        window = MainWindow(AppConfig(PROJECT_ROOT, PROJECT_ROOT))
        window.show()
        app.processEvents()
        routes = sorted(window.page_factories)
        size_results: dict[str, list[str]] = {route: [] for route in routes}
        rows_by_route: dict[str, dict[str, str]] = {}

        for width, height in TARGET_SIZES:
            window.resize(width, height)
            app.processEvents()
            for route in routes:
                window.open_page(route, remember=False)
                app.processEvents()
                app.processEvents()
                page = window.pages[route]
                overflow = window.content_scroll.horizontalScrollBar().maximum() if window.content_scroll else 0
                grand_total_visible = _grand_total_visible(window, page)
                fits = overflow == 0 and page.width() <= window.stack.width() + 2 and grand_total_visible
                size_results[route].append(f"{width}x{height}:{'PASS' if fits else 'FAIL'}")
                if route in rows_by_route:
                    continue

                buttons = _visible_buttons(page)
                dead = [
                    button.text().strip() or button.objectName() or type(button).__name__
                    for button in buttons
                    if button.isEnabled() and button.receivers(button.clicked) == 0
                ]
                no_feedback = [
                    button.text().strip() or button.objectName() or type(button).__name__
                    for button in buttons
                    if button.property("_erpFeedbackInstalled") is not True
                ]
                framework, header, toolbar = _frameworks(page)
                source_path = _source_path(page)
                handlers = [name for name in SAVE_HANDLERS if callable(getattr(page, name, None))]
                issues: list[str] = []
                if page.property("factoryFallback") is True:
                    issues.append("factory fallback page")
                if dead:
                    issues.append("unwired: " + ", ".join(dead))
                if no_feedback:
                    issues.append("feedback missing: " + ", ".join(no_feedback))
                vertical_stacks = _vertical_toolbar_stacks(page)
                if vertical_stacks:
                    issues.append("vertical toolbar stack: " + " / ".join(vertical_stacks))
                if not grand_total_visible:
                    issues.append("Grand Total clipped outside viewport")
                rows_by_route[route] = {
                    "menu_route": route,
                    "view_class": type(page).__name__,
                    "view_file": source_path,
                    "shared_framework": framework,
                    "header_implementation": header,
                    "toolbar_implementation": toolbar,
                    "layout_type": type(page.layout()).__name__ if page.layout() else "none",
                    "action_buttons": " | ".join(button.text().strip() for button in buttons if button.text().strip()),
                    "signal_slot_wiring": f"{len(buttons) - len(dead)}/{len(buttons)} visible buttons wired",
                    "keyboard_shortcuts": " | ".join(_shortcuts(page)) or "none declared locally",
                    "save_handler": " | ".join(handlers) or "not an entry page / service action",
                    "error_handling": _error_handling(page),
                    "test_coverage": _test_coverage(route, type(page).__name__),
                    "screen_fit": "",
                    "known_issue": "; ".join(issues) if issues else "none found",
                }

        for page in window.pages.values():
            source = getattr(page, "source", None)
            close_resources = getattr(source, "close_database_resources", None)
            if callable(close_resources):
                close_resources()
            page.deleteLater()
        window.close()
        app.processEvents()
        gc.collect()
        for route, row in rows_by_route.items():
            row["screen_fit"] = " | ".join(size_results[route])
            if "FAIL" in row["screen_fit"]:
                row["known_issue"] = (
                    row["known_issue"] + "; screen overflow"
                    if row["known_issue"] != "none found"
                    else "screen overflow"
                )
        return [rows_by_route[route] for route in routes]


def write_outputs(rows: list[dict[str, str]]) -> tuple[Path, Path]:
    audit_dir = PROJECT_ROOT / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    csv_path = audit_dir / "live_page_ui_inventory.csv"
    md_path = audit_dir / "live_page_ui_inventory.md"
    headers = list(INVENTORY_FIELDS)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    passed = sum(1 for row in rows if row["known_issue"] == "none found")
    lines = [
        "# Live Page UI Inventory",
        "",
        "Generated from the page factories used by `MainWindow`; fallback pages, visible button wiring, shared UI markers, and three target desktop sizes are checked at runtime.",
        "",
        f"- Live routes: {len(rows)}",
        f"- Routes with no detected issue: {passed}",
        f"- Routes requiring review: {len(rows) - passed}",
        "",
        "| Route | View | Framework | Toolbar | Wiring | Screen fit | Known issue |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        values = [
            row["menu_route"],
            row["view_class"],
            row["shared_framework"],
            row["toolbar_implementation"],
            row["signal_slot_wiring"],
            row["screen_fit"],
            row["known_issue"],
        ]
        lines.append("| " + " | ".join(value.replace("|", "/") for value in values) + " |")
    lines.extend(["", "The CSV companion contains the complete action, shortcut, save-handler, error-handling, source-file, and test-coverage fields.", ""])
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return csv_path, md_path


def main() -> int:
    paths = write_outputs(audit())
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
