from __future__ import annotations

from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config.app_config import AppConfig
from services.financial_year_service import FinancialYearService
from services.numbering_series_service import NumberingSeriesService
from widgets.action_toolbar import ActionSpec, CompactActionToolbar
from widgets.form_layout_helpers import build_field_section
from widgets.erp_components import ERPFieldBox, ERPPageHeader, ERPGrid


class NumberingSeriesAdminView(QWidget):
    def __init__(self, config: AppConfig, db_path: Path | None = None) -> None:
        super().__init__()
        self.config = config
        self.series_service = NumberingSeriesService(db_path)
        self.year_service = FinancialYearService(db_path)
        self.current_id = 0
        self._build()
        self.refresh()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)
        root.addWidget(self._title_bar())
        root.addWidget(self._form_card())
        root.addWidget(self._table_card(), stretch=1)

    def _title_bar(self) -> QWidget:
        header = ERPPageHeader("Numbering Series", "Configure document numbering patterns and preview the next numbers.")
        self.status_label = header.status_label
        return header

    def _form_card(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        self.document_type = QLineEdit()
        self.prefix = QLineEdit()
        self.suffix = QLineEdit()
        self.separator = QLineEdit("-")
        self.financial_year_label = QComboBox()
        self.financial_year_label.setEditable(True)
        self.branch_code = QLineEdit()
        self.warehouse_code = QLineEdit()
        self.business_type_code = QLineEdit()
        self.padding_length = QSpinBox()
        self.padding_length.setRange(1, 16)
        self.padding_length.setValue(6)
        self.start_number = QSpinBox()
        self.start_number.setRange(1, 999999)
        self.start_number.setValue(1)
        self.reset_rule = QComboBox()
        self.reset_rule.addItems([NumberingSeriesService.RESET_NEVER, NumberingSeriesService.RESET_YEARLY, NumberingSeriesService.RESET_MONTHLY])
        self.is_active = QCheckBox("Active")
        self.is_active.setChecked(True)
        self.preview_output = QLineEdit()
        self.preview_output.setReadOnly(True)

        fields: list[tuple[str, QWidget, int]] = [
            ("Document Type", self.document_type, 180),
            ("Prefix", self.prefix, 100),
            ("Suffix", self.suffix, 100),
            ("Separator", self.separator, 80),
            ("Financial Year", self.financial_year_label, 180),
            ("Branch Code", self.branch_code, 120),
            ("Warehouse Code", self.warehouse_code, 120),
            ("Business Type", self.business_type_code, 140),
            ("Padding", self.padding_length, 80),
            ("Start Number", self.start_number, 90),
            ("Reset Rule", self.reset_rule, 120),
            ("Status", self.is_active, 90),
            ("Preview Next", self.preview_output, 260),
        ]

        layout.addWidget(build_field_section(fields, spacing=6, margin=0))

        self.action_toolbar = CompactActionToolbar(
            [
                ActionSpec("New", self.clear_form, "Start a new numbering series.", role="positive"),
                ActionSpec("Save Series", self.save_series, "Save the numbering series.", role="primary"),
                ActionSpec("Preview", self.preview_next_number, "Preview the next document number."),
                ActionSpec("Refresh", self.refresh, "Reload numbering series."),
            ]
        )
        layout.addWidget(self.action_toolbar)
        return frame

    def _field(self, label: str, widget: QWidget) -> QWidget:
        box = QFrame()
        box.setObjectName("fieldBox")
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        label_widget = QLabel(label)
        label_widget.setObjectName("fieldLabel")
        layout.addWidget(label_widget)
        layout.addWidget(widget)
        return box

    def _table_card(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        self.table = ERPGrid()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(self.table.SelectionMode.SingleSelection)
        self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(self.table.horizontalHeader().ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(26)
        self.table.itemSelectionChanged.connect(self._row_selected)
        layout.addWidget(self.table, stretch=1)
        return frame

    def clear_form(self) -> None:
        self.current_id = 0
        self.document_type.clear()
        self.prefix.clear()
        self.suffix.clear()
        self.separator.setText("-")
        self.financial_year_label.setCurrentText("")
        self.branch_code.clear()
        self.warehouse_code.clear()
        self.business_type_code.clear()
        self.padding_length.setValue(6)
        self.start_number.setValue(1)
        self.reset_rule.setCurrentText(NumberingSeriesService.RESET_NEVER)
        self.is_active.setChecked(True)
        self.preview_output.clear()
        self.status_label.setText("Ready")

    def refresh(self) -> None:
        self._load_financial_year_labels()
        series = self.series_service.list_series()
        self._populate_table(series)
        self.status_label.setText(f"{len(series)} numbering series loaded")
        if series:
            self._select_table_row(0)
        else:
            self.clear_form()

    def _load_financial_year_labels(self) -> None:
        self.financial_year_label.clear()
        labels = [row["label"] for row in self.year_service.list_years()]
        self.financial_year_label.addItems(labels)

    def _populate_table(self, rows: list[dict[str, Any]]) -> None:
        headers = [
            "id",
            "document_type",
            "prefix",
            "suffix",
            "separator",
            "financial_year_label",
            "branch_code",
            "warehouse_code",
            "business_type_code",
            "padding_length",
            "start_number",
            "current_number",
            "reset_rule",
            "is_active",
        ]
        self.table.setColumnCount(len(headers))
        self.table.setRowCount(len(rows))
        self.table.setHorizontalHeaderLabels([self._pretty(column) for column in headers])
        for row_index, row in enumerate(rows):
            for col_index, header in enumerate(headers):
                value = row.get(header, "")
                item = QTableWidgetItem(str(value or ""))
                if header in {"id", "padding_length", "start_number", "current_number", "is_active"}:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row_index, col_index, item)
        self.table.resizeRowsToContents()

    def _select_table_row(self, row_index: int) -> None:
        if 0 <= row_index < self.table.rowCount():
            self.table.selectRow(row_index)

    def _row_selected(self) -> None:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            self.clear_form()
            return
        row = selected[0].row()
        item = self.table.item(row, 0)
        if item is None:
            self.clear_form()
            return
        self._load_series(int(item.text()))

    def _load_series(self, series_id: int) -> None:
        series = self.series_service.get_series(series_id)
        if not series:
            self.clear_form()
            return
        self.current_id = int(series.get("id") or 0)
        self.document_type.setText(str(series.get("document_type") or ""))
        self.prefix.setText(str(series.get("prefix") or ""))
        self.suffix.setText(str(series.get("suffix") or ""))
        self.separator.setText(str(series.get("separator") or "-"))
        self.financial_year_label.setCurrentText(str(series.get("financial_year_label") or ""))
        self.branch_code.setText(str(series.get("branch_code") or ""))
        self.warehouse_code.setText(str(series.get("warehouse_code") or ""))
        self.business_type_code.setText(str(series.get("business_type_code") or ""))
        self.padding_length.setValue(int(series.get("padding_length") or 6))
        self.start_number.setValue(int(series.get("start_number") or 1))
        self.reset_rule.setCurrentText(str(series.get("reset_rule") or NumberingSeriesService.RESET_NEVER))
        self.is_active.setChecked(bool(int(series.get("is_active") or 0)))
        self.preview_output.clear()
        active_label = "Active" if self.is_active.isChecked() else "Inactive"
        self.status_label.setText(f"Selected: {series['document_type']} ({active_label})")

    def save_series(self) -> None:
        document_type = self.document_type.text().strip()
        if not document_type:
            QMessageBox.warning(self, "Numbering Series", "Document type is required.")
            return
        data = {
            "prefix": self.prefix.text().strip(),
            "suffix": self.suffix.text().strip(),
            "separator": self.separator.text().strip() or "-",
            "financial_year_label": self.financial_year_label.currentText().strip(),
            "branch_code": self.branch_code.text().strip(),
            "warehouse_code": self.warehouse_code.text().strip(),
            "business_type_code": self.business_type_code.text().strip(),
            "padding_length": self.padding_length.value(),
            "start_number": self.start_number.value(),
            "reset_rule": self.reset_rule.currentText(),
            "is_active": 1 if self.is_active.isChecked() else 0,
        }
        try:
            if self.current_id:
                self.series_service.update_series(self.current_id, data)
                self.status_label.setText(f"Series updated: {document_type}")
            else:
                self.series_service.create_series(document_type=document_type, **data)
                self.status_label.setText(f"Series created: {document_type}")
        except Exception as exc:
            QMessageBox.warning(self, "Numbering Series", str(exc))
            return
        self.refresh()

    def preview_next_number(self) -> None:
        if not self.current_id:
            QMessageBox.information(self, "Numbering Series", "Select a numbering series first to preview.")
            return
        series = self.series_service.get_series(self.current_id)
        if not series:
            QMessageBox.warning(self, "Numbering Series", "Unable to load the selected numbering series.")
            return
        scope = {
            "financial_year_label": str(series.get("financial_year_label") or ""),
            "branch_code": str(series.get("branch_code") or ""),
            "warehouse_code": str(series.get("warehouse_code") or ""),
            "business_type_code": str(series.get("business_type_code") or ""),
        }
        try:
            preview = self.series_service.generate_next(series["document_type"], scope, preview=True)
            self.preview_output.setText(preview)
            self.status_label.setText("Preview generated")
        except Exception as exc:
            QMessageBox.warning(self, "Numbering Series", str(exc))

    @staticmethod
    def _pretty(value: str) -> str:
        return value.replace("_", " ").strip().title()
