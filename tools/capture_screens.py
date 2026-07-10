from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from config.app_config import AppConfig
from views.main_window import MainWindow


def main() -> int:
    out_dir = PROJECT_ROOT / "screenshots"
    out_dir.mkdir(parents=True, exist_ok=True)
    app = QApplication([])
    window = MainWindow(AppConfig(PROJECT_ROOT, PROJECT_ROOT))
    window.resize(1440, 900)
    window.show()
    app.processEvents()

    pages = [
        "dashboard",
        "sales_bill",
        "sales_return_entry",
        "purchase_entry",
        "purchase_return_entry",
        "stock_out_entry",
        "dispatch_return_entry",
        "route_settlement",
        "audit",
        "migration_backlog",
        "ui_rules",
    ]
    for page in pages:
        window.open_page(page, remember=False)
        app.processEvents()
        QTimer.singleShot(50, app.quit)
        app.exec()
        shot = window.grab()
        shot.save(str(out_dir / f"{page}.png"))
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
