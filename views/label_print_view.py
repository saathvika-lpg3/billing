from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
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
    QVBoxLayout,
    QWidget,
)

from config.app_config import AppConfig
from services.mysql_source import MySqlSource
from widgets.erp_components import ERPFieldBox, ERPPageHeader, ERPToolbar, ERPGrid


class LabelPrintView(QWidget):
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
        root.setSpacing(4)
        root.addWidget(self._title_bar())
        root.addWidget(self._entry_card())
        root.addWidget(self._table_card(), stretch=1)

    def _title_bar(self) -> QWidget:
        header = ERPPageHeader("Product Labels / Barcode", "Prepare FMCG pack labels with barcode, MRP, sale rate and batch-ready fields")
        header.setMaximumHeight(58)
        header.status_label.setText(self.source_status.text() if hasattr(self, "source_status") else "Source: loading")
        self.source_status = header.status_label
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh)
        export_button = QPushButton("Export CSV")
        export_button.clicked.connect(self.export_csv)
        save_button = QPushButton("Save Batch")
        save_button.clicked.connect(self.save_batch)
        header.layout().addWidget(refresh_button)
        header.layout().addWidget(export_button)
        header.layout().addWidget(save_button)
        return header

    def _entry_card(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("card")
        frame.setMaximumHeight(96)
        grid = QGridLayout(frame)
        grid.setContentsMargins(8, 6, 8, 6)
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(4)
        self.product = QComboBox()
        self.product.currentTextChanged.connect(self._product_changed)
        self.barcode = QLineEdit()
        self.display_name = QLineEdit()
        self.mrp = QLineEdit("0.00")
        self.sale_rate = QLineEdit("0.00")
        self.copies = QLineEdit("1")
        self.template = QComboBox()
        self.template.addItems(["2 x 1 label", "3 x 1 label", "Thermal 58mm", "Thermal 80mm", "A4 barcode sheet"])
        add_button = QPushButton("Add Label")
        add_button.clicked.connect(self.add_label)
        clear_button = QPushButton("Clear Batch")
        clear_button.clicked.connect(self.clear_batch)

        grid.addWidget(self._field("Product / Pack", self.product, 360), 0, 0, 1, 3)
        grid.addWidget(self._field("Barcode", self.barcode, 160), 0, 3)
        grid.addWidget(self._field("Display Name", self.display_name, 220), 0, 4, 1, 2)
        grid.addWidget(self._field("MRP", self.mrp, 90), 1, 0)
        grid.addWidget(self._field("Sale", self.sale_rate, 90), 1, 1)
        grid.addWidget(self._field("Copies", self.copies, 80), 1, 2)
        grid.addWidget(self._field("Template", self.template, 160), 1, 3)
        grid.addWidget(add_button, 1, 4)
        grid.addWidget(clear_button, 1, 5)
        for column in range(6):
            grid.setColumnStretch(column, 1)
        return frame

    def _field(self, label: str, widget: QWidget, width: int) -> QWidget:
        field = ERPFieldBox(label, widget)
        if not isinstance(widget, QComboBox):
            widget.setFixedHeight(28)
        else:
            widget.setMaxVisibleItems(18)
        widget.setMinimumWidth(min(width, 160))
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return field

    def _table_card(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        title = QLabel("Label Batch")
        title.setObjectName("cardTitle")
        layout.addWidget(title)
        headers = ["#", "Product", "Pack", "Barcode", "MRP", "Sale", "Copies", "Template"]
        self.table = QTableWidget(0, len(headers))
        self.table.setHorizontalHeaderLabels(headers)
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
            labels = [self._product_label(row) for row in self.products]
            self.product_by_label = dict(zip(labels, self.products))
            self.product.clear()
            self.product.addItems(labels)
            self.source_status.setText(f"{len(self.products)} product packs ready")
        except Exception as exc:
            self.source_status.setText(f"Source unavailable: {exc}")

    def add_label(self) -> None:
        product = self.product_by_label.get(self.product.currentText())
        if not product:
            QMessageBox.warning(self, "Product Labels", "Select a product before adding.")
            return
        try:
            copies = int(float(self.copies.text().replace(",", "") or 0))
            mrp = float(self.mrp.text().replace(",", "") or 0)
            sale = float(self.sale_rate.text().replace(",", "") or 0)
        except ValueError:
            QMessageBox.warning(self, "Product Labels", "MRP, Sale and Copies must be numeric.")
            return
        if copies <= 0:
            QMessageBox.warning(self, "Product Labels", "Copies must be greater than zero.")
            self.copies.setFocus()
            return
        self.rows.append(
            {
                "product": product.get("item_name") or "",
                "pack": product.get("pack_name") or "",
                "barcode": self.barcode.text().strip(),
                "mrp": mrp,
                "sale": sale,
                "copies": copies,
                "template": self.template.currentText(),
            }
        )
        self._redraw_rows()
        self.copies.setText("1")
        self.product.setFocus()

    def clear_batch(self) -> None:
        self.rows.clear()
        self._redraw_rows()
        self.product.setFocus()

    def save_batch(self) -> None:
        if not self.rows:
            QMessageBox.information(self, "Product Labels", "Add at least one label before saving.")
            return
        payload = {"source": "desktop_product_labels", "saved_at": datetime.now().isoformat(timespec="seconds"), "labels": self.rows}
        drafts_dir = self.config.project_root / "drafts"
        drafts_dir.mkdir(parents=True, exist_ok=True)
        path = drafts_dir / f"label_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        QMessageBox.information(self, "Product Labels", f"Label batch saved:\n{path}")

    def export_csv(self) -> None:
        if not self.rows:
            QMessageBox.information(self, "Product Labels", "Add at least one label before export.")
            return
        default_path = self.config.project_root / "reports" / f"label_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        default_path.parent.mkdir(parents=True, exist_ok=True)
        path_text, _ = QFileDialog.getSaveFileName(self, "Export Label Batch", str(default_path), "CSV Files (*.csv)")
        if not path_text:
            return
        self._write_csv(Path(path_text))
        QMessageBox.information(self, "Product Labels", f"Label CSV exported:\n{path_text}")

    def _write_csv(self, path: Path) -> None:
        headers = ["product", "pack", "barcode", "mrp", "sale", "copies", "template"]
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers)
            writer.writeheader()
            writer.writerows(self.rows)

    def _product_changed(self, label: str) -> None:
        row = self.product_by_label.get(label)
        if not row:
            return
        self.barcode.setText(str(row.get("barcode") or ""))
        self.display_name.setText(str(row.get("pack_name") or row.get("item_name") or ""))
        self.mrp.setText(f"{float(row.get('mrp') or 0):.2f}")
        self.sale_rate.setText(f"{float(row.get('sale_rate') or 0):.2f}")

    def _redraw_rows(self) -> None:
        self.table.setRowCount(len(self.rows))
        for index, row in enumerate(self.rows):
            values = [
                str(index + 1),
                row["product"],
                row["pack"],
                row["barcode"],
                f"{row['mrp']:.2f}",
                f"{row['sale']:.2f}",
                str(row["copies"]),
                row["template"],
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column in {0, 4, 5, 6}:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(index, column, item)
        self.table.resizeRowsToContents()

    def _product_label(self, row: dict[str, Any]) -> str:
        return f"{row.get('item_name','')} | {row.get('pack_name','')} | Barcode {row.get('barcode') or '-'}"
