from __future__ import annotations

from PyQt6.QtCore import QPoint, QRect, QSize, Qt
from PyQt6.QtWidgets import QLayout, QLayoutItem, QWidget


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
            if item.isEmpty():
                continue
            size = size.expandedTo(item.minimumSize())
        left, top, right, bottom = self.getContentsMargins()
        size += QSize(left + right, top + bottom)
        return size

    def rowCountForWidth(self, width: int) -> int:  # noqa: N802
        """Return the number of visible rows needed at ``width``.

        This is primarily useful to containers and UI checks that need to
        reserve the correct height before the widget has been shown.
        """
        return self._layout(QRect(0, 0, max(0, width), 0), True)[1]

    def doLayout(self, rect: QRect, testOnly: bool) -> int:
        return self._layout(rect, testOnly)[0]

    def _layout(self, rect: QRect, test_only: bool) -> tuple[int, int]:
        line_height = 0
        left, top, right, bottom = self.getContentsMargins()
        effective_rect = rect.adjusted(left, top, -right, -bottom)
        x = effective_rect.x()
        y = effective_rect.y()
        row_count = 0
        row_has_item = False
        available_right = effective_rect.x() + max(0, effective_rect.width())
        space_x = max(0, self.spacing())
        space_y = max(0, self.spacing())
        for item in self.item_list:
            if item.isEmpty():
                continue
            widget_size = item.sizeHint()
            next_x = x + widget_size.width() + space_x
            if x + widget_size.width() > available_right and row_has_item:
                x = effective_rect.x()
                y += line_height + space_y
                next_x = x + widget_size.width() + space_x
                line_height = 0
                row_count += 1
                row_has_item = False
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), widget_size))
            x = next_x
            line_height = max(line_height, widget_size.height())
            row_has_item = True
        if row_has_item:
            row_count += 1
            y += line_height
        used_height = max(0, y - rect.y()) + bottom
        return used_height, row_count
