from __future__ import annotations

from PyQt6.QtCore import QPoint, QRect, QSize, Qt
from PyQt6.QtWidgets import QLayout, QSizePolicy, QLayoutItem, QWidget


class FlowLayout(QLayout):
    def __init__(self, parent: QWidget | None = None, margin: int = 0, spacing: int = 8) -> None:
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self.item_list: list[QLayoutItem] = []

    def addItem(self, item: QLayoutItem) -> None:
        self.item_list.append(item)

    def addWidget(self, widget: QWidget) -> None:
        super().addWidget(widget)

    def count(self) -> int:
        return len(self.item_list)

    def itemAt(self, index: int) -> QLayoutItem | None:
        return self.item_list[index] if 0 <= index < len(self.item_list) else None

    def takeAt(self, index: int) -> QLayoutItem | None:
        if 0 <= index < len(self.item_list):
            return self.item_list.pop(index)
        return None

    def expandingDirections(self) -> Qt.Orientations:
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self.doLayout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect: QRect) -> None:
        super().setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self.item_list:
            size = size.expandedTo(item.minimumSize())
        left, top, right, bottom = self.getContentsMargins()
        size += QSize(left + right, top + bottom)
        return size

    def doLayout(self, rect: QRect, testOnly: bool) -> int:
        x = rect.x()
        y = rect.y()
        line_height = 0
        left, top, right, bottom = self.getContentsMargins()
        effective_rect = rect.adjusted(left, top, -right, -bottom)
        for item in self.item_list:
            widget_size = item.sizeHint()
            space_x = self.spacing()
            space_y = self.spacing()
            next_x = x + widget_size.width() + space_x
            if next_x - space_x > effective_rect.right() and line_height > 0:
                x = effective_rect.x()
                y += line_height + space_y
                next_x = x + widget_size.width() + space_x
                line_height = 0
            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), widget_size))
            x = next_x
            line_height = max(line_height, widget_size.height())
        if line_height:
            y += line_height
        return y + bottom
