from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtWidgets import QApplication


_FONT_REGISTERED = False


def ensure_application_font() -> None:
    """Register the approved Windows UI font for app and offscreen rendering."""
    global _FONT_REGISTERED
    app = QApplication.instance()
    if app is None:
        return
    if not _FONT_REGISTERED and "Segoe UI" not in QFontDatabase.families():
        fonts_dir = Path("C:/Windows/Fonts")
        for file_name in ("segoeui.ttf", "segoeuib.ttf", "seguisb.ttf", "segoeuil.ttf"):
            font_path = fonts_dir / file_name
            if font_path.exists():
                QFontDatabase.addApplicationFont(str(font_path))
        _FONT_REGISTERED = True
    if "Segoe UI" in QFontDatabase.families():
        app.setFont(QFont("Segoe UI", 9))
