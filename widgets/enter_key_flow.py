from __future__ import annotations

from PyQt6.QtCore import QEvent, QObject, Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QAbstractSpinBox,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QHeaderView,
    QLineEdit,
    QPlainTextEdit,
    QTableWidget,
    QTextEdit,
    QWidget,
)


class EnterKeyFlowFilter(QObject):
    """Desktop ERP operator flow: Enter advances fields, Shift+Enter keeps multiline text."""

    flow_widgets = (QLineEdit, QComboBox, QDateEdit, QAbstractSpinBox, QCheckBox, QTextEdit, QPlainTextEdit)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if isinstance(watched, QTableWidget) and event.type() in (QEvent.Type.Polish, QEvent.Type.Show):
            self._polish_table(watched)
        if event.type() != QEvent.Type.KeyPress:
            return super().eventFilter(watched, event)
        if isinstance(watched, QTableWidget):
            return self._handle_table_key(watched, event)
        if self._is_table_child(watched):
            return super().eventFilter(watched, event)
        if not isinstance(watched, self.flow_widgets):
            return super().eventFilter(watched, event)
        if watched.property("enterSubmits") or watched.property("allowReturn"):
            return super().eventFilter(watched, event)
        if event.key() not in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            return super().eventFilter(watched, event)
        modifiers = event.modifiers()
        if modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier):
            return super().eventFilter(watched, event)
        if isinstance(watched, (QTextEdit, QPlainTextEdit)) and modifiers & Qt.KeyboardModifier.ShiftModifier:
            return super().eventFilter(watched, event)
        if isinstance(watched, QComboBox):
            watched.hidePopup()
        if self._advance_focus(watched):
            event.accept()
            return True
        return super().eventFilter(watched, event)

    def _is_table_child(self, watched: QObject) -> bool:
        parent = watched.parent()
        while parent is not None:
            if isinstance(parent, QAbstractItemView):
                return True
            parent = parent.parent()
        return False

    def _advance_focus(self, watched: QObject) -> bool:
        if not isinstance(watched, QWidget):
            return False
        window = watched.window()
        if not isinstance(window, QWidget):
            return False
        window.focusNextPrevChild(True)
        return True

    def _handle_table_key(self, table: QTableWidget, event: QEvent) -> bool:
        if event.key() not in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            return super().eventFilter(table, event)
        if event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier):
            return super().eventFilter(table, event)
        row = max(table.currentRow(), 0)
        column = max(table.currentColumn(), 0)
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            if column > 0:
                table.setCurrentCell(row, column - 1)
            elif row > 0:
                table.setCurrentCell(row - 1, max(table.columnCount() - 1, 0))
            else:
                self._advance_focus(table)
        elif column + 1 < table.columnCount():
            table.setCurrentCell(row, column + 1)
        elif row + 1 < table.rowCount():
            table.setCurrentCell(row + 1, 0)
        else:
            self._advance_focus(table)
        event.accept()
        return True

    def _polish_table(self, table: QTableWidget) -> None:
        if table.property("operatorTablePolished"):
            return
        table.setProperty("operatorTablePolished", True)
        table.setAlternatingRowColors(True)
        table.setWordWrap(False)
        table.setTextElideMode(Qt.TextElideMode.ElideRight)
        table.setSizeAdjustPolicy(QAbstractItemView.SizeAdjustPolicy.AdjustIgnored)
        table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        table.setMinimumHeight(max(table.minimumHeight(), 96))
        table.verticalHeader().setMinimumSectionSize(22)
        table.verticalHeader().setDefaultSectionSize(min(table.verticalHeader().defaultSectionSize(), 26))
        header = table.horizontalHeader()
        header.setMinimumSectionSize(min(header.minimumSectionSize(), 72))
        header.setDefaultSectionSize(min(header.defaultSectionSize(), 96))
        header.setSectionsClickable(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
