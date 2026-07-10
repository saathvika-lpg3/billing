from __future__ import annotations

from decimal import Decimal
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config.app_config import AppConfig
from services.mysql_source import MySqlSource


class StockDashboardView(QWidget):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.source = MySqlSource()
        self.tables: dict[str, QTableWidget] = {}
        self.summary: dict[str, Any] = {}
        self._build()
        self.refresh()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)
        root.addWidget(self._title_bar())
        root.addWidget(self._metric_grid())
        root.addWidget(self._table_area(), stretch=1)

    def _title_bar(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("pageHeader")
        frame.setMaximumHeight(52)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 4, 8, 4)
        text_box = QVBoxLayout()
        text_box.setSpacing(0)
        title = QLabel("Stock Dashboard")
        title.setObjectName("pageTitle")
        caption = QLabel("Live stock position, shortage alerts, negative stock, batches and movement")
        caption.setObjectName("pageSubtitle")
        text_box.addWidget(title)
        text_box.addWidget(caption)
        layout.addLayout(text_box, stretch=1)
        self.filter_text = QLineEdit()
        self.filter_text.setPlaceholderText("Filter all stock tables")
        self.filter_text.setMinimumWidth(160)
        self.filter_text.setMaximumWidth(260)
        self.filter_text.textChanged.connect(self._redraw_all_tables)
        layout.addWidget(self.filter_text)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh)
        layout.addWidget(refresh_button)
        return frame

    def _metric_grid(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("card")
        frame.setMaximumHeight(96)
        self.metric_layout = QGridLayout(frame)
        self.metric_layout.setContentsMargins(8, 6, 8, 6)
        self.metric_layout.setHorizontalSpacing(7)
        self.metric_layout.setVerticalSpacing(5)
        self.metric_labels: dict[str, QLabel] = {}
        metrics = [
            ("items", "Stock Items", "Active product masters"),
            ("packs", "Pack Quantity", "Current pack stock"),
            ("alerts", "Low Stock", "Below minimum level"),
            ("negative", "Negative Stock", "Needs correction"),
            ("warehouses", "Warehouses", "Store locations"),
            ("batches", "Live Batches", "Batch rows with stock"),
        ]
        for index, (key, title, subtitle) in enumerate(metrics):
            card = self._metric_card(key, title, subtitle)
            self.metric_layout.addWidget(card, 0, index)
            self.metric_layout.setColumnStretch(index, 1)
        return frame

    def _metric_card(self, key: str, title: str, subtitle: str) -> QWidget:
        card = QFrame()
        card.setObjectName("metricCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 5, 8, 5)
        layout.setSpacing(2)
        heading = QLabel(title)
        heading.setObjectName("metricTitle")
        value = QLabel("0")
        value.setObjectName("metricValue")
        note = QLabel(subtitle)
        note.setObjectName("metricNote")
        layout.addWidget(heading)
        layout.addWidget(value)
        layout.addWidget(note)
        self.metric_labels[key] = value
        return card

    def _table_area(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("card")
        grid = QGridLayout(frame)
        grid.setContentsMargins(8, 6, 8, 6)
        grid.setHorizontalSpacing(7)
        grid.setVerticalSpacing(6)
        sections = [
            ("Stock Alerts", "stock_alerts"),
            ("Negative Stock", "negative_stock"),
            ("Recent Movement", "stock_entry"),
            ("Expiry / Batch Watch", "expiry_wastage"),
        ]
        for index, (title, key) in enumerate(sections):
            grid.addWidget(self._table_card(title, key), index // 2, index % 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)
        return frame

    def _table_card(self, title: str, key: str) -> QWidget:
        card = QFrame()
        card.setObjectName("innerCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(6, 5, 6, 5)
        heading = QLabel(title)
        heading.setObjectName("cardTitle")
        layout.addWidget(heading)
        table = QTableWidget()
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.verticalHeader().setDefaultSectionSize(26)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        layout.addWidget(table, stretch=1)
        self.tables[key] = table
        return card

    def refresh(self) -> None:
        try:
            self.summary = self.source.stock_summary()
            self.rows_by_key = {
                "stock_alerts": self.source.operation_rows("stock_alerts", 80),
                "negative_stock": self.source.operation_rows("negative_stock", 80),
                "stock_entry": self.source.operation_rows("stock_entry", 80),
                "expiry_wastage": self.source.operation_rows("expiry_wastage", 80),
            }
        except Exception as exc:
            self.summary = {}
            self.rows_by_key = {key: [{"Status": f"Source unavailable: {exc}"}] for key in self.tables}
        self._redraw_metrics()
        self._redraw_all_tables()

    def _redraw_metrics(self) -> None:
        values = {
            "items": self._metric_text("items", "count"),
            "packs": self._metric_text("packs", "qty"),
            "alerts": self._metric_text("alerts", "count"),
            "negative": self._metric_text("negative", "count"),
            "warehouses": self._metric_text("warehouses", "count"),
            "batches": self._metric_text("batches", "count"),
        }
        for key, value in values.items():
            self.metric_labels[key].setText(value)

    def _metric_text(self, section: str, field: str) -> str:
        value = (self.summary.get(section) or {}).get(field, 0)
        if isinstance(value, (float, Decimal)):
            return f"{value:,.2f}"
        return f"{int(value):,}" if str(value).replace("-", "").isdigit() else str(value)

    def _redraw_all_tables(self) -> None:
        for key, table in self.tables.items():
            self._draw_table(table, self.rows_by_key.get(key, []))

    def _draw_table(self, table: QTableWidget, rows: list[dict[str, Any]]) -> None:
        query = self.filter_text.text().strip().lower()
        filtered = []
        for row in rows:
            haystack = " ".join(str(value) for value in row.values()).lower()
            if not query or query in haystack:
                filtered.append(row)
        if not filtered:
            table.setColumnCount(1)
            table.setRowCount(1)
            table.setHorizontalHeaderLabels(["Status"])
            table.setItem(0, 0, QTableWidgetItem("No matching stock rows."))
            return
        headers = list(filtered[0].keys())
        table.setColumnCount(len(headers))
        table.setRowCount(len(filtered))
        table.setHorizontalHeaderLabels([self._pretty(header) for header in headers])
        for row_index, row in enumerate(filtered):
            for column_index, header in enumerate(headers):
                value = row.get(header, "")
                item = QTableWidgetItem(str(value))
                if isinstance(value, (int, float)):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                table.setItem(row_index, column_index, item)
        table.resizeRowsToContents()
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        table.resizeColumnsToContents()

    def _pretty(self, value: str) -> str:
        return value.replace("_", " ").strip().title()
