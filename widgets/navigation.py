from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QPushButton


class SidebarNavigationButton(QPushButton):
    """Sidebar button with explicit keyboard navigation signals."""

    moveRequested = pyqtSignal(int)
    escapeRequested = pyqtSignal()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        key = event.key()
        if key in {Qt.Key.Key_Up, Qt.Key.Key_Left}:
            self.moveRequested.emit(-1)
            event.accept()
            return
        if key in {Qt.Key.Key_Down, Qt.Key.Key_Right}:
            self.moveRequested.emit(1)
            event.accept()
            return
        if key in {Qt.Key.Key_Return, Qt.Key.Key_Enter}:
            self.click()
            event.accept()
            return
        if key == Qt.Key.Key_Escape:
            self.escapeRequested.emit()
            event.accept()
            return
        super().keyPressEvent(event)
