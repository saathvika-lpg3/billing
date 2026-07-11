from __future__ import annotations

from typing import Any

from PyQt6.QtCore import QDate, QDateTime, QTime
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QDoubleSpinBox,
    QLineEdit,
    QPlainTextEdit,
    QRadioButton,
    QSpinBox,
    QTableWidgetItem,
    QTextEdit,
    QTimeEdit,
)


def widget_value(widget: Any, *, prefer_combo_data: bool = False) -> Any:
    """Return a control's value without assuming every editor has ``text()``.

    Qt's input controls deliberately expose different APIs.  Keeping those
    branches here prevents form collectors from treating a QComboBox like a
    QLineEdit and also gives custom lookup controls a small, explicit protocol.
    """

    if widget is None:
        return None
    if isinstance(widget, QComboBox):
        if prefer_combo_data:
            data = widget.currentData()
            if data is not None:
                return data
        return widget.currentText().strip()
    if isinstance(widget, QLineEdit):
        return widget.text().strip()
    if isinstance(widget, (QTextEdit, QPlainTextEdit)):
        return widget.toPlainText().strip()
    if isinstance(widget, QDateEdit):
        return widget.date()
    if isinstance(widget, QTimeEdit):
        return widget.time()
    if isinstance(widget, QDateTimeEdit):
        return widget.dateTime()
    if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
        return widget.value()
    if isinstance(widget, (QCheckBox, QRadioButton)):
        return widget.isChecked()
    if isinstance(widget, QTableWidgetItem):
        return widget.text().strip()

    # Custom lookup editors can opt into one of these conventional APIs.
    for accessor in ("selectedValue", "selected_value", "value", "currentData", "currentText"):
        method = getattr(widget, accessor, None)
        if callable(method):
            value = method()
            if value is not None:
                return value.strip() if isinstance(value, str) else value

    raise TypeError(f"Unsupported editor type: {type(widget).__name__}")


def widget_text(widget: Any, *, prefer_combo_data: bool = False) -> str:
    """Return a normalized string representation of an editor value."""

    value = widget_value(widget, prefer_combo_data=prefer_combo_data)
    if value is None:
        return ""
    if isinstance(value, QDateTime):
        return value.toString("yyyy-MM-dd HH:mm:ss")
    if isinstance(value, QDate):
        return value.toString("yyyy-MM-dd")
    if isinstance(value, QTime):
        return value.toString("HH:mm:ss")
    return str(value).strip()


def set_widget_value(widget: Any, value: Any, *, match_combo_data: bool = False) -> None:
    """Set a supported editor while preserving a combo box's item model."""

    if isinstance(widget, QComboBox):
        if match_combo_data:
            index = widget.findData(value)
            if index >= 0:
                widget.setCurrentIndex(index)
                return
        text = "" if value is None else str(value)
        index = widget.findText(text)
        if index >= 0:
            widget.setCurrentIndex(index)
        elif widget.isEditable():
            widget.setEditText(text)
        else:
            widget.setCurrentIndex(-1)
        return
    if isinstance(widget, QLineEdit):
        widget.setText("" if value is None else str(value))
        return
    if isinstance(widget, (QTextEdit, QPlainTextEdit)):
        widget.setPlainText("" if value is None else str(value))
        return
    if isinstance(widget, QDateEdit):
        if isinstance(value, QDate):
            widget.setDate(value)
            return
    elif isinstance(widget, QTimeEdit):
        if isinstance(value, QTime):
            widget.setTime(value)
            return
    elif isinstance(widget, QDateTimeEdit):
        if isinstance(value, QDateTime):
            widget.setDateTime(value)
            return
    elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
        widget.setValue(value)
        return
    elif isinstance(widget, (QCheckBox, QRadioButton)):
        widget.setChecked(bool(value))
        return

    setter = getattr(widget, "setValue", None)
    if callable(setter):
        setter(value)
        return
    raise TypeError(f"Unsupported editor type: {type(widget).__name__}")
