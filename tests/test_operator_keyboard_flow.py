from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QLineEdit, QTableWidget, QWidget

from widgets.enter_key_flow import EnterKeyFlowFilter


_APP: QApplication | None = None


def app() -> QApplication:
    global _APP
    _APP = QApplication.instance() or _APP or QApplication([])
    return _APP


def enter_event() -> QKeyEvent:
    return QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)


def test_enter_moves_to_next_form_control() -> None:
    qapp = app()
    window = QWidget()
    layout = QHBoxLayout(window)
    first = QLineEdit()
    second = QLineEdit()
    layout.addWidget(first)
    layout.addWidget(second)
    window.show()
    first.setFocus()
    qapp.processEvents()

    flow = EnterKeyFlowFilter(window)
    assert flow.eventFilter(first, enter_event())

    qapp.processEvents()
    assert second.hasFocus()
    window.close()


def test_enter_moves_across_table_cells() -> None:
    app()
    table = QTableWidget(2, 2)
    table.setCurrentCell(0, 0)
    flow = EnterKeyFlowFilter(table)

    assert flow.eventFilter(table, enter_event())

    assert table.currentRow() == 0
    assert table.currentColumn() == 1
