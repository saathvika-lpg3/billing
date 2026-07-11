from __future__ import annotations

from typing import Iterable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from widgets.flow_layout import FlowLayout


COMPACT_TEXT_MIN_HEIGHT = 40
COMPACT_TEXT_MAX_HEIGHT = 98
COMPACT_TEXT_FIELD_HEIGHT = 56


def prepare_form_control(widget: QWidget, minimum_width: int = 96, fixed_height: int = 28) -> QWidget:
    # Respect page-specific business widths and let FlowLayout wrap fields;
    # shrinking every control to 120px made party/master dropdown text unreadable.
    responsive_minimum = min(max(minimum_width, 96), 200)
    widget.setProperty("erpMinimumWidth", responsive_minimum)
    widget.setMinimumWidth(max(widget.minimumWidth(), responsive_minimum))
    if isinstance(widget, (QLineEdit, QComboBox, QDateEdit)):
        widget.setMinimumHeight(min(fixed_height, 28))
        widget.setMaximumHeight(max(30, widget.minimumHeight()))
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    elif isinstance(widget, (QTextEdit, QPlainTextEdit)):
        widget.setMinimumHeight(COMPACT_TEXT_MIN_HEIGHT)
        widget.setMaximumHeight(COMPACT_TEXT_MAX_HEIGHT)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    else:
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    if isinstance(widget, QComboBox):
        widget.setMaxVisibleItems(12)
        widget.setMinimumContentsLength(min(widget.minimumContentsLength(), 8))
        widget.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
    return widget


def field_box(label: str, widget: QWidget, minimum_width: int = 120) -> QFrame:
    prepare_form_control(widget, minimum_width=minimum_width)
    box = QFrame()
    box.setObjectName("fieldBox")
    box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    responsive_minimum = min(max(minimum_width, 96), 200)
    box.setProperty("erpMinimumWidth", responsive_minimum)
    box.setMinimumWidth(responsive_minimum)
    box.setMinimumHeight(46 if not isinstance(widget, (QTextEdit, QPlainTextEdit)) else COMPACT_TEXT_FIELD_HEIGHT)
    layout = QVBoxLayout(box)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(3)
    if isinstance(widget, QCheckBox):
        widget.setText(label)
    else:
        label_widget = QLabel(label)
        label_widget.setObjectName("fieldLabel")
        label_widget.setMinimumHeight(14)
        # Build a horizontal container for label + optional required badge
        from PyQt6.QtWidgets import QHBoxLayout, QWidget

        label_container = QWidget()
        h = QHBoxLayout(label_container)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(3)
        h.addWidget(label_widget)
        # If the widget has a required property, add a badge
        try:
            if bool(widget.property("required")):
                badge = QLabel("*")
                badge.setObjectName("requiredBadge")
                badge.setStyleSheet("color: red; font-weight: bold;")
                h.addWidget(badge)
        except Exception:
            pass
        layout.addWidget(label_container)
    layout.addWidget(widget)
    return box


def mark_widget_required(widget: QWidget) -> None:
    """Mark a widget as required and refresh its field box label to show a badge.

    Safe to call after the form is built.
    """
    try:
        widget.setProperty("required", True)
    except Exception:
        return
    # Try to refresh existing field box if present
    try:
        parent = widget.parent()
        if parent is None:
            return
        # parent is the fieldBox frame; its layout's first item is the label container
        layout = parent.layout()
        if layout is None:
            return
        label_container_item = layout.itemAt(0)
        if not label_container_item:
            return
        label_container = label_container_item.widget()
        if label_container is None:
            return
        # Look for existing badge to avoid duplicates
        from PyQt6.QtWidgets import QLabel

        for child in label_container.findChildren(QLabel):
            if child.objectName() == "requiredBadge":
                return
        # Add badge to the end of label_container's layout
        h = label_container.layout()
        if h is None:
            return
        badge = QLabel("*")
        badge.setObjectName("requiredBadge")
        badge.setStyleSheet("color: red; font-weight: bold;")
        h.addWidget(badge)
    except Exception:
        return


def build_field_section(fields: Iterable[tuple[str, QWidget, int]], spacing: int = 6, margin: int = 8) -> QWidget:
    container = QFrame()
    container.setObjectName("fieldSection")
    flow = FlowLayout(container, margin=margin, spacing=spacing)
    for label, widget, width in fields:
        flow.addWidget(field_box(label, widget, width))
    container.setLayout(flow)
    return container


def wrap_in_scroll(widget: QWidget) -> QScrollArea:
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setWidget(widget)
    return scroll
