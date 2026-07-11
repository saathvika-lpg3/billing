from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from config.app_config import AppConfig
from services.mysql_source import MySqlSource
from widgets.action_toolbar import ActionSpec, CompactActionToolbar
from widgets.erp_components import ERPFieldBox, ERPPageHeader, ERPGrid


class SchemeMasterView(QWidget):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.source = MySqlSource()
        self.products: list[dict[str, Any]] = []
        self.product_by_label: dict[str, dict[str, Any]] = {}
        self.rows: list[dict[str, Any]] = []
        self._build()
        self.refresh()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)
        root.addWidget(self._title_bar())
        root.addWidget(self._action_toolbar())
        root.addWidget(self._form_card())
        root.addWidget(self._list_card(), stretch=1)

    def _title_bar(self) -> QWidget:
        header = ERPPageHeader("Schemes / Offers", "FMCG scheme quantity, minimum quantity and special sale-rate rules")
        self.source_status = header.status_label
        return header

    def _action_toolbar(self) -> CompactActionToolbar:
        self.action_toolbar = CompactActionToolbar(
            [
                ActionSpec("Save Draft", self.save_draft, "Validate and save the scheme draft.", role="primary"),
                ActionSpec("Refresh", self.refresh, "Reload schemes and source data."),
            ]
        )
        return self.action_toolbar

    def _form_card(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("card")
        frame.setMinimumHeight(136)
        grid = QGridLayout(frame)
        grid.setContentsMargins(8, 6, 8, 6)
        grid.setHorizontalSpacing(7)
        grid.setVerticalSpacing(4)

        self.product = QComboBox()
        self.min_qty = QLineEdit("1")
        self.free_qty = QLineEdit("0")
        self.sale_rate = QLineEdit("0.00")
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate().addMonths(1))
        self.active = QCheckBox("Active")
        self.active.setChecked(True)
        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Operator notes, route condition, customer level, or scheme remarks")

        grid.addWidget(self._field("Product / Pack", self.product, 380), 0, 0, 1, 3)
        grid.addWidget(self._field("Minimum Qty", self.min_qty, 110), 0, 3)
        grid.addWidget(self._field("SCH Qty", self.free_qty, 110), 0, 4)
        grid.addWidget(self._field("Sale Rate", self.sale_rate, 110), 0, 5)
        grid.addWidget(self._field("Start Date", self.start_date, 120), 1, 0)
        grid.addWidget(self._field("End Date", self.end_date, 120), 1, 1)
        grid.addWidget(self._field("Status", self.active, 100), 1, 2)
        grid.addWidget(self._field("Notes", self.notes, 420), 1, 3, 1, 3)
        for column in range(6):
            grid.setColumnStretch(column, 1)
        return frame

    def _field(self, label: str, widget: QWidget, width: int) -> QWidget:
        box = QFrame()
        box.setObjectName("fieldBox")
        box.setMinimumHeight(46 if not isinstance(widget, QTextEdit) else 64)
        box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        label_widget = QLabel(label)
        label_widget.setObjectName("fieldLabel")
        label_widget.setWordWrap(True)
        label_widget.setMinimumHeight(13)
        layout.addWidget(label_widget)
        if isinstance(widget, QTextEdit):
            widget.setMinimumHeight(40)
            widget.setMaximumHeight(56)
        elif not isinstance(widget, QCheckBox):
            widget.setFixedHeight(28)
        widget.setMinimumWidth(min(width, 160))
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        if isinstance(widget, QComboBox):
            widget.setMaxVisibleItems(18)
            widget.setMinimumContentsLength(min(widget.minimumContentsLength(), 8))
        layout.addWidget(widget)
        return box

    def _list_card(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        bar = QHBoxLayout()
        title = QLabel("Existing Schemes")
        title.setObjectName("cardTitle")
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search schemes")
        self.search.textChanged.connect(self._redraw_table)
        bar.addWidget(title)
        bar.addStretch(1)
        bar.addWidget(self.search)
        layout.addLayout(bar)
        self.table = ERPGrid()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(26)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, stretch=1)
        return frame

    def refresh(self) -> None:
        try:
            self.products = self.source.product_choices()
            self.rows = self.source.operation_rows("schemes", 500)
            labels = [self._product_label(row) for row in self.products]
            self.product_by_label = dict(zip(labels, self.products))
            self.product.clear()
            self.product.addItems(labels)
            self.source_status.setText(f"{len(self.products)} packs | {len(self.rows)} schemes")
        except Exception as exc:
            self.source_status.setText(f"Source unavailable: {exc}")
            self.rows = []
        self._redraw_table()

    def save_draft(self) -> None:
        if not self.product.currentText().strip():
            QMessageBox.warning(self, "Schemes / Offers", "Select a product before saving.")
            self.product.setFocus()
            return
        try:
            min_qty = float(self.min_qty.text().replace(",", "") or 0)
            free_qty = float(self.free_qty.text().replace(",", "") or 0)
            sale_rate = float(self.sale_rate.text().replace(",", "") or 0)
        except ValueError:
            QMessageBox.warning(self, "Schemes / Offers", "Quantity and sale rate must be numeric.")
            return
        if min_qty <= 0:
            QMessageBox.warning(self, "Schemes / Offers", "Minimum quantity must be greater than zero.")
            self.min_qty.setFocus()
            return
        payload = {
            "source": "desktop_scheme_master",
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "scheme": {
                "product": self.product.currentText(),
                "min_qty": min_qty,
                "free_qty": free_qty,
                "sale_rate": sale_rate,
                "start_date": self.start_date.date().toString("yyyy-MM-dd"),
                "end_date": self.end_date.date().toString("yyyy-MM-dd"),
                "is_active": self.active.isChecked(),
                "notes": self.notes.toPlainText().strip(),
            },
        }
        drafts_dir = self.config.project_root / "drafts"
        drafts_dir.mkdir(parents=True, exist_ok=True)
        path = drafts_dir / f"scheme_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        QMessageBox.information(self, "Schemes / Offers", f"Draft saved:\n{path}")

    def _redraw_table(self) -> None:
        query = self.search.text().strip().lower()
        rows = [row for row in self.rows if not query or query in " ".join(str(v) for v in row.values()).lower()]
        if not rows:
            self.table.setColumnCount(1)
            self.table.setRowCount(1)
            self.table.setHorizontalHeaderLabels(["Status"])
            self.table.setItem(0, 0, QTableWidgetItem("No schemes found."))
            return
        headers = list(rows[0].keys())
        self.table.setColumnCount(len(headers))
        self.table.setRowCount(len(rows))
        self.table.setHorizontalHeaderLabels([header.replace("_", " ").title() for header in headers])
        for row_index, row in enumerate(rows):
            for column_index, header in enumerate(headers):
                item = QTableWidgetItem("" if row.get(header) is None else str(row.get(header)))
                if isinstance(row.get(header), (int, float)):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row_index, column_index, item)
        self.table.resizeRowsToContents()

    def _product_label(self, row: dict[str, Any]) -> str:
        return f"{row.get('item_name','')} | {row.get('pack_name','')} | MRP {float(row.get('mrp') or 0):.2f}"
