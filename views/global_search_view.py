from __future__ import annotations

from decimal import Decimal
from typing import Any, Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config.app_config import AppConfig
from services.mysql_source import MySqlSource
from widgets.action_toolbar import ActionSpec, CompactActionToolbar
from widgets.erp_components import ERPFieldBox, ERPPageHeader, ERPGrid


class GlobalSearchView(QWidget):
    def __init__(
        self,
        config: AppConfig,
        open_page: Callable[[str], None],
        route_allowed: Callable[[str], bool] | None = None,
    ) -> None:
        super().__init__()
        self.config = config
        self.open_page = open_page
        self.route_allowed = route_allowed or (lambda _route: True)
        self.source = MySqlSource()
        self.page_size = 25
        self.offset = 0
        self.total = 0
        self.rows: list[dict[str, Any]] = []
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)
        root.addWidget(self._title_bar())
        root.addWidget(self._search_bar())
        root.addWidget(self._table_card(), stretch=1)

    def _title_bar(self) -> QWidget:
        header = ERPPageHeader("ERP Search", "Search bills, parties, items, vouchers, and menu pages with paginated results")
        header.setMaximumHeight(58)
        return header

    def _search_bar(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("card")
        frame.setMaximumHeight(96)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 5, 8, 5)
        layout.setSpacing(4)
        search_row = QHBoxLayout()
        search_row.setSpacing(6)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search bill number, party, item, phone, GSTIN, HSN...")
        self.search.setProperty("enterSubmits", True)
        self.search.returnPressed.connect(self.run_search)
        self.page_label = QLabel("Ready")
        self.page_label.setObjectName("caption")
        self.action_toolbar = CompactActionToolbar(
            [
                ActionSpec("Search", self.run_search, "Run the global search.", shortcut="Ctrl+Return", role="primary"),
                ActionSpec("First", lambda: self._go_to(0), "Go to the first result page."),
                ActionSpec("Previous", lambda: self._go_to(max(0, self.offset - self.page_size)), "Go to the previous result page."),
                ActionSpec("Next", lambda: self._go_to(self.offset + self.page_size), "Go to the next result page."),
                ActionSpec("Last", self._last_page, "Go to the last result page."),
            ]
        )
        self.first_button = self.action_toolbar.button("First")
        self.prev_button = self.action_toolbar.button("Previous")
        self.next_button = self.action_toolbar.button("Next")
        self.last_button = self.action_toolbar.button("Last")
        search_row.addWidget(self.search, stretch=1)
        search_row.addWidget(self.page_label)
        layout.addLayout(search_row)
        layout.addWidget(self.action_toolbar)
        self._update_page_label()
        return frame

    def _table_card(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        self.table = ERPGrid()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(26)
        self.table.itemActivated.connect(self._open_current_row)
        layout.addWidget(self.table, stretch=1)
        return frame

    def open_search(self, query: str) -> None:
        self.search.setText(query)
        self.offset = 0
        self.run_search()

    def run_search(self) -> None:
        self.offset = min(self.offset, self.total if self.total else 0)
        # The source has a bounded maximum (fewer than 1,000 route/record
        # candidates). Filter the complete bounded result set before paging so
        # permission-hidden routes never distort totals or page boundaries.
        result = self.source.global_search(self.search.text(), 1000, 0)
        allowed_rows = [
            row
            for row in list(result.get("rows") or [])
            if not str(row.get("target_page") or "")
            or self.route_allowed(str(row.get("target_page") or ""))
        ]
        self.total = len(allowed_rows)
        self.offset = min(self.offset, max(0, self.total - 1)) if self.total else 0
        self.rows = allowed_rows[self.offset : self.offset + self.page_size]
        self._redraw_table()

    def _go_to(self, offset: int) -> None:
        self.offset = max(0, min(max(0, self.total - 1), offset))
        if self.total:
            self.offset = (self.offset // self.page_size) * self.page_size
        self.run_search()

    def _last_page(self) -> None:
        if not self.total:
            self._go_to(0)
            return
        self._go_to(((self.total - 1) // self.page_size) * self.page_size)

    def _redraw_table(self) -> None:
        headers = ["type", "reference", "date", "party", "amount", "detail"]
        self.table.clear()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels([self._pretty(header) for header in headers])
        if not self.rows:
            self.table.setRowCount(1)
            message = "Enter at least 2 characters to search records, or type a menu name."
            if self.search.text().strip():
                message = "No matching pages or records found."
            self.table.setItem(0, 0, QTableWidgetItem(message))
            for col in range(1, len(headers)):
                self.table.setItem(0, col, QTableWidgetItem(""))
            self._update_page_label()
            return
        self.table.setRowCount(len(self.rows))
        for row_index, row in enumerate(self.rows):
            for col_index, header in enumerate(headers):
                value = row.get(header, "")
                item = QTableWidgetItem(self._display(value))
                if header == "amount":
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row_index, col_index, item)
        self.table.resizeRowsToContents()
        self._update_page_label()

    def _open_current_row(self, _item: QTableWidgetItem | None = None) -> None:
        row_index = self.table.currentRow()
        if row_index < 0 or row_index >= len(self.rows):
            return
        target = str(self.rows[row_index].get("target_page") or "")
        if target and self.route_allowed(target):
            self.open_page(target)

    def _update_page_label(self) -> None:
        if not self.total:
            text = "0 records"
        else:
            start = self.offset + 1
            end = min(self.total, self.offset + len(self.rows))
            page = (self.offset // self.page_size) + 1
            pages = ((self.total - 1) // self.page_size) + 1
            text = f"Showing {start}-{end} of {self.total} | Page {page} of {pages}"
        self.page_label.setText(text)
        self.first_button.setEnabled(self.offset > 0)
        self.prev_button.setEnabled(self.offset > 0)
        self.next_button.setEnabled(self.offset + self.page_size < self.total)
        self.last_button.setEnabled(self.offset + self.page_size < self.total)

    def _display(self, value: Any) -> str:
        if isinstance(value, Decimal):
            return f"{value:,.2f}"
        if isinstance(value, float):
            return f"{value:,.2f}"
        return "" if value is None else str(value)

    def _pretty(self, value: str) -> str:
        return value.replace("_", " ").strip().title()
